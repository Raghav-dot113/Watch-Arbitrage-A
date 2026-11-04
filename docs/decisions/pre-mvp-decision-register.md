# ChronoArb — Pre-MVP Implementation Decision Register

**Document type:** Architecture and product decision audit  
**Status:** Open / Pending Stakeholder Approvals  
**Date:** 2026-10-31  
**Target baseline:** ChronoArb MVP SRS v1.0, AI-Agent Engineering Playbook v1.0, Approved ADRs (0001–0009)  
**Authority:** AGENTS.md §1 & §4, Playbook §2.1 & §3.3  

---

## 1. Executive Summary

This decision register audits the current ChronoArb requirements, architecture documentation, code baseline, and execution plans to isolate all pending decisions required before MVP implementation proceeds.

Following the authority order defined in `AGENTS.md` §1 and the stop conditions in Playbook §5.3 / A.3, AI coding agents and engineering teams must not invent product data, assume legal approvals, or make silent architectural compromises. Where code has drifted ahead of formal sign-offs (e.g., hardcoding vendor-specific identifiers or creating database columns without S3 pointers), these discrepancies are cataloged below with the exact decision needed, affected workflow steps, and suggested owner.

---

## 2. Decision Register

### DEC-01: Initial Supported Watch References Universe (25 Canonical Models)

- **Authoritative Source:**
  - SRS Document Control: *Approvals Required Before Build* — Product Owner scope includes "watch-reference universe".
  - SRS §1.4: "The MVP supports approximately 25 high-liquidity modern watch references."
  - SRS §3.1: "25 canonical modern references; configuration supports expansion without schema changes."
  - SRS §3.2 (Launch Stages): Design-partner beta requires "15 references; Reference accuracy ≥97%"; Paid MVP requires "25 references".
  - SRS §4.3 (FR-CAT-001 through FR-CAT-004): Brands, references, variants, aliases, and attributes.
  - SRS §14.3: "Model Acceptance by Reference... Release evaluation shall report each supported reference separately."
  - SRS §15: Paid MVP Gate: "25 active supported references and three production-approved sources."
- **Current State in Code and Plans:**
  - Database schema (`alembic/versions/a40b5bfef9a2_001_identity_and_catalog.py`) defines `brands`, `references`, `aliases`, `watch_lists`, and `watch_list_entries` tables.
  - ORM models in `apps/api/apps/api/catalog/infrastructure/models.py` (`Brand`, `Reference`, `Alias`, etc.) and Pydantic response schemas in `apps/api/apps/api/catalog/api/schemas.py`.
  - Database contains **zero seed records**.
  - Test suites (`apps/api/tests/test_catalog.py`) use arbitrary illustrative strings (e.g., `Brand("Rolex")`, `Reference("310.30.42")`).
  - Web UI at `apps/web/app/(dashboard)/watches/page.tsx` is an empty placeholder.
  - Plans (`week-02-domain-plan.md`, `development-roadmap.md` Weeks 3–5) schedule 25 references, but no approved reference list exists in the repository.
- **Exact Decision Needed:**
  1. Product Owner approval of the exact list of 25 modern luxury watch references for MVP (and the 15-reference subset for beta), spanning high-liquidity models across target brands (e.g., Rolex, Patek Philippe, Audemars Piguet, Omega).
  2. For each canonical reference: brand slug, reference code, official model name, generation, case material, bezel, dial, bracelet, movement caliber, production status, and liquidity tier.
  3. Approved known aliases and punctuation/spacing permutations (e.g., "126610LN", "126610 LN", "126610-LN") for deterministic matching.
- **Affected Workflow Steps:**
  - Catalog seed migrations and test fixtures (`brands`, `references`, `aliases`).
  - Reference extraction regexes and tokenizers in `packages/domain-python/chronoarb/domain/normalization/`.
  - Valuation model comparable selection rules and adjustment matrices (`packages/domain-python/chronoarb/domain/valuation/`).
  - Organization default onboarding watch lists (`watch_lists`, `watch_list_entries`).
  - Reference-specific precision benchmarks (SRS §14.3 quality gates).
- **Suggested Owner:** Product Owner (with Luxury Watch Domain Expert).
- **Blocking Urgency:** High — blocks normalization and valuation implementation (Weeks 3–6).

