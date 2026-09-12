# Architecture

## Two interfaces, one policy

`beready/core.py` owns deterministic assessment, ranking, dated plan generation, missed-week adaptation and completion-based progress. `beready/trails.py` owns the curated catalog and provenance. Neither imports an LLM, database or web framework.

The existing `app.py` remains the Streamlit entry point. Its quick check consumes Python-generated assessment data, and chat wraps the same policy. `web/` is the commercial Next.js App Router application. It looks up the compiled `web/public/catalog.json` for 9 trails x 3 training levels x 52 integer week values. The browser can filter and sort records, never recompute a verdict or preparation threshold.

`python -m beready.catalog --write` regenerates the catalog. `--check` is a CI gate. Schema version 1 and the TypeScript definitions are committed with the catalog.

## Dynamic services

```
Browser -> Next.js same-origin /api/* -> Python /plan, /progress, /ask, /conditions
        -> Next.js account handlers  -> Supabase Auth + PostgreSQL with RLS
        -> Next.js hosted checkout   -> Stripe, disabled until configured
```

Plan preview is stateless and does not require an account. Dynamic Python inputs are validated and responses never depend on model prose. Next proxies only named endpoints, never a user-supplied URL. It does not forward browser cookies to Python. CORS is deliberately not enabled on the policy service. Place Python behind a private network or request-limiting gateway in production.

Supabase credentials are used server-side. Supabase verifies identities, owner RLS enforces access to every saved plan/session/log and company workspace. No browser token storage or custom password database. Account mutations require same-origin requests. Saved assessments and sessions are regenerated from inputs rather than trusted from the browser. Authenticated database roles cannot insert or rewrite canonical plans/sessions or execute the save RPC. A server-only trusted writer performs that single atomic operation using the verified owner's ID. All owner reads, logs, deletes and company operations retain the user-scoped RLS client.

## Safety-relevant boundaries

- Fitness assessment is not medical advice, technical mountaineering ability, or clearance to hike.
- Every generation uses the actual dated interval, not a stale slider value. Less than one full week is rejected. The catalog supports up to 52 weeks.
- Dated sessions and adaptation are a conservative, provisional planning model that still needs conditioning review. An insufficient-runway verdict is not repaired by logging checkboxes.
- Progress is percent of canonical sessions completed, not a validated physiological readiness formula. Future, unknown, duplicate and early logs cannot manufacture credit.
- Typical season does not mean open. Exposure is an editorial field awaiting approval. Newer supplied season values supersede the draft, with provenance retained.
- Forecasts describe a representative point, not every part of a route. Unknown closure/snow safety stays unknown. A failure never blocks the plan. Dates outside the 16-day forecast window do not show a current forecast as a future prediction.
- Discovery text parsing is deliberately bounded. It asks when unsure. It does not generate assessments. Unsupported demand is logged without storing user messages or medical details.

## References and contracts

- [API and JSON shapes](contracts.md)
- [Architecture decision](decisions/001-commercial-foundation.md)
- [Account and database setup](account-setup.md)
- [Release gates](release-checklist.md)
- [Operations](operations.md)
