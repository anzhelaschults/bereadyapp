# BeReady

**Can you handle this trail?** A deterministic fitness-preparation check for nine routes in Norway and Iceland. Verdicts come from Python policy, not a model. Unknown trails, missing inputs and medical questions do not receive invented answers.

This repository contains the existing Streamlit MVP and the commercial Next.js application. The decision documents and throwaway mockups live outside the code repository. See [architecture](docs/architecture.md), [contracts](docs/contracts.md), and [implementation checklist](tasks/todo.md).

## Run the commercial app locally

Requires Python 3.12+, Node.js 22+, npm and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --frozen --extra test
uv run python -m beready.catalog --check
uv run uvicorn beready.api:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd web
npm ci
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000. No account or LLM key is needed to check trails, discover/compare or view the full dated preparation plan. The Python service must be running for dated plans. The catalog-based verdict continues to work if it is unavailable.

The training level starts unselected. Choose one and move the weeks slider. The optional hike date appears only with the plan. Saving and persistent progress require configured Supabase, never a fake local account. See [account setup](docs/account-setup.md).

## Features and boundaries

- Shared Python scorer and checked-in catalog. Every verdict state has a preparation runway.
- Level-adaptive challenge/payoff content and typical season notes with review-pending provenance.
- Personalized discovery, explicit filters and comparison of two or three trails. Too-soon trails stay visible by default.
- Bounded natural-language discovery without a model inventing inputs or verdicts.
- Full free dated plan, conservative missed-week adaptation and server-computed completion progress.
- Managed email sign-in, owner-scoped saved plans/session logs and a company pilot workspace.
- Date-specific forecast adapter with independent unavailable/out-of-horizon fallback. Closure and route-snow safety remain unknown, never inferred from weather.
- Optional hosted operator checkout, disabled until configured and approved. Viewing a plan is never paywalled.

**Not a production release.** Trail/exposure and conditioning approval, provider configuration, real staging account/payment tests, weather licensing, privacy/legal sign-off and an operator pilot are separate [release gates](docs/release-checklist.md). Progress measures logged sessions, not physiological readiness or mountain safety.

## Verification

```bash
uv run pytest
uv run python -m beready.catalog --check
cd web
npm run lint
npm run typecheck
npm test
npm run build
E2E_PRODUCTION=true npm run e2e
npm audit --audit-level=high
```

Browser setup: `cd web && npx playwright install chromium`. Browser tests use isolated test profiles and capture screenshots under `docs/screenshots/`. For real owner-isolation tests, follow the SQL instructions in [account setup](docs/account-setup.md). External providers are stubbed at their boundaries in unit tests, never represented as verified live integration.

## Catalog changes

Edit `beready/trails.py` or `beready/core.py`, add regression tests, then run:

```bash
uv run python -m beready.catalog --write
uv run pytest
```

Commit `web/public/catalog.json` with the policy change. Never add scoring thresholds or status computation to browser code. New route facts need source and content-owner approval. The catalog includes whole weeks 1 through 52.

## Existing Streamlit MVP

```bash
uv sync --frozen --extra legacy
uv run --extra legacy streamlit run app.py
```

Live MVP: https://bereadyapp.streamlit.app

Both the form and Ask use the shared deterministic policy without an API key. The former model-generated chat path has been removed so it cannot change user inputs or override a verdict. Existing transcripts from that path are cleared on upgrade.

## Project map

```text
app.py                   Existing Streamlit interface
beready/core.py          Deterministic policy, plans and progress
beready/trails.py        Curated route facts and content provenance
beready/catalog.py       Reproducible browser catalog compiler
beready/api.py           Stateless FastAPI endpoints
beready/conditions.py    Validated forecast adapter and fallback
beready/discovery.py     Guarded natural-language catalog tool
web/                     Next.js UI and same-origin account/API handlers
supabase/                Owner-isolated schema and SQL tests
tests/                   Python policy and API regression tests
docs/                    Contracts, decisions, screenshots and release gates
```

See [operations](docs/operations.md) for configuration, telemetry and rollback. Do not deploy from this checklist without a named release owner and the required approvals.