---

### DEC-02: First Three Sources & Approved Access, Retention, and Display Terms

- **Authoritative Source:**
  - SRS Document Control: *Approvals Required Before Build* — Legal Counsel scope includes "Source terms, permitted collection methods, privacy, consumer disclosures".
  - SRS §1.4, §3.1, §3.2, §15: Minimum three dependable, legally reviewed data integrations.
  - SRS §1.5: Non-goals: "No unsupported circumvention of access controls, CAPTCHAs, authentication walls or contractual restrictions. No public consumer marketplace and no seller listings hosted by ChronoArb."
  - SRS §4.4 (FR-SRC-001, FR-SRC-002, FR-SRC-003, FR-SRC-006, FR-SRC-007):
    - FR-SRC-001: "A source cannot run in production until status is Approved."
    - FR-SRC-002: "The preferred access order shall be official API, commercial/affiliate feed, partner feed, permissioned crawl, then legally reviewed public extraction. Source record documents the selected access mode and approval evidence."
  - SRS §5.3: Raw public-source evidence retention baseline (90 days hot; archive up to 12 months if permitted; shorter retention overrides apply when source terms require).
  - SRS §6.3: "eBay Browse API or equivalent official endpoint: Search and listing metadata where approved. License compliance, attribution/usage review and API quotas."
  - SRS §11.2: Scraping and data-source compliance workflow and takedown process.
  - Playbook §14.3: "Implement only the approved access mode; technical ability is not permission."
- **Current State in Code and Plans:**
  - `sources` table exists in Migration 001 (`source_key`, `display_name`, `adapter_version`, `access_mode`, `rate_policy`, `approval_ref`, `is_enabled`), with zero seeded sources.
  - `packages/source-adapters/` contains only an empty `__init__.py`; no adapter implementations exist.
  - `packages/domain-python/chronoarb/domain/source_adapters/protocol.py` defines the abstract `SourceAdapter` protocol.
  - eBay Browse API is referenced as an example in SRS §6.3, and Chrono24 / dealer networks are casually mentioned in onboarding text, but **no executed contract, legal memorandum, or formal approval reference (`approval_ref`) exists for any source**.
- **Exact Decision Needed:**
  1. Selection and formal sign-off on the three initial production sources (e.g., eBay Browse API, Chrono24, WatchBox, Reddit/r/Watchexchange, or designated dealer feeds).
  2. For each source, formal approval of:
     - **Access Mode:** Official API, commercial partner feed, or legally reviewed public extraction.
     - **Rate & Concurrency Limits:** Requests per second/minute, burst allowances, daily quota, schedule windows.
     - **Data Retention Constraints:** Permitted retention window for raw payloads (standard 90-day hot retention vs source-mandated shorter retention or deletion requirements upon listing removal).
     - **Customer Display Rights:** Permitted display of external URLs, raw text descriptions, listing photos/thumbnails, and seller identifiers (including required attribution or affiliate disclosures).
     - **Legal Approval Identifier:** Explicit `approval_ref` string linking to the legal review document.
- **Affected Workflow Steps:**
  - Adapter implementation in `packages/source-adapters/chronoarb/adapters/`.
  - Ingestion worker scheduling, rate-limiting, and error classification (`apps/worker/workers/discovery/`, `fetch/`).
  - Raw evidence S3 storage and lifecycle deletion policies.
  - Normalization attribute extraction policies.
  - Web and mobile opportunity detail views (rendering listing links, images, and attribution).
- **Suggested Owner:** Legal Counsel (lead) and Product Owner / Engineering Lead.
- **Blocking Urgency:** Blocker — No adapter code can be implemented or tested against live/recorded feeds without approved terms and access mode (Playbook Rule 17, AGENTS.md §2).

---

### DEC-03: Identity Provider (IdP) Confirmation & OIDC Schema Alignment

