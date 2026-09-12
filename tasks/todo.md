# Implementation checklist

Implemented and verified locally. This is not a production release. See [verification evidence](../docs/verification.md) for exact commands and test boundaries.

- [x] Python scorer, trails, catalog and parity tests
- [x] Streamlit shares Python-generated assessments, with no model bypass
- [x] Next.js quick check and runway
- [x] Adaptive motivation and static conditions
- [x] Discovery filters and comparison
- [x] Deterministic dated plan and safe missed-week adaptation
- [x] Free plan UI and completion-based progress
- [x] Supabase auth, saved plans, logging and owner RLS implementation
- [x] Conditions API and explicit forecast/closure limitations
- [x] Deterministic natural-language discovery and demand events
- [x] Company workspace and gated pilot billing implementation
- [x] CI, documentation, launch checklist and screenshots
- [x] Local validation and adversarial review, including corrective regression tests

## External and human gates, not completed
- [ ] Trail-content, season, exposure and representative-coordinate approval
- [ ] Conditioning professional approval
- [ ] Privacy/legal and commercial weather licensing review
- [ ] Target Supabase pgTAP and real staging auth/storage/payment integration
- [ ] HTTPS edge, rate limits, monitoring delivery, backup and erasure rehearsal
- [ ] Operator pilot and production release authorization

Accounts require configured Supabase and a trusted server-only canonical writer. Billing and live weather remain disabled by default. No deployment, email delivery, charge or external approval was performed.
