# Local verification

Verified on 2026-09-12 on the `feature/road-to-commercial` branch. This is implementation evidence, not production or provider approval.

## Passing checks

| Check | Evidence |
|---|---|
| Python regression suite | `uv run pytest`: 126 passed |
| Compiled policy parity | `uv run python -m beready.catalog --check`: passed. Nine trails, three levels, weeks 1 through 52 |
| Web unit/server/PostgreSQL tests | `cd web && npm test`: 40 passed across 11 files |
| Lint and types | `npm run lint` and `npm run typecheck`: passed |
| Production build | `npm run build`: passed |
| Production browser tests | `E2E_PRODUCTION=true npm run e2e`: 18 passed, real Python service, desktop 1440px and mobile 320px |
| Dependency audit | `npm audit --audit-level=high`: zero vulnerabilities. pip-audit against frozen exported Python dependencies: no known vulnerabilities |
| Diff hygiene | `git diff --check`: passed |

Browser checks cover unselected training level, keyboard use, all four verdicts and actual runway positions, level-adaptive challenges, full free plan, optional-date recomputation, source-labelled dated forecast, provider failure, static discovery, null-season/reachable behavior, three-trail comparison, bounded Ask, workspace error recovery, persisted checkbox UI after reload, export, deletion and clearing private state on logout. Automated axe checks cover initial, verdict, dated-plan, comparison and workspace states. Screenshots are in `docs/screenshots/` and were visually inspected. Mobile runway labels, progress-ring proportions and action-button separation were corrected during that inspection.

Account and forecast transports in the browser tests are **stubbed**. These tests prove browser behavior, not real managed login, storage or weather integration. The ordinary free-plan flow calls the real local Python service. Playwright disables external account, billing and forecast configuration to avoid contacting real providers.

## Security review and repairs

- The initial authenticated SQL/RPC write boundary could bypass Python regeneration. Authenticated roles now cannot create or rewrite canonical plans/sessions or execute the save RPC. A server-only trusted writer uses the verified user's ID after Python regeneration.
- Embedded PostgreSQL tests execute the migration and exercise owner/attacker/anonymous privileges, company isolation, child reads, owner deletion, logs, atomic trusted persistence and completion-reschedule guards.
- The callback formerly used the request host. It now uses only validated configured APP_URL. Regression tests include a hostile host and malformed configuration.
- Failed sign-out no longer returns a false success.
- Legacy Streamlit model dispatch could alter tool inputs or final prose. It was removed. Keyless AppTest cases prove canonical output and medical/override/missing-input refusals.
- React Strict Mode abort handling and mobile table keyboard access were repaired in browser verification.

## Limits and external gates

- Supabase local pgTAP is included in CI, but **was not executed locally** because the Docker daemon was unavailable. PGlite executes PostgreSQL policy tests without the pgcrypto extension or the complete Supabase Auth stack. It is not a replacement for the target-project gate.
- CI configuration was authored, not run on GitHub in this session.
- Real OTP delivery/callback, secure HTTPS cookies, two-account provider isolation, signed Stripe test webhooks/checkout and licensed weather integration still need staging evidence.
- No deployment, real emails, payment, operator invitations or external sign-offs occurred.
- Trail facts/exposure/seasons, coordinates and conditioning rules remain review-pending. No safety clearance is implied.
- Privacy/legal, rate limiting at the deployment gateway, monitoring delivery, backup/erasure rehearsal, operator pilot and production authorization remain blocked in `release-checklist.md`.
- Two third-party Python test-client deprecation warnings remain. Streamlit's existing HTML-component interface also reports a deprecation notice. These did not fail tests and the commercial UI uses Next.js.