- **Authoritative Source:**
  - SRS Document Control: Security Owner (threat model, IAM) & Engineering Lead (architecture, stack).
  - SRS §4.1 (FR-AUTH-001 through FR-AUTH-007): OIDC Authorization Code + PKCE, email/password + social/enterprise provider, immutable internal user ID mapping.
  - SRS §5.1 & Figure 1: `users` entity schema defines `id PK, oidc_subject, email, name`.
  - SRS §7.2: Baseline: "Amazon Cognito or equivalent standards-compliant OIDC provider".
  - `docs/project-analysis.md` §3.3: Marked as `[NEEDS APPROVAL] Amazon Cognito vs alternative OIDC provider`.
  - `docs/adr/0006-authentication-flow.md`: Web authentication flow assuming Cognito hosted UI and tokens.
  - `docs/architecture/architecture-review.md` Risk 3: Staging and local testing hurdles with Cognito.
- **Current State in Code and Plans:**
  - Migration 001 (`alembic/versions/a40b5bfef9a2_001_identity_and_catalog.py`) and ORM model `apps/api/apps/api/identity/infrastructure/models.py` define `cognito_sub TEXT UNIQUE NOT NULL` on `users`.
  - `UserRepository` implements `get_by_cognito_sub(sub)`.
  - FastAPI auth dependency in `apps/api/apps/api/deps.py` is an unauthenticated stub.
  - Next.js auth routes (`apps/web/app/api/auth/*`) are not implemented.
  - Infrastructure repository lacks Terraform for Cognito User Pool.
  - **Discrepancy:** The database schema and repository hardcode `cognito_sub`, violating the vendor-neutral `oidc_subject` specified in SRS §5.1 / Figure 1 before a formal IdP selection was finalized.
- **Exact Decision Needed:**
  1. Security Owner & Engineering Lead formal sign-off confirming Amazon Cognito as the designated IdP (or selecting an alternative such as Auth0, Clerk, or Keycloak).
  2. If Amazon Cognito is confirmed:
     - User pool parameters: self-registration policy, mandatory email verification (FR-AUTH-003), allowed social identity providers (FR-AUTH-002: Google / Apple), and MFA configuration (FR-AUTH-005).
     - Local development and test strategy: define how JWT verification is tested locally and in CI without an external AWS dependency (e.g. local JWKS stub generator vs hosted test user pool).
  3. Database Schema Alignment: Determine whether to issue a migration renaming `cognito_sub` to vendor-neutral `oidc_subject` to adhere to SRS Figure 1 and decouple the domain model from third-party vendor naming.
- **Affected Workflow Steps:**
  - Backend JWT verification middleware and dependency injection (`apps/api/apps/api/deps.py`).
  - Next.js route handlers (`apps/web/app/api/auth/[callback|session|refresh|logout]`).
  - Mobile authentication coordinator (Flutter OIDC + `flutter_secure_storage`).
  - Terraform user pool and client provisioning (`infrastructure/terraform/cognito`).
  - User onboarding and team invitation acceptance flows.
- **Suggested Owner:** Security Owner & Engineering Lead.
- **Blocking Urgency:** Blocker for Phase 4 / Web Auth integration (Week 3–5).

---

### DEC-04: Raw Snapshot Storage Architecture (JSONB vs S3 Object Storage)

- **Authoritative Source:**
  - SRS §5.1 & Figure 1: `listing_snapshots` specifies `raw_uri` pointing to object storage.
  - SRS §5.3: Raw public-source evidence retention (90 days hot; archive up to 12 months).
  - SRS §7.2: "Object storage: Amazon S3 with KMS encryption and lifecycle rules. Raw evidence, exports and immutable snapshots."
  - `docs/architecture/architecture-review.md` NOTE-01: Ambiguity in `database-design.md` line 111 (`raw_payload JSONB (or S3 key reference)`).
- **Current State in Code and Plans:**
  - Migration 002 (`alembic/versions/12e1f9e711d2_002_listings_and_valuation.py`) created `raw_snapshots` table with `raw_payload postgresql.JSONB()`, but **no `s3_key` or `raw_uri` column**.
  - `apps/api/apps/api/listings/infrastructure/models.py` has not yet implemented the `RawSnapshot` ORM model (scheduled for Phase 3).
  - Storing raw multi-megabyte HTML crawl pages directly in PostgreSQL JSONB causes massive database bloat, degrades VACUUM/PITR performance, and contradicts SRS Figure 1.
