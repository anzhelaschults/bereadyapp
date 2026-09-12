# ADR-001: Python policy with compiled assessments and managed account services

Status: Accepted for local implementation. Commercial release requires the listed sign-offs.

## Context
The supplied engineering plan assumes a commercial foundation absent from GitHub main. The live MVP also had a second scorer embedded in browser JavaScript. The product's trust rule forbids that duplication. The product needs fast interactive verdicts without accounts, followed by genuinely dated plans and saved progress.

## Decision
Extract the existing Python policy. Compile its finite input space (9 trails, 3 levels, 1..52 whole weeks) into a checked-in catalog. Next.js does lookup/filter/sort only. FastAPI serves date-dependent operations. Prefer explicit errors over a local browser fallback that recomputes policy.

Use Supabase managed email authentication, server-only cookie sessions and PostgreSQL RLS for user data. Regenerate plans before saving and use one database transaction. Adversarial testing showed that owner RLS alone still allowed an owner to forge canonical plan content through direct database writes. Authenticated roles therefore receive no canonical insert/update or save-RPC privilege. Only a server-only service-role writer can atomically persist a regenerated plan, using the verified user's ID. Other account operations stay user-scoped under RLS. Adopt Stripe hosted checkout for a separately flagged operator pilot, not a paywall around the free plan. Do not deploy or configure external services automatically.

The physiological readiness formula and progression prescription have no approved source in the documents. Implement conservative provisional sessions and a clearly labeled completion score instead. Never present it as proof of fitness. Content/exposure approval and provider licensing are external gates.

## Alternatives
- Duplicate scoring in TypeScript: rejected because policies can drift and it violates the explicit product rule.
- Call an API for every slider tick: unnecessary latency and backend availability dependence for a finite deterministic input space.
- Rebuild Streamlit as the commercial interface: rejected because the documents explicitly specify Next.js, while retaining Streamlit protects the existing deployment.
- Store plans/tokens in localStorage: rejected. It is not account persistence, cannot enforce ownership and exposes session material to scripts.
- Model-generated plans/verdicts: rejected for safety, reproducibility and testability. The legacy Streamlit model-dispatch path was also removed rather than relying on prompts to preserve the user's inputs or verdict. Ask remains available without a key, using the guarded deterministic parser.

## Consequences
Catalog size increases with supported time inputs, so changes to range/schema need coordinated generation and UI testing. Dates are handled dynamically on the server. Two runtimes must be deployed, but only the dynamic plan service depends on Python availability during use. Public check/discovery remain usable if that service fails. Provider configuration and manual staging verification remain necessary.

## Sources checked during implementation
- Next.js installation and App Router: https://nextjs.org/docs/app/getting-started/installation
- Route handler request/response and async route params: https://nextjs.org/docs/app/api-reference/file-conventions/route
- Supabase SSR cookies and verified user identity: https://supabase.com/docs/guides/auth/server-side/creating-a-client
- PostgreSQL grants plus owner policies: https://supabase.com/docs/guides/database/postgres/row-level-security
- FastAPI request models: https://fastapi.tiangolo.com/tutorial/body/
- Open-Meteo date horizon and daily variables: https://open-meteo.com/en/docs
- Commercial weather licensing: https://open-meteo.com/en/pricing

Exact installed JavaScript dependencies are in web/package-lock.json. Python policy dependencies are in uv.lock. No third-party secrets are part of either lockfile.
