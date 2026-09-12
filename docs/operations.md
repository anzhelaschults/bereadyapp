# Operations and observability

## Questions the service must answer
1. Are users getting plans, or errors/timeouts?
2. Is failure in the Next proxy, Python policy service, account provider or forecast provider?
3. How often do forecasts degrade to static notes?
4. Are users asking for unsupported trails/regions, without collecting raw private messages?

## Signals
Python emits JSON `http_request` events with generated request_id, method, bounded route template, status and duration_ms. `conditions_fetch` includes outcome and duration. `catalog_demand` records only unknown_trail/unknown_region counts, not raw query text. Next public proxy emits `policy_request` and `policy_unavailable`, also without bodies, cookies or query strings. Account handlers use their own allowlisted structured events.

Configure the log collector to build request-count/error-count series and latency histograms from these events. Use only route, status class, provider and outcome as metric labels. IDs and free text must not become labels. No telemetry vendor credentials are required for local development. Dashboards, alert delivery and distributed tracing are deployment configuration gates, not verified here. The API accepts only UUID-shaped correlation IDs and otherwise generates one. The Next public proxy forwards its generated ID to Python, so the same request can be followed across both services without forwarding cookies or user text.

## Runbook
- `/api/health` failing: check Next's configured BEREADY_API_URL, then Python `/health`. Do not inspect or paste environment secret values into logs.
- Plan failures: inspect status/duration by route. Validation failures are not provider outages. A Python outage must not break static verdicts or discovery.
- Auth failure: verify SUPABASE_URL/key presence, allowed callback origin, provider email quotas, RLS migration version and cookie transport. Never switch to service-role for ordinary user requests to bypass a policy error.
- Conditions failure: compare unavailable rate and forecast horizon. Disable CONDITIONS_ENABLED if needed. Never substitute current weather for future dates or imply closures are known.
- Billing issue: disable BILLING_ENABLED, inspect verified webhook event processing. Do not infer entitlement from a success URL or re-run a live charge to debug.

## Proposed alerts, must be exercised in staging
- Page: plan/progress 5xx >1% for 5 minutes or p95 >2 seconds for 5 minutes. Confirm the health route and inspect matching JSON events. Establish baseline before rollout.
- Page immediately: any confirmed cross-user access, erroneous verdict or leaked credential. Disable affected access, preserve evidence, rotate exposed keys.
- Ticket: forecast fallback >20% for 30 minutes within supported horizon. Check provider configuration/license and upstream status. Plan remains usable.

No paging destination is configured by this implementation. A named on-call/release owner must set it up and exercise delivery before launch.

## Deployment boundaries
Use HTTPS at the edge and a private policy service. Enforce request timeouts, a 64 KiB web input cap, backend 256 KiB cap, bounded concurrency and per-IP rate limits at the gateway. Do not cache authentication routes or Set-Cookie responses. Do not expose Supabase/PostgreSQL administrator ports publicly. Keep deployment, test and production providers separate.

Next sets CSP, frame denial, MIME sniffing protection, referrer/permissions policies and production HSTS. CSP allows inline scripts for Next hydration and inline styles for computed runway/progress positions. No user HTML is rendered. Development alone permits script evaluation and WebSocket connections. A per-request nonce policy is a further hardening option when choosing fully dynamic hosting. Validate these headers at the actual HTTPS edge, including any reverse-proxy overrides.
