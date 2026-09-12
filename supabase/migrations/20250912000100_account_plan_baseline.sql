-- Account/workspace and saved-plan baseline. Browser access is authenticated RLS only.
create extension if not exists pgcrypto;
create schema if not exists private;

create table public.companies (
 id uuid primary key default gen_random_uuid(), owner_id uuid not null unique default auth.uid() references auth.users(id) on delete cascade,
 name text not null check (char_length(name) between 1 and 100), created_at timestamptz not null default now());
create table public.prep_plans (
 id uuid primary key default gen_random_uuid(), owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 trail_id text not null check (trail_id ~ '^[a-z0-9-]{1,100}$'), fitness smallint not null check (fitness between 1 and 3),
 start_date date not null, trip_date date not null check (trip_date > start_date and trip_date <= start_date + 364),
 plan jsonb not null check (plan->>'version' = '1'), created_at timestamptz not null default now());
create table public.plan_sessions (
 plan_id uuid not null references public.prep_plans(id) on delete cascade, session_id uuid not null,
 week smallint not null check (week between 1 and 52), day smallint not null check (day between 1 and 7), session_date date not null,
 session jsonb not null, primary key (plan_id,session_id), unique(plan_id,week,day),
 check (session->>'id'=session_id::text), check ((session->>'week')::smallint=week), check ((session->>'day')::smallint=day), check ((session->>'date')::date=session_date));
create table public.session_logs (
 owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade, plan_id uuid not null, session_id uuid not null,
 done_at date not null default (now() at time zone 'utc')::date, created_at timestamptz not null default now(), primary key(plan_id,session_id),
 foreign key(plan_id,session_id) references public.plan_sessions(plan_id,session_id) on delete cascade);
create table private.billing_webhook_events (stripe_event_id text primary key, event_type text not null, received_at timestamptz not null default now());

-- Do not depend on Supabase's historical defaults: anon has no table or RPC access.
revoke all on all tables in schema public from anon, authenticated;
revoke all on all tables in schema private from public, anon, authenticated;
revoke all on all functions in schema public from public, anon, authenticated;
grant usage on schema public to authenticated, service_role;
grant select,insert,update,delete on public.companies,public.session_logs to authenticated;
grant select,delete on public.prep_plans to authenticated;
grant select on public.plan_sessions to authenticated;
-- Canonical plan writes are performed only by the trusted Next.js server using this role.
grant select,insert,update,delete on public.prep_plans,public.plan_sessions to service_role;

alter table public.companies enable row level security;
alter table public.prep_plans enable row level security;
alter table public.plan_sessions enable row level security;
alter table public.session_logs enable row level security;
create policy companies_owner_all on public.companies for all to authenticated using(owner_id=auth.uid()) with check(owner_id=auth.uid());
create policy plans_owner_select on public.prep_plans for select to authenticated using(owner_id=auth.uid());
create policy plans_owner_delete on public.prep_plans for delete to authenticated using(owner_id=auth.uid());
create policy sessions_owner_select on public.plan_sessions for select to authenticated using(exists(select 1 from public.prep_plans p where p.id=plan_id and p.owner_id=auth.uid()));
create policy logs_owner_all on public.session_logs for all to authenticated using(owner_id=auth.uid() and exists(select 1 from public.prep_plans p where p.id=plan_id and p.owner_id=auth.uid())) with check(owner_id=auth.uid() and exists(select 1 from public.prep_plans p where p.id=plan_id and p.owner_id=auth.uid()));

create or replace function public.validate_plan_session() returns trigger language plpgsql security definer set search_path=public as $$
declare p public.prep_plans;
begin
 if tg_op = 'UPDATE' and (new.plan_id, new.session_id) is distinct from (old.plan_id, old.session_id) then
  raise exception 'canonical session identity is immutable' using errcode='22023';
 end if;
 select * into p from public.prep_plans where id=new.plan_id;
 if not found or new.session_date < p.start_date or new.session_date >= p.trip_date then raise exception 'session date outside plan interval' using errcode='22023'; end if;
 if tg_op = 'UPDATE' and new.session_date is distinct from old.session_date and exists (
  select 1 from public.session_logs where plan_id=old.plan_id and session_id=old.session_id and done_at < new.session_date
 ) then
  raise exception 'cannot move a completed session after its completion date' using errcode='22023';
 end if;
 return new;
end $$;
create trigger plan_session_date_guard before insert or update on public.plan_sessions for each row execute function public.validate_plan_session();
create or replace function public.validate_session_log() returns trigger language plpgsql security definer set search_path=public as $$
declare scheduled date;
begin
 select session_date into scheduled from public.plan_sessions where plan_id=new.plan_id and session_id=new.session_id;
 if not found or new.done_at < scheduled or new.done_at > (now() at time zone 'utc')::date then raise exception 'invalid completion date' using errcode='22023'; end if;
 return new;
end $$;
create trigger session_log_date_guard before insert or update on public.session_logs for each row execute function public.validate_session_log();

create or replace function public.save_prep_plan(p_plan jsonb, p_owner_id uuid) returns uuid language plpgsql security invoker set search_path=public as $$
declare v_plan_id uuid; v_start date; v_trip date; v_days integer;
begin
 if p_owner_id is null then raise exception 'plan owner is required' using errcode='22023'; end if;
 if jsonb_typeof(p_plan) is distinct from 'object' or p_plan->>'version' is distinct from '1' or jsonb_typeof(p_plan->'sessions') is distinct from 'array' then raise exception 'invalid canonical plan' using errcode='22023'; end if;
 begin v_start:=(p_plan->>'start_date')::date; v_trip:=(p_plan->>'trip_date')::date; end;
 v_days:=v_trip-v_start;
 if v_days not between 7 and 364 or (p_plan->>'trail_id') !~ '^[a-z0-9-]{1,100}$' or (p_plan->>'fitness')::smallint not between 1 and 3 or jsonb_array_length(p_plan->'sessions')>156 then raise exception 'invalid canonical plan metadata' using errcode='22023'; end if;
 if exists(select 1 from jsonb_array_elements(p_plan->'sessions') x(value) where jsonb_typeof(x.value) is distinct from 'object' or (x.value->>'week')::smallint not between 1 and 52 or (x.value->>'day')::smallint not between 1 and 7 or (x.value->>'date')::date < v_start or (x.value->>'date')::date >= v_trip) then raise exception 'invalid canonical session' using errcode='22023'; end if;
 insert into public.prep_plans(owner_id,trail_id,fitness,start_date,trip_date,plan) values(p_owner_id,p_plan->>'trail_id',(p_plan->>'fitness')::smallint,v_start,v_trip,p_plan-'sessions') returning id into v_plan_id;
 insert into public.plan_sessions(plan_id,session_id,week,day,session_date,session) select v_plan_id,(x.value->>'id')::uuid,(x.value->>'week')::smallint,(x.value->>'day')::smallint,(x.value->>'date')::date,x.value from jsonb_array_elements(p_plan->'sessions') x(value);
 return v_plan_id;
end $$;
revoke all on function public.save_prep_plan(jsonb,uuid) from public, anon, authenticated;
grant execute on function public.save_prep_plan(jsonb,uuid) to service_role;
