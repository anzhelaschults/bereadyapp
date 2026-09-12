# Shared implementation contracts, schema v1

Python JSON uses snake_case. The TypeScript definitions in web/lib/types.ts are the frontend contract. Strict integer fitness 1,2,3 and weeks 1..52. Dates are ISO calendar dates, UTC today on the API. Unknown trail, missing level, missing time or medical requests never manufacture an assessment.

## Python
- `beready.trails.TRAILS`: dict keyed by stable lower-case trail id. Each record has all Trail fields other than assessments.
- `beready.core.assess(trail_id: str, fitness: int, weeks: int) -> Assessment`
- `beready.core.discover(fitness, weeks, filters=None, today=None) -> list[dict]`: each returned trail has `assessment` singular. Filters: region (Norway/Iceland), length (day/multi), max_grade (1..4), hide_exposed (bool), in_season (bool), reachable (bool). Empty filters keep all trails, status weights ready=0,cond=1,hard=2,toosoon=3, diff then km then id.
- `beready.core.build_plan(trail_id, fitness, start_date, trip_date) -> Plan`. Accept ISO date strings or date objects. 7..364 days, available weeks=floor(days/7). Session IDs are deterministic UUID strings. Day is 1..7 relative to start_date. Never schedule on/after trip date. Full last 2 days are rest. Stable IDs during adaptation.
- `beready.core.adapt_plan(plan, logs, today) -> Plan`. Logs are list of {session_id, done_at: ISO date string}. Repeat base work after a fully missed completed week, never stack extra load. No mutation. Historical sessions/IDs unchanged.
- `beready.core.readiness(plan, logs, today) -> Progress`. Score is completion percent over total canonical sessions, not physiological fitness. Ignore unknown, duplicate or future logs. on_track means all sessions strictly before today completed. Streak counts consecutive completed full plan weeks through last completed week, not future weeks.
- `python -m beready.catalog --write` writes web/public/catalog.json, deterministic serialization. `--check` exits nonzero for stale catalog. All integer weeks 1..52 compiled.

## Public Python API and same-origin Next proxy
`POST /plan` (`/api/plan` in web) body: {trail_id, fitness, weeks, start_date?: ISO, trip_date?: ISO}. Missing start defaults UTC today, missing trip defaults start + weeks*7. Supplied trip_date takes precedence and actual weeks recomputed. Response Plan.
`POST /progress` body: {plan: Plan, logs: SessionLog[], today?: ISO}. Server must regenerate/validate canonical plan from inputs rather than trust user sessions/assessment. Response {plan: adapted Plan, progress: Progress}.
`GET /conditions?trail=<id>&date=YYYY-MM-DD` -> Conditions.
`POST /discover` body {fitness, weeks, filters?} -> {trails: (Trail & {assessment: Assessment})[]}.
`POST /ask` body {query: string max 1000} -> {message: string, trails?: (Trail & {assessment: Assessment})[], assessment?: Assessment, trail_id?: string}. Deterministic guarded parser, not a model-fabricated answer.
`GET /health` -> {status:'ok',schema_version:1}.
Errors use {error:{code,message}}, no stack traces, 422 validation, 503 dependency unavailable. Request body cap 256 KiB at Python, 64 KiB public input, deadlines and no arbitrary upstream URL.

## Next account routes
All cookie-session endpoints are dynamic/no-store. Supabase auth verified via getUser. Owner reads, logs, deletes and company mutations use the user-scoped RLS client. Only canonical plan persistence uses a server-only trusted writer after Python regeneration, with the owner taken from the verified user, never request JSON. Mutations require same Origin, bounded JSON, safe error envelope.
- GET /api/auth -> {configured:boolean,user: null|{id,email?}}
- POST /api/auth body {email} -> {message}; managed email OTP, redirect to fixed APP_URL/auth/callback. No passwords stored. Supabase rate limits plus gateway protections documented.
- DELETE /api/auth -> {ok:true} sign out.
- GET /auth/callback exchanges provider code, redirects only to the configured APP_URL origin plus /workspace, never the request host.
- GET /api/plans -> {plans: [{id,trail_id,fitness,start_date,trip_date,created_at}]}
- POST /api/plans body {plan:Plan} -> {id}; regenerate plan through Python and atomically persist via SQL RPC. Never trust caller ownership. ID generated in DB.
- GET /api/plans/[id] -> {id,plan:Plan,logs:SessionLog[],progress:Progress}. Use saved canonical metadata and SQL sessions. Progress recomputed by Python, not browser.
- PATCH /api/plans/[id] body {session_id:string,done:boolean} -> same shape as GET. Owner enforcement and composite session FK. Future completion rejected.
- DELETE /api/plans/[id] -> {ok:true} cascade.
- GET /api/workspace -> {company:null|{id,name},billing_enabled:boolean}
- POST /api/workspace body {name:string 1..100} -> {company:{id,name}}. Owner scoped, one company per user for pilot, no public membership/invite elevation.
- POST /api/billing -> {url:string} or disabled 503. Supabase verified user. Server-selected price, Stripe hosted checkout, user binding, no client prices. Only pilot subscription, never gate viewing plans.
- POST /api/billing/webhook: raw body signature verification, no client entitlement claims. If billing is enabled use verified event idempotency. Do not expose management credentials to browser.

When account providers are absent, form/discovery/free plans work. Save fails clearly as not configured, never silently uses fake account or localStorage persistence.
