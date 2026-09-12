begin;
select plan(13);

-- Requires Supabase local test database with pgTAP, auth.users, and service_role available.
insert into auth.users (id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data, created_at, updated_at)
values
 ('11111111-1111-4111-8111-111111111111','00000000-0000-0000-0000-000000000000','authenticated','authenticated','owner@example.test','',now(),'{}','{}',now(),now()),
 ('22222222-2222-4222-8222-222222222222','00000000-0000-0000-0000-000000000000','authenticated','authenticated','attacker@example.test','',now(),'{}','{}',now(),now());

-- Only trusted infrastructure seeds canonical rows, always with explicit ownership.
set local role service_role;
insert into public.prep_plans (id,owner_id,trail_id,fitness,start_date,trip_date,plan)
values ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','11111111-1111-4111-8111-111111111111','test-trail',1,'2025-01-01','2025-01-08','{"version":"1"}');
insert into public.plan_sessions(plan_id,session_id,week,day,session_date,session) values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa01',1,1,'2025-01-01','{"id":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa01","week":1,"day":1,"date":"2025-01-01"}');

set local role authenticated;
select set_config('request.jwt.claim.sub', '22222222-2222-4222-8222-222222222222', true);
select is((select count(*) from public.prep_plans), 0::bigint, 'cross-user plan reads are hidden');
select throws_ok($$insert into public.session_logs(owner_id,plan_id,session_id) values ('22222222-2222-4222-8222-222222222222','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa01')$$, '42501', null, 'cross-user session log write is blocked');
select throws_ok($$insert into public.prep_plans(owner_id,trail_id,fitness,start_date,trip_date,plan) values ('22222222-2222-4222-8222-222222222222','forged',1,'2025-01-01','2025-01-08','{"version":"1"}')$$, '42501', null, 'authenticated canonical plan insert is blocked');
select throws_ok($$insert into public.plan_sessions(plan_id,session_id,week,day,session_date,session) values ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',1,2,'2025-01-02','{"id":"bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb","week":1,"day":2,"date":"2025-01-02"}')$$, '42501', null, 'authenticated canonical session insert is blocked');
select throws_ok($$select public.save_prep_plan('{"version":"1","trail_id":"trail","fitness":"1","start_date":"2025-01-01","trip_date":"2025-01-08","sessions":[]}'::jsonb, '22222222-2222-4222-8222-222222222222')$$, '42501', null, 'authenticated cannot execute trusted RPC');

set local role anon;
select throws_ok($$select * from public.prep_plans$$, '42501', null, 'anon cannot read plans after explicit privilege revoke');

set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);
select throws_ok($$insert into public.session_logs(plan_id,session_id) values ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb')$$, '22023', null, 'missing session is rejected by the log validator');
insert into public.session_logs(plan_id,session_id,done_at) values ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa01','2025-01-01');
select is((select count(*) from public.session_logs), 1::bigint, 'owner can log own known session');

set local role service_role;
select throws_ok($$update public.plan_sessions set session_date='2025-01-02', session=jsonb_set(session,'{date}','"2025-01-02"') where plan_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'$$, '22023', null, 'completed session cannot be moved after done_at');
select lives_ok($$select public.save_prep_plan('{"version":"1","trail_id":"trail","fitness":"1","start_date":"2025-01-01","trip_date":"2025-01-08","sessions":[{"id":"cccccccc-cccc-4ccc-8ccc-cccccccccccc","week":"1","day":"1","date":"2025-01-01"}]}'::jsonb, '22222222-2222-4222-8222-222222222222')$$, 'trusted RPC saves explicit owner plan');
select is((select count(*) from public.prep_plans where owner_id='22222222-2222-4222-8222-222222222222'), 1::bigint, 'trusted RPC preserves owner isolation');

set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);
delete from public.prep_plans where id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
select is((select count(*) from public.plan_sessions where plan_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'), 0::bigint, 'owner plan delete cascades sessions');
select is((select count(*) from public.session_logs where plan_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'), 0::bigint, 'owner plan delete cascades logs');

select * from finish();
rollback;
