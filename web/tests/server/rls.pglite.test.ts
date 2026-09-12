import { readFile } from "node:fs/promises";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { PGlite } from "@electric-sql/pglite";

const owner = "11111111-1111-4111-8111-111111111111";
const attacker = "22222222-2222-4222-8222-222222222222";
const plan = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const session = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa01";
let db: PGlite;

async function asUser(id: string) { await db.exec(`set role authenticated; set request.jwt.claim.sub = '${id}'`); }
async function asTrusted() { await db.exec("reset role; set role service_role"); }

function canonicalPlan(sessionId: string, date = "2025-01-01") {
  return JSON.stringify({ version: "1", trail_id: "trail", fitness: "1", start_date: "2025-01-01", trip_date: "2025-01-08", sessions: [{ id: sessionId, week: "1", day: "1", date }] });
}

describe("account-plan RLS (embedded PostgreSQL)", () => {
  beforeEach(async () => {
    db = new PGlite();
    await db.exec("create schema auth; create table auth.users(id uuid primary key); create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$; create role anon; create role authenticated; create role service_role bypassrls; grant authenticated, service_role to current_user; grant usage on schema auth to authenticated; grant execute on function auth.uid() to authenticated;");
    const migration = (await readFile(new URL("../../../supabase/migrations/20250912000100_account_plan_baseline.sql", import.meta.url), "utf8")).replace("create extension if not exists pgcrypto;", "");
    await db.exec(migration);
    await db.exec(`insert into auth.users values('${owner}'),('${attacker}')`);
    await asTrusted();
    await db.exec(`insert into public.prep_plans(id,owner_id,trail_id,fitness,start_date,trip_date,plan) values('${plan}','${owner}','trail',1,'2025-01-01','2025-01-08','{"version":"1"}'); insert into public.plan_sessions values('${plan}','${session}',1,1,'2025-01-01','{"id":"${session}","week":1,"day":1,"date":"2025-01-01"}')`);
  });
  afterEach(async () => db.close());

  it("denies authenticated canonical inserts, updates, and RPC execution", async () => {
    await asUser(owner);
    await expect(db.exec(`insert into public.prep_plans(owner_id,trail_id,fitness,start_date,trip_date,plan) values('${owner}','forged',1,'2025-01-01','2025-01-08','{"version":"1"}')`)).rejects.toThrow();
    await expect(db.exec(`update public.prep_plans set trail_id='other' where id='${plan}'`)).rejects.toThrow();
    await expect(db.exec(`insert into public.plan_sessions(plan_id,session_id,week,day,session_date,session) values('${plan}','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',1,2,'2025-01-02','{"id":"bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb","week":1,"day":2,"date":"2025-01-02"}')`)).rejects.toThrow();
    await expect(db.exec(`update public.plan_sessions set session_date='2025-01-02' where plan_id='${plan}'`)).rejects.toMatchObject({ code: "42501" });
    await expect(db.query(`select public.save_prep_plan('${canonicalPlan("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")}'::jsonb, '${owner}')`)).rejects.toMatchObject({ code: "42501" });
  });

  it("hides other owners while allowing owner plan deletion and session logging", async () => {
    await asUser(attacker);
    expect((await db.query("select * from public.prep_plans")).rows).toHaveLength(0);
    await expect(db.exec(`insert into public.session_logs(plan_id,session_id) values('${plan}','${session}')`)).rejects.toThrow();
    await asUser(owner);
    await db.exec(`insert into public.session_logs(plan_id,session_id,done_at) values('${plan}','${session}','2025-01-01')`);
    expect((await db.query("select * from public.session_logs")).rows).toHaveLength(1);
    await db.exec(`delete from public.prep_plans where id='${plan}'`);
    expect((await db.query("select * from public.plan_sessions")).rows).toHaveLength(0);
    expect((await db.query("select * from public.session_logs")).rows).toHaveLength(0);
  });

  it("allows only the trusted RPC to atomically write the explicit owner plan", async () => {
    await asTrusted();
    const valid = canonicalPlan("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb");
    await db.query(`select public.save_prep_plan('${valid}'::jsonb, '${attacker}')`);
    expect((await db.query(`select count(*) from public.prep_plans where owner_id='${attacker}'`)).rows[0].count).toBe(1);
    await expect(db.query(`select public.save_prep_plan('{"version":"1","trail_id":"trail","fitness":"1","start_date":"2025-01-01","trip_date":"2025-01-08","sessions":[{"id":"cccccccc-cccc-4ccc-8ccc-cccccccccccc","week":"1","day":"1","date":"2025-01-09"}]}'::jsonb, '${attacker}')`)).rejects.toThrow();
    expect((await db.query(`select count(*) from public.prep_plans where owner_id='${attacker}'`)).rows[0].count).toBe(1);
    await asUser(owner);
    expect((await db.query("select * from public.prep_plans")).rows).toHaveLength(1);
  });

  it("blocks anon access, foreign child reads/deletes and company takeover", async () => {
    await asUser(owner);
    await db.exec("insert into public.companies(name) values('Owner company')");
    await db.exec(`insert into public.session_logs(plan_id,session_id,done_at) values('${plan}','${session}','2025-01-01')`);
    await asUser(attacker);
    for (const table of ["prep_plans", "plan_sessions", "session_logs", "companies"]) {
      expect((await db.query(`select * from public.${table}`)).rows).toHaveLength(0);
    }
    expect((await db.exec(`delete from public.prep_plans where id='${plan}'`))[0].affectedRows).toBe(0);
    expect((await db.exec("update public.companies set name='Taken over'"))[0].affectedRows).toBe(0);
    await expect(db.exec(`insert into public.companies(owner_id,name) values('${owner}','Forged')`)).rejects.toMatchObject({ code: "42501" });
    await db.exec("reset role; set role anon");
    await expect(db.query("select * from public.prep_plans")).rejects.toMatchObject({ code: "42501" });
  });

  it("rejects rescheduling a completed session after its done_at", async () => {
    await asUser(owner);
    await db.exec(`insert into public.session_logs(owner_id,plan_id,session_id,done_at) values('${owner}','${plan}','${session}','2025-01-01')`);
    await asTrusted();
    await expect(db.exec(`update public.plan_sessions set session_date='2025-01-02', session=jsonb_set(session, '{date}', '"2025-01-02"') where plan_id='${plan}' and session_id='${session}'`)).rejects.toThrow();
  });
});
