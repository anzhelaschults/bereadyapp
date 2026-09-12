# Road to commercial implementation

## Scope and baseline
Source: decision documents 00 through 04 and HTML concepts in the sibling `BeReady road to commercial` folder. GitHub main at fe0b867 is a single-file Streamlit MVP, not the commercial foundation assumed by the engineering spec. Build that missing foundation first. The newer `04 Trail data fields.docx` explicitly supersedes the draft `(1)`.

User authorized implementation without further questions. Work locally on feature/road-to-commercial. Do not deploy, send real authentication mail, charge customers, invent sign-offs, or modify external infrastructure.

## Decisions
- One pure Python scorer, compiled to a versioned catalog for all 9 trails, all 3 fitness levels, and integer weeks 1 through 52. Browser only looks up assessments and sorts them.
- Next.js App Router with TypeScript. FastAPI for dynamic dated plans, progress, deterministic natural-language discovery, and conditions. Same-origin Next route handlers proxy the allowlisted Python endpoints.
- Supabase Auth and PostgreSQL RLS for saved plans and owner-scoped company workspaces. Only server-side cookie sessions, no browser token storage. Stripe hosted checkout is disabled unless explicitly configured.
- A plan is free and available without an account. Sign-up only at save. Weeks at the check. Date is optional at plan stage. A date change recomputes assessment using actual available whole weeks.
- Provisional conservative plan: 3 sessions each full week with intervening rest days and a lighter final week. Too-soon plans never imply the selected trail is achievable. Missed-week adaptation repeats base work, never catches up by increasing load.
- No validated physiological readiness formula exists in the docs. Show completion-based plan progress, explicitly not a fitness or mountain-safety clearance. Logging never changes the trail verdict.
- Static content and exposure flags retain review-pending provenance. Seasons are typical, never a guarantee of access. Live closure or snow safety is never inferred from a forecast. Conditions degrade independently of plans.

## Ordered slices and verification
1. Core/catalog parity: extract existing Python policy and trails. Remove browser scorer from Streamlit. Unit-test thresholds, refusals, catalog completeness and parity.
2. Quick check: Next scaffold, native radio cards, weeks slider, null initial fitness, assessment and runway. Unit and Playwright checks of each verdict state.
3. Motivation/discovery: reviewed-status content for all levels, typical conditions, explicit filters, stable ranking, compare 2 or 3. Python parity and browser tests.
4. Dated plan/progress: deterministic generation and adaptation, API boundary validation, free UI and truthful progress. Unit, API and browser checks.
5. Accounts/workspace: managed email auth, atomic save, reloadable session completion, owner-only RLS and deletion/export. SQL abuse tests and route tests. Local provider integration where tooling permits.
6. Conditions/discovery API: bounded and validated external forecast, unavailable fallback, deterministic discovery tool and redacted demand events. Mock external-boundary tests.
7. Commercial gates: disabled hosted checkout, workspace registration, privacy/pilot/rollback checklists. Provider-failure and disabled-feature tests.
8. Verify: pytest, catalog --check, npm lint/typecheck/test/build, Playwright with screenshots, accessibility, SQL tests, dependency audit and independent adversarial review.

## External launch gates
Real Supabase configuration and email delivery, licensed commercial weather access, verified route coordinates and content approval, conditioning professional approval of planning rules, privacy/legal approval, pricing validation and Stripe configuration, staging end-to-end auth/payment tests and two or three operator pilot participants. These cannot honestly be completed by writing code.