- **Exact Decision Needed:**
  - Decide the storage tiering architecture for raw evidence:
    - **Option A (Threshold Hybrid):** Payloads < 64 KB stored inline in `raw_payload` (JSONB); payloads ≥ 64 KB or non-JSON payloads (raw HTML, XML) stored in S3, storing `s3_uri` in database.
    - **Option B (Pure Object Storage per SRS Figure 1):** All raw fetch payloads stored in S3 with KMS encryption; database stores only `s3_uri`, `checksum`, fetch metadata, and parsed output.
  - If S3 is adopted (recommended), approve an Alembic migration to add `s3_uri TEXT` to `raw_snapshots` before Phase 3 ORM models are finalized.
- **Affected Workflow Steps:**
  - Phase 3 listings ORM model and repository (`RawSnapshot`).
  - Fetch worker pipeline (`apps/worker/workers/fetch/`).
  - S3 bucket creation, KMS encryption policy, and retention lifecycle rules.
- **Suggested Owner:** Engineering Lead & Data Lead.
- **Blocking Urgency:** Blocker for Phase 3 (Day 3 Backend Listing Models).

---

### DEC-05: Telegram Bot Integration Pattern (Long-Polling Worker vs Public Webhook)

- **Decision:** Long-polling worker using Telegram `getUpdates`; do not expose an
  inbound Telegram webhook in FastAPI. Approved for B13 on 2026-11-04.
- **Consequences:** Telegram linking tokens are short-lived and stored hashed.
  Worker-side link completion persists the verified chat ID encrypted. Public
  webhook ingress and Telegram secret-token validation are not used by this flow.
- **Authoritative Source:**
  - SRS §4.10 (FR-ALT-002, FR-ALT-003): Real-time alerts and user-initiated linking.
  - SRS §6.3: "Telegram Bot API: Instant text alerts and linking flow. HTTPS API, secret token, chat ownership validation and idempotency."
  - SRS §11.1 & §14.1: Webhook security controls (signature verification, replay protection).
  - `docs/architecture/architecture-review.md` NOTE-05: Identified missing webhook endpoint vs polling decision; recommended ADR-0005.
- **Current State in Code and Plans:**
  - B13 implements token generation at `POST /api/v1/settings/integrations/telegram`
    and the service operation used to complete links from a polling worker.
  - The polling worker and notification delivery are not implemented yet.
- **Decision Needed:** None for B13. Implement the approved polling worker with the
  notification workstream; do not add a public Telegram webhook without revisiting
  this decision.
- **Affected Workflow Steps:**
  - Backend Telegram integration routes vs worker processes.
  - WAF/ALB ingress routing rules and security review.
  - Notification module linking flow verification.
- **Suggested Owner:** Backend Lead & Security Owner.
- **Blocking Urgency:** Medium — blocks Week 6–8 notification workstream.

---

### DEC-06: Ingestion Scheduling Cadence vs NFR-PERF-004

- **Authoritative Source:**
  - SRS §4.4 FR-SRC-004: "The scheduler shall enqueue idempotent collection jobs by source, watch scope and time window."
  - SRS §12.1 NFR-PERF-004: "Time-to-detect target shall be <3 minutes for push/API feeds where source capability allows and <10 minutes p95 across MVP high-priority sources."
  - `docs/project-analysis.md` §3.3: Marked as `[NEEDS APPROVAL] Weekly or daily ingestion schedules per source (Product/Operations)`.
- **Current State in Code and Plans:**
  - `docs/project-analysis.md` §3.3 speculates on "weekly or daily ingestion schedules", which is a direct violation of SRS NFR-PERF-004 (sub-10-minute detection).
  - EventBridge scheduler schedules are not yet defined.
- **Exact Decision Needed:**
  - Reconcile documentation to explicitly reject weekly/daily collection for active inventory.
  - Approve tiered schedule cadence:
    - Tier 1 (High-liquidity active listings): 3–5 minute intervals via EventBridge cron.
    - Tier 2 (Catalog price comps / historical observations): Daily or weekly refresh.
- **Affected Workflow Steps:**
  - EventBridge scheduler Terraform definitions.
  - Discovery worker batching and rate limiting (`sources.rate_policy`).
  - Worker infrastructure sizing and operating cost projections.
