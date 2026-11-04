# PROGRESS (update after every task: tick the box, add one line of notes, commit)
Rule: do the first unticked task whose dependencies are ticked. One task per chat session.

## Backend
- [x] B01 toolchain + baseline (no code) — Python 3.13.17 venv and `.env.example` set up; pytest: 57 collected, 2 collection errors, 0 run; Ruff: 51 errors; mypy: 1 duplicate-module error; import-linter: config not readable; web typecheck and build passed.
- [x] B02 listings ORM models — added migration-matched ORM tables, startup registration, and SQLite FK/unique/chain coverage; 7 focused tests and all 64 API tests pass.
- [x] B03 valuation, duplicates, opportunities ORM models — added five migration-matched tables, startup registration, and parity/FK/tenant/unique tests; 9 focused tests and all 73 API tests pass.
- [x] B04 alerts, feedback, billing, operations ORM models — added eight migration-matched tables, startup registration, column parity and global idempotency tests; 10 focused tests and all 83 API tests pass.
- [x] B05 tenant repositories + keyset pagination — added checksum-validated cursors, latest-version joined opportunity feed, scoped feature repositories, and isolation/paging/query-count coverage; focused tests 26 passed and API suite 94 passed.
- [x] B06 cost model (domain) + property tests — added versioned Decimal/Money cost assumptions, acquisition/resale breakdowns, profit/ROI calculations, and Hypothesis financial-identity tests; domain suite: 42 passed.
- [x] B07 settings, dev auth, auth context, RBAC — added local-only HS256 dev tokens, verified identity/tenant resolution from membership records, server-side role permissions and platform-ops allowlisting; API suite: 112 passed.
- [ ] B08 error envelope, CORS, idempotency helper, audit helper
- [ ] B09 identity + catalog routes
- [ ] B10 opportunities feed + detail routes
- [ ] B11 feedback, history, trade outcome + state machine
- [ ] B12 alerts + activity routes
- [ ] B13 settings, billing, admin routes
- [ ] B14 seed part 1 (orgs, users, catalog, sources)
- [ ] B15 seed part 2 (listings -> valuations -> opportunities)
- [ ] B16 seed part 3 (alerts, feedback, outcomes, billing, flags, audit)
- [ ] B17 OpenAPI export + freshness test + Makefile targets

## Frontend
- [ ] F01 deps, vitest, api-client package
- [ ] F02 auth route handlers + route protection
- [ ] F03 AuthProvider + login page
- [ ] F04 api layer, query hooks, formatters
- [ ] F05 shared UI states/components
- [ ] F06 shell: user menu, move design preview
- [ ] F07 opportunities feed page
- [ ] F08 opportunity detail page
- [ ] F09 decision actions + outcome form
- [ ] F10 watches pages
- [ ] F11 alerts page
- [ ] F12 activity page
- [ ] F13 settings (organization, integrations, billing)
- [ ] F14 onboarding
- [ ] F15 admin console

## Quality
- [ ] Q01 Playwright journeys
- [ ] Q02 accessibility (axe) pass
- [ ] Q03 security gates
- [ ] Q04 docs, README, acceptance report, local run
- [ ] Q05 (optional) deployment decision + docker compose
