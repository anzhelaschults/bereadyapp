# Account, workspace, saved-plan, and billing setup

This slice is intentionally safe when no provider is configured: `GET /api/auth` returns
`{configured:false,user:null}` and saves return a clear 503. It never creates a local or
browser-stored account. Auth uses only Supabase's server cookie client and `getUser()`;
do not add a browser Supabase client or store access tokens in localStorage.

## Required configuration

Set these **server-side** values (do not commit them):

```sh
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_PUBLISHABLE_KEY=<publishable-anon-key>
# Server-only canonical-plan writer; never prefix this NEXT_PUBLIC_ or expose it to a browser.
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
# Legacy public-key fallbacks also supported: NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY
APP_URL=https://app.example.com
BEREADY_API_URL=http://localhost:8000
BILLING_ENABLED=false
```

`APP_URL` must be the exact deployed application origin. In Supabase Auth, configure it
as the Site URL and allow only `https://app.example.com/auth/callback` as a redirect URL.
The code never accepts a request-provided return URL. Configure managed email OTP in
Supabase; enforce its rate limits and add gateway rate limiting/WAF for `/api/auth` before
launch. Cookies are issued by `@supabase/ssr` as httpOnly, secure (in production), and
same-site cookies.

Install the reviewed, locked frontend dependencies from the repository root:

```sh
cd web
npm ci
```

The plan-save route verifies the session with the cookie client, regenerates the plan server-side, and only then uses `SUPABASE_SERVICE_ROLE_KEY` in a server-only client to call the trusted write RPC. This key must never be browser-exposed, logged, or placed in any `NEXT_PUBLIC_*` variable.

## Database deployment and RLS verification

This is an initial schema for a fresh private staging project. Review existing schemas and back up data before applying it anywhere else. The migration's explicit privilege revocations must not be blindly applied to a shared project.

1. Link the intended non-production Supabase project.
2. Apply `supabase/migrations/20250912000100_account_plan_baseline.sql` with `supabase db push`.
3. Run the pgTAP abuse suite against an isolated local Supabase database:

   ```sh
   supabase start
   supabase test db supabase/tests/account_plan_rls.sql
   ```

The test covers cross-user reads/writes, anon access, direct canonical-write and RPC denial,
trusted explicit-owner RPC writes, completed-session rescheduling, and plan cascades. It must pass before treating RLS as
verified. It was not run in this checkout because no local Docker/Supabase daemon was
available; `psql` alone does not provide the required `auth` schema, roles, or pgTAP.

## Python dependency and route integration

Run the Python service on the fixed `BEREADY_API_URL` origin. The server helper only calls
`POST /plan` and `POST /progress`, with a 10-second timeout; it validates response shape.
Saving discards client-provided sessions and assessment, regenerates a canonical plan, then
uses a server-only service-role client and the `save_prep_plan(jsonb, uuid)` RPC to atomically
persist its metadata and sessions under the verified user ID. Detail and
completion routes fetch persisted sessions/logs through RLS and recompute progress through
Python. Completion writes are idempotent by `(plan_id, session_id)` and future session dates
are rejected in UTC.

## Billing launch gate

Billing is off unless `BILLING_ENABLED=true`. Checkout additionally requires
`STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`, `BILLING_DATABASE_URL`,
and `APP_URL`; the server selects the price and uses fixed workspace return URLs. The
webhook verifies Stripe's raw-body signature, then writes a parameterized `ON CONFLICT DO
NOTHING` record to the private `private.billing_webhook_events` table through the dedicated
`BILLING_DATABASE_URL` connection. A ledger failure returns 503 so Stripe retries. It never
creates an entitlement from client metadata or from this ledger alone. Provision a dedicated database login with only schema usage and the ledger insert/select privileges needed for this connection, not a general administrator login. Do not expose a
SECURITY DEFINER event-recording RPC to anon or authenticated clients.

## Rollback

Leave `BILLING_ENABLED=false` to stop new Checkout sessions immediately. To roll back the
account feature, remove route exposure at the deployment layer; do **not** drop tables
while accounts exist. A later reviewed migration can revoke policies/RPC execute grants,
then archive data under the approved retention policy. Database migrations are additive and
are not automatically reversed.

## Manual launch gates

- Real Supabase OTP delivery and staging callback test
- Local pgTAP suite and cross-user route integration test
- Production HTTPS/domain/cookie verification
- Privacy/legal retention review for account email and workspace name
- Stripe test-mode webhook ledger, retry, and reconciliation test (only if billing enabled)
- Operator-approved rate limiting, monitoring, and rollback owner