- **Suggested Owner:** Operations Lead & Data Lead.
- **Blocking Urgency:** Medium — blocks Week 6 pipeline scheduler configuration.

---

### DEC-07: Mobile App Store Billing Policy & Reader-App Architecture

- **Authoritative Source:**
  - SRS §4.13 FR-BIL-006: "The mobile MVP shall support sign-in to an existing entitlement. Any in-app purchase or external purchase call-to-action shall be implemented only after current Apple and Google policy review. Must: App-store submission checklist records the approved billing approach for each storefront and region."
  - SRS §11.1, §15: App store submission review and legal sign-off.
  - Playbook §9.6, §17.4: Mobile store submission policy checks.
- **Current State in Code and Plans:**
  - Web application implements Stripe Billing (checkout session, portal, webhooks).
  - Mobile application architecture (`docs/architecture/frontend-design.md`, `apps/mobile`) plans account settings and login, but the in-app monetization model is not formally defined.
- **Exact Decision Needed:**
  - Legal & Product decision on mobile billing model:
    - **Option A (Reader/Companion App):** Users cannot subscribe or purchase within mobile apps; no buttons, external links, or CTAs for billing. Mobile app is purely a companion for active subscribers who registered on web.
    - **Option B (Multiplatform In-App Purchase):** Integrate Apple StoreKit and Google Play Billing, requiring unified cross-platform entitlement reconciliation in the backend `billing` module.
- **Affected Workflow Steps:**
  - Mobile settings and account presentation UI (`apps/mobile/lib/features/settings/`).
  - Backend entitlement verification endpoints.
  - App Store / Google Play submission review compliance documentation.
- **Suggested Owner:** Product Owner & Legal Counsel.
- **Blocking Urgency:** High — required before mobile billing and store submission work (Weeks 11–13).

---

### DEC-08: Opportunity Feed Cursor Pagination Sorting Anchor

- **Authoritative Source:**
  - SRS §6.2: "Pagination uses opaque cursor tokens rather than page numbers for changing feeds."
  - Playbook §13.3: "Use opaque cursor pagination for mutable feeds."
  - `docs/architecture/architecture-review.md` MINOR-05: Highlighted pagination instability when sorting by dynamic `score`.
- **Current State in Code and Plans:**
  - `api-design.md` and `database-design.md` specify cursor pagination for `/api/v1/opportunities`.
  - The opportunity feed sorts by `score DESC`, but opportunity score dynamically recalculates on price changes and fresh comps, causing items to shift positions between pagination requests.
- **Exact Decision Needed:**
  - Approve the deterministic cursor anchoring policy:
    - Encode cursor as base64 tuple of immutable or monotonically ordered fields: `(published_at, id)` or `(score_at_generation, id)` rather than dynamic live score, OR
    - Use feed snapshot caching in Redis with TTL for paginated dealer browsing sessions.
- **Affected Workflow Steps:**
  - `OpportunityRepository` cursor query implementation in Phase 3.
  - Opportunity API router schemas (`apps/api/apps/api/opportunities/api/`).
  - Web and mobile TanStack Query / Riverpod cursor consumption.
- **Suggested Owner:** Backend Lead.
- **Blocking Urgency:** Medium — affects Phase 3 `OpportunityRepository` and Week 9 Web feed.

---

### DEC-09: Local Emulation and Mock Strategy for Cloud Infrastructure (Cognito, SQS, S3, Redis)

- **Authoritative Source:**
  - SRS §13.1: Local environment data policy ("Synthetic/test data only; no production secrets").
  - Playbook §15.2: "Prefer deterministic fixtures and fake clocks/IDs over sleeps and live external services."
  - `docs/adr/0009-local-database-development-strategy.md`: Resolved SQLite vs asyncpg for local development, but external cloud services remain unspecified.
  - `docs/architecture/architecture-review.md` NOTE-04 & Risk 3: Lack of unified local environment specification.
- **Current State in Code and Plans:**
  - Local database runs SQLite for unit tests, Docker PostgreSQL for migration verification.
  - No Docker Compose or mock configuration exists for SQS queues, S3 buckets, or Cognito authentication.
  - Developers currently lack a runnable local stack for end-to-end ingest-to-alert testing.
