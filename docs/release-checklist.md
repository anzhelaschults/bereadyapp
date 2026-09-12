# Commercial release checklist

This is a launch gate, not evidence that a launch occurred. An unchecked owner or signature blocks traveler-facing release. Do not replace it with an agent-generated name.

## Named approvals

| Gate | Owner | Evidence | Status |
|---|---|---|---|
| Trail challenges, rewards, exposure and seasons | Unassigned | Per-trail source review and signed record | BLOCKED |
| Representative forecast coordinates and elevation | Unassigned | Route-map check, summit/valley limitations | BLOCKED |
| Plan progression and missed-week behavior | Unassigned conditioning reviewer | Review of core.py, including insufficient-runway plans | BLOCKED |
| Meaning of progress and fitness disclaimer | Unassigned product/conditioning reviewers | No physiological claims from logged sessions | BLOCKED |
| Privacy/legal and data processor contracts | Unassigned | Retention, lawful basis, deletion and transfer review | BLOCKED |
| Weather API commercial license | Unassigned | Valid subscription or approved license | BLOCKED |
| Billing price and entitlement design | Unassigned | Demand validation, approved Stripe test mode configuration | BLOCKED |
| Staging auth, RLS and hosted checkout | Unassigned engineer | Real provider end-to-end evidence | BLOCKED |
| Pilot with 2 or 3 operators | Unassigned pilot lead | See pilot.md | BLOCKED |
| Production rollout | Unassigned release owner | Staging sign-off and rollback rehearsal | BLOCKED |

## Engineering gates
- [ ] `uv sync --frozen --extra test`, `uv run pytest` pass.
- [ ] `uv run python -m beready.catalog --check` passes.
- [ ] `cd web && npm ci && npm run lint && npm run typecheck && npm test && npm run build` pass.
- [ ] `E2E_PRODUCTION=true npm run e2e` passes after a production build, with real Python service and screenshots. Account/browser transports are stubbed in this suite and do not count as real provider sign-off.
- [ ] RLS tests execute against the target Supabase schema, not just SQL text checks.
- [ ] Two distinct staging accounts cannot read/write/delete each other's plans or companies.
- [ ] Anonymous plan preview works, actual email login saves it and completion survives reload.
- [ ] Account provider down does not affect verdicts and discovery.
- [ ] Forecast down and out-of-horizon date display typical notes, not stale live claims.
- [ ] Keyboard, mobile and WCAG AA checks include all saved/account states.
- [ ] `npm audit --audit-level=high` reviewed, Python dependency audit reviewed.
- [ ] HTTPS and security headers present, proxy cache never stores auth cookies or personal data.
- [ ] Configure gateway body/time/concurrency limits and per-IP public API limits. Provider auth email quotas alone are not enough.
- [ ] Production signing keys and webhook secret configured only in secret storage.
- [ ] No service-role key used in browser, owner reads, logs, deletes or company requests. Canonical plan inserts alone use a trusted server writer with an owner ID taken from verified authentication.
- [ ] OTP mail sender, callback URL and allowlist verified in the target project.
- [ ] Logs redact bodies, query strings, cookies and payment/session secrets.
- [ ] Monitor availability, p95 latency, policy failures and conditions fallback rate. Exercise an alert.
- [ ] Privacy page finalized, account erasure procedure exercised including provider records and backups.

## Rollout and rollback
1. Deploy to private staging. Keep BILLING_ENABLED and CONDITIONS_ENABLED false.
2. Run all gates. Invite pilot participants manually only after consent. Do not send invites from test automation.
3. Enable licensed conditions for the team. Verify representative-point labels and unavailable fallback.
4. Enable Stripe test-mode pilot only after pricing approval. Test duplicate/out-of-order webhooks and cancellation. Do not use live cards in automated tests.
5. Release to a limited invited cohort with a named monitor. Review one day of errors before broadening access.
6. Roll back on any ownership violation, incorrect safety claim, unexplained 5xx rate above 1% for 5 minutes, or p95 plan latency above 2 seconds for 5 minutes. Thresholds are provisional pending a staging baseline.
7. Disable billing/conditions flags immediately if those providers cause the incident. Redeploy the previous app and API together for policy/schema regressions. Keep saved data. Do not drop production tables to roll back code.
8. Retain backup and migration version. Destructive schema rollback needs separate authorization and verified restore.

Flag owner: unassigned release owner. Review flags during each pilot review. Remove obsolete rollout flags within two weeks of full rollout, but keep operational provider kill switches.
