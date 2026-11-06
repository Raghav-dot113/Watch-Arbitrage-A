# ChronoArb Backend Progress

## Completed

- [x] B-BASE / Phase 0: Baseline verification recorded. API and domain suites must be run separately because both expose a top-level `tests` package.
- [x] B17 / Phase 1: Deterministic OpenAPI export and freshness checks, Makefile gates, and route metadata added.
- [x] B18 / Phase 2: Tenant-scoped organization listing and local/test HS256 authentication added.
- [x] Phase 3 (B19): Pipeline ORM models, repositories, Decimal/NUMERIC fields, cursor pagination, and idempotent opportunity views added.
- [x] B19 production-auth hardening (part of Phase 3 continuation): Added production-only RS256/JWKS verification with issuer, audience, expiry, issued-at, key-id, and JWKS cache checks. Local/test HS256 remains development-only.

## Implemented and verified evidence

- API suite: **84 passed** (`python -m pytest apps/api/tests -q`).
- Domain suite: **37 passed** (`python -m pytest packages/domain-python/tests -q`).
- Worker suite: **4 passed** (`python -m pytest apps/worker/tests -q`).
- Ruff lint: all checked application, worker, domain, adapter, and migration paths pass.
- OpenAPI: `docs/api/openapi.yaml` is exported and its freshness check passes.
- Identity isolation coverage includes empty, single, and multiple memberships plus invalid identities and tenant context.
- Stripe webhook signature validation now has PostgreSQL-backed replay protection; the forward migration is `f3c8d2a1b6e4_005_stripe_webhook_replay.py`.

## Phase implementation status

- [x] Phase 0: Baseline and separate API/domain/worker gates established.
- [x] Phase 1: Deterministic OpenAPI export, freshness test, and Makefile targets.
- [x] Phase 2: Organization membership context, roles, and authenticated tenant isolation.
- [x] Phase 3: Listing, valuation, duplicate, and opportunity foundations plus cursor and view behavior.
- [~] Phase 4: Fixture source adapter and registry exist; approved live adapters, admin controls, and immutable evidence workflows remain future work.
- [~] Phase 5: Normalization, duplicate, and replay-envelope foundations exist; full durable stage lineage requires workers and PostgreSQL integration.
- [~] Phase 6: Decimal valuation foundations and opportunity models exist; end-to-end valuation, FX, cost assumptions, and expiry scheduling remain future work.
- [~] Phase 7: Bounded job envelopes and stage dispatch exist; durable queue publication, DLQ operations, and graceful shutdown remain future work.
- [~] Phase 8: Operations audit/feature/flag models and tenant repositories exist; complete admin job/listing/source routes require further implementation.
- [~] Phase 9: Alert and feedback foundations exist; notification delivery adapters, outbox publication, and alert matching remain future work.
- [~] Phase 10: Signature validation and durable Stripe webhook-event replay protection exist; full subscription state reconciliation remains future work.
- [~] Phase 11: Baseline tenant tests and lint/OpenAPI gates exist; full security, observability, and PostgreSQL query-plan sweep remains outstanding.
- [~] Phase 12: Architecture and runbooks exist partially; final release acceptance and migration staging evidence remain outstanding.

## Operational blockers

- Docker/PostgreSQL migration rehearsal remains outstanding in this environment; Alembic parity is not equivalent to a PostgreSQL staging run.
- The combined API/domain pytest command is unsupported due to package-name collision; run `pytest apps/api/tests` and `pytest packages/domain-python/tests` separately.
- The Windows environment does not provide the `make` executable, so Makefile targets require GNU Make on PATH (the equivalent OpenAPI Python freshness test passes).
- Production Cognito settings must be supplied through `CHRONOARB_AUTH_MODE=production`, `CHRONOARB_COGNITO_JWKS_URL`, `CHRONOARB_COGNITO_ISSUER`, and `CHRONOARB_COGNITO_AUDIENCE`.