- **Exact Decision Needed:**
  - Define local tooling baseline:
    - LocalStack (community edition) vs dedicated lightweight mocks (ElasticMQ for SQS, MinIO for S3, local JWKS mock server for Cognito).
    - Provide standardized `docker-compose.local.yml` and environment variable templates.
- **Affected Workflow Steps:**
  - Developer onboarding and local verification workflows (`make bootstrap`, local dev).
  - CI test runners for worker and API integration tests.
- **Suggested Owner:** DevOps Lead & Backend Lead.
- **Blocking Urgency:** High — required for Week 3+ worker and auth development.

---

## 3. Decision Matrix Summary

| ID | Decision Topic | Authoritative Source | Current State in Code / Plans | Exact Decision Needed | Suggested Owner | Blocker Urgency |
|---|---|---|---|---|---|---|
| **DEC-01** | Initial 25 Supported Watch References | SRS §1.4, §3.1, §4.3, §14.3, §15 | Schema created in 001; zero seed data; mock values in tests | Approve specific list of 25 canonical references, attributes, and aliases | Product Owner / Domain Expert | High (Weeks 3–6) |
| **DEC-02** | First 3 Sources & Access/Retention Terms | SRS §1.4, §1.5, §4.4, §5.3, §11.2, Playbook §14.3 | `sources` table exists; zero adapters implemented; no `approval_ref` records | Select 3 sources; approve access mode, rate policy, display rights, and retention limits | Legal Counsel & Product Owner | Blocker (Week 3+) |
| **DEC-03** | Identity Provider (IdP) Confirmation & Schema | SRS §4.1, §5.1, §7.2, ADR-0006 | `users.cognito_sub` hardcoded in DB/ORM; vendor-neutral `oidc_subject` in SRS; unauthenticated API stub | Confirm Cognito vs alternative; determine if renaming `cognito_sub` to `oidc_subject`; approve user pool config & local test mock | Security Owner & Engineering Lead | Blocker (Week 3–5) |
| **DEC-04** | Raw Snapshot Storage (JSONB vs S3) | SRS Fig. 1, §5.3, §7.2, Arch Review NOTE-01 | Migration 002 has `raw_payload JSONB` but NO S3 URI column; model not implemented | Decide S3 vs JSONB storage tiering; approve migration to add `s3_uri` to `raw_snapshots` | Engineering Lead & Data Lead | Blocker (Phase 3 Backend) |
| **DEC-05** | Telegram Bot Integration Pattern | SRS §4.10, §6.3, §11.1, Arch Review NOTE-05 | Long polling approved; B13 linking API/service implemented; worker remains follow-up | None for B13; implement polling worker with notifications | Backend Lead & Security Owner | Resolved for B13; worker follow-up |
| **DEC-06** | Ingestion Scheduling vs NFR-PERF-004 | SRS §4.4, §12.1 NFR-PERF-004 | `project-analysis.md` suggests daily/weekly; conflicts with <10m detection NFR | Formalize 3–5 min polling for high-priority references vs daily comps | Operations Lead & Data Lead | Medium (Weeks 3–6) |
| **DEC-07** | Mobile App Store Billing Policy | SRS §4.13, §11.1, §15, Playbook §17.4 | Web Stripe implemented; mobile billing UX undefined | Decide Companion/Reader app model (no IAP) vs native Apple/Google IAP | Product Owner & Legal Counsel | High (Weeks 11–13) |
| **DEC-08** | Cursor Pagination Dynamic Score Anchor | SRS §6.2, Playbook §13.3, Arch Review MINOR-05 | Pagination specified; sorting on mutable score causes drift | Approve deterministic cursor tuple `(published_at, id)` or feed snapshot caching | Backend Lead | Medium (Phase 3 / Week 9) |
| **DEC-09** | Local Emulation Strategy for Cloud Dependencies | SRS §13.1, Playbook §15.2, Arch Review NOTE-04 | SQLite/Postgres resolved; no mock stack for SQS, S3, Cognito | Select LocalStack vs lightweight mocks; supply compose definition | DevOps Lead & Backend Lead | High (Week 3+) |
