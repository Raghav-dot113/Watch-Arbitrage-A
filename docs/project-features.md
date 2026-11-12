# ChronoArb - Implemented Feature Overview

This document summarizes features present in the repository. It distinguishes
working application flows from local-development support and architectural
foundations; it is not a claim that every feature is deployed or production
ready. See [`PROGRESS.md`](../PROGRESS.md) for the phase-by-phase implementation
record.

## Product

ChronoArb is a dealer-acquisition intelligence application for researching
luxury-watch listings and recording opportunity decisions. It is not a
marketplace, custody service, automated purchasing system, or watch
authentication service.

## Web application

The Next.js application includes a responsive dealer console with a shared
navigation shell, a dark visual theme, reusable data and status components,
and loading, empty, and error states.

- **Sign-in and sessions:** Login, logout, protected application routes, and
  signed session cookies. The current login flow obtains a local development
  API token; production OIDC/Cognito sign-in is not established by this flow.
- **Organization onboarding:** Create an organization and configure its
  default currency and timezone.
- **Opportunities:** View and search the opportunity feed, open an opportunity
  detail page, review valuation and confidence information, record contacted,
  dismissed, or purchased decisions, and submit realized trade outcomes.
- **Watch lists:** Create, edit, and delete lists of catalog references.
- **Alerts:** Manage alert rules, inspect delivery history, and request a test
  notification.
- **Activity and outcomes:** Review decision activity and recorded trade
  outcomes.
- **Organization settings and integrations:** Configure organization
  assumptions; view subscription status and initiate or cancel PayPal
  subscriptions; link or unlink Telegram; and register or remove push-device
  records.
- **Operations console:** Review source controls, feature flags, audit events,
  unmatched listings, and duplicate groups. The API also exposes job and
  dead-letter queue (DLQ) operations.
- **Watch search:** Search the Channel3 catalog and view returned product
  details, images, and retailer offers, including a link to an offer. This is
  an on-demand catalog search, defaulting to pre-owned offers with optional new
  or all-condition results and an in-stock-only filter; it is not an ingestion
  feed. The visible “Watch” action is not currently connected to watch-list
  persistence.

The web data layer uses typed API functions and TanStack Query hooks. Shared
design tokens and UI primitives are provided in `packages/design-tokens` and
`apps/web/components`.

## API and backend

The FastAPI application exposes versioned, organization-aware APIs for the
implemented web flows:

- **Identity and organizations:** Local-development token issuance, current
  user and membership context, and organization creation and management.
- **Catalog:** Brand and reference search/detail, reference aliases and
  attributes, watch-list lifecycle, and Channel3 search.
- **Opportunities:** A tenant-scoped, cursor-paginated feed with sorting and
  filters, plus tenant-scoped detail and valuation/listing context.
- **Feedback:** Opportunity decisions, decision history, and realized trade
  outcomes, with state-transition, audit, and idempotency support.
- **Alerts and activity:** Alert-rule lifecycle, idempotent test-notification
  requests, delivery history, team activity, and outcome reads.
- **Settings and integrations:** Organization defaults, Telegram linking, and
  push-device registration.
- **Billing:** PayPal subscription status, checkout and cancellation
  operations, and webhook verification with duplicate-event protection.
- **Operations:** Source controls, feature flags, audit reads, unmatched and
  duplicate review, job replay, and DLQ review/replay/discard operations.
- **Service support:** Health/readiness endpoints, trace IDs, consistent API
  response/error handling, and an exported OpenAPI contract.

The API uses async SQLAlchemy persistence, tenant-scoped access patterns,
server-side role checks, idempotency records, and audit helpers. Local
development supports guarded SQLite schema initialization and repeatable demo
data seeding; PostgreSQL migrations are also present.

## Shared domain and worker foundations

- **Financial domain:** Currency-aware `Money` values and `Decimal`-based,
  versioned acquisition/resale cost assumptions, cost breakdowns, expected
  net profit, and ROI calculations.
- **Listing domain:** Normalization and duplicate-candidate domain logic,
  typed source-adapter contracts, and namespaced identifiers.
- **Worker framework:** Traceable job envelopes, bounded retry counters,
  deterministic idempotency keys, and stage-to-handler dispatch.
- **Source adapter package:** A fixture adapter for offline/test data and an
  adapter registry.
- **Developer tooling:** API OpenAPI export/check commands, API setup and
  seeding instructions, and an APIMatic documentation/SDK-generation
  workflow.

## Scope and implementation limits

- No Flutter mobile application is currently present in the repository.
- A production source-ingestion pipeline is not complete. The worker currently
  provides dispatch foundations, and the fixture adapter is for offline/test
  data. Channel3 is used for explicit search requests, not background listing
  ingestion.
- Domain valuation and cost-calculation code and persistence models exist, but
  this overview does not imply a complete automated, continuously refreshed
  comparable-pricing pipeline.
- Production identity-provider configuration and deployment are separate from
  the local development login and setup flows described above.
- The project does not automate purchases, guarantee listing availability,
  authenticity, or profit, or execute dealer transactions.
- The repository's quality backlog still lists end-to-end journeys,
  accessibility, security, and release/documentation work as pending in
  [`PROGRESS.md`](../PROGRESS.md).

For detailed contracts and architecture, see
[`docs/architecture/api-design.md`](architecture/api-design.md),
[`docs/architecture/system-design.md`](architecture/system-design.md), and
[`docs/api/APIMATIC.md`](api/APIMATIC.md).
