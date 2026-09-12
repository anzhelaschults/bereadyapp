"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, post } from "../../lib/client";
import type { Plan, SavedPlan } from "../../lib/types";
import { ProgressRing } from "../../components/plan";

type Auth = { configured: boolean; user: null | { id: string; email?: string } };
type Summary = { id: string; trail_id: string; trip_date: string };
type Company = { id: string; name: string } | null;

export default function WorkspacePage() {
  const [auth, setAuth] = useState<Auth>();
  const [plans, setPlans] = useState<Summary[]>([]);
  const [selected, setSelected] = useState<SavedPlan>();
  const [company, setCompany] = useState<Company>(null);
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState<Plan>();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [billing, setBilling] = useState(false);
  const generation = useRef(0);
  const mutation = useRef(false);

  const load = useCallback(async () => {
    const current = generation.current;
    try {
      const nextAuth = await api<Auth>("/api/auth");
      if (current !== generation.current) return;
      setAuth(nextAuth);
      if (!nextAuth.user) { setPlans([]); setSelected(undefined); setCompany(null); return; }
      const [list, workspace] = await Promise.all([
        api<{ plans: Summary[] }>("/api/plans"),
        api<{ company: Company; billing_enabled: boolean }>("/api/workspace"),
      ]);
      if (current !== generation.current) return;
      setPlans(list.plans); setCompany(workspace.company); setBilling(workspace.billing_enabled);
      try {
        const stored = sessionStorage.getItem("beready:pending-plan");
        if (stored) { const draft = JSON.parse(stored); if (draft?.version === 1 && typeof draft.trail_id === "string") setPending(draft); }
      } catch { setMessage("The browser could not restore an unsaved draft. Your account plans are unaffected."); }
    } catch (cause) { if (current === generation.current) setMessage((cause as Error).message); }
  }, []);
  useEffect(() => {
    void Promise.resolve().then(load);
    return () => { generation.current += 1; };
  }, [load]);

  const run = async (work: () => Promise<void>) => {
    if (mutation.current) return;
    mutation.current = true; setBusy(true); setMessage("");
    const current = generation.current;
    try { await work(); }
    catch (cause) { if (current === generation.current) setMessage((cause as Error).message); }
    finally { mutation.current = false; setBusy(false); }
  };
  const open = async (id: string) => {
    const current = generation.current;
    const result = await api<SavedPlan>(`/api/plans/${id}`);
    if (current === generation.current) setSelected(result);
  };
  const signOut = async () => {
    generation.current += 1;
    setPlans([]); setSelected(undefined); setCompany(null); setPending(undefined); setBilling(false);
    setCompanyName(""); setEmail("");
    try { sessionStorage.removeItem("beready:pending-plan"); } catch { /* Browser storage may be unavailable. Server sign-out must still run. */ }
    setAuth({ configured: true, user: null });
    try { await api("/api/auth", { method: "DELETE" }); setMessage("Signed out."); }
    catch { setMessage("Sign-out could not be confirmed. Please try again before leaving this shared browser."); }
  };
  if (!auth) return <main>{message ? <><p role="alert">{message}</p><button onClick={() => void load()}>Retry workspace</button></> : <p aria-busy="true">Loading workspace…</p>}</main>;

  return <main className="stack">
    <header className="page-intro"><p className="eyebrow">Workspace</p><h1>Saved preparation plans</h1><p>Plan progress tracks sessions, not fitness or mountain safety.</p></header>
    {message && <p role="status">{message}</p>}
    {!auth.configured ? <section className="card"><h2>Saving is not configured</h2><p>Free plans remain available. Managed sign-in is not configured for this pilot.</p></section> : !auth.user ? <section className="card"><h2>Sign in to your workspace</h2><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label><button disabled={busy || !email.trim()} onClick={() => void run(async () => { await post("/api/auth", { email }); setMessage("Check your email for a managed sign-in link."); })}>Send sign-in link</button>{message.includes("Sign-out") && <button onClick={() => void signOut()}>Retry sign out</button>}</section> : <>
      <section className="card"><h2>Your plans</h2>{plans.length ? <ul>{plans.map((plan) => <li key={plan.id}><button disabled={busy} className="text-button" onClick={() => void run(() => open(plan.id))}>{plan.trail_id}, trip {plan.trip_date}</button></li>)}</ul> : <p>No saved plans yet.</p>}</section>
      {pending && <section className="card"><h2>Pending plan</h2><p>{pending.trail_id}, trip {pending.trip_date}</p><button disabled={busy} onClick={() => void run(async () => { const result = await post<{ id: string }>("/api/plans", { plan: pending }); sessionStorage.removeItem("beready:pending-plan"); setPending(undefined); await load(); await open(result.id); setMessage("Plan saved."); })}>Save pending plan</button></section>}
      {selected && <SavedDetail value={selected} busy={busy} onToggle={(sessionId, done) => run(async () => { const current = generation.current; const result = await api<SavedPlan>(`/api/plans/${selected.id}`, { method: "PATCH", body: JSON.stringify({ session_id: sessionId, done }) }); if (current === generation.current) setSelected(result); })} onDelete={() => run(async () => { if (!confirm(`Delete the plan for ${selected.plan.trail_id}?`)) return; await api(`/api/plans/${selected.id}`, { method: "DELETE" }); setSelected(undefined); await load(); })} />}
      <section className="card"><h2>Company workspace</h2>{company ? <p>{company.name}</p> : <><label>Company name (optional)<input value={companyName} maxLength={100} onChange={(event) => setCompanyName(event.target.value)} /></label><button disabled={busy || !companyName.trim()} onClick={() => void run(async () => { const result = await post<{ company: Company }>("/api/workspace", { name: companyName }); setCompany(result.company); })}>Create company workspace</button></>}</section>
      {billing && <button disabled={busy} onClick={() => void run(async () => { const result = await post<{ url: string }>("/api/billing", {}); const url = new URL(result.url); if (url.protocol !== "https:" || url.hostname !== "checkout.stripe.com") throw new Error("Checkout returned an unexpected address."); window.location.assign(url.href); })}>Open hosted pilot checkout</button>}
      <button className="light" disabled={busy} onClick={() => void signOut()}>Sign out</button>
    </>}
  </main>;
}

function SavedDetail({ value, busy, onToggle, onDelete }: { value: SavedPlan; busy: boolean; onToggle: (id: string, done: boolean) => Promise<void>; onDelete: () => Promise<void> }) {
  const today = new Date().toISOString().slice(0, 10);
  return <section className="card"><ProgressRing progress={value.progress} /><h2>{value.plan.trail_id}</h2>
    {[...new Set(value.plan.sessions.map((session) => session.week))].map((week) => <section className="plan-week" key={week}><h3>Week {week}</h3>{value.plan.sessions.filter((s) => s.week === week).map((session) => <label className="session" key={session.id}><input type="checkbox" disabled={busy || session.date > today} checked={value.logs.some((log) => log.session_id === session.id)} onChange={(event) => void onToggle(session.id, event.target.checked)} /> {session.date}, {session.label}{session.adapted ? " (adapted)" : ""}</label>)}</section>)}
    <div className="plan-actions"><a className="button light" href={`data:application/json,${encodeURIComponent(JSON.stringify(value))}`} download="beready-plan.json">Export plan JSON</a><button disabled={busy} onClick={() => void onDelete()}>Delete this plan</button></div>
  </section>;
}
