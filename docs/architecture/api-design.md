# ChronoArb — API Design

**Document type:** REST API contract and design
**Source:** ChronoArb_MVP_SRS_v1.0 §10, AI-Agent Engineering Playbook §11, §13
**Date:** 2026-08-03

---

## 1. API Conventions

| Convention | Rule |
|-----------|------|
| URL prefix | `/api/v1/` |
| Case style | `snake_case` for all JSON keys |
| Timestamps | RFC 3339 UTC (`2026-08-02T16:42:19Z`) |
| Money | String representation, e.g. `"11150.00"` with explicit `currency` field (ISO 4217) |
| Pagination | Opaque cursor-based for mutable feeds; `next_cursor` in response |
| Errors | Stable envelope: `{ code, message, field_errors, trace_id, retryable }` |
| Idempotency | `Idempotency-Key` header on retryable write endpoints |
| CORS | Explicit comma-separated origins; wildcard origins are prohibited |
| Content-Type | `application/json` |
| Authorization | `Authorization: Bearer <JWT>` |

## 2. Response Envelope

### Success

```json
{
  "data": { ... },
  "meta": {
    "trace_id": "trc_01J...",
    "next_cursor": "cur_01J...",
    "has_more": true
  }
}
```

### Error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "field_errors": {
      "email": ["must be a valid email address"]
    },
    "trace_id": "trc_01J...",
    "retryable": false
  }
}
```

### Error Codes

| Code | HTTP Status | Retryable |
|------|-------------|-----------|
| VALIDATION_ERROR | 422 | No |
| UNAUTHORIZED | 401 | No |
| FORBIDDEN | 403 | No |
| NOT_FOUND | 404 | No |
| CONFLICT | 409 | No (idempotent retry returns original) |
| RATE_LIMITED | 429 | Yes |
| INTERNAL_ERROR | 500 | Yes |
| SERVICE_UNAVAILABLE | 503 | Yes |

---

## 3. Operational Endpoints

Operational endpoints serve infrastructure and deployment needs — load balancer health checks, ECS task readiness probes, and monitoring systems. They are not part of the customer-facing API contract.

### 3.1 Envelope Distinction

Operational endpoints use a **simplified response format** that omits the `meta` wrapper. The `trace_id` is embedded directly in the response data:

```
GET /health
→ { "data": { "status": "ok", "trace_id": "trc_01J..." } }

GET /ready
→ { "data": { "status": "ok", "database": "connected", "trace_id": "trc_01J..." } }
```

This is intentional: operational endpoints are consumed by machines (ALB target group health checks, ECS health checks, monitoring agents) that do not parse the full API envelope. Including a `meta` wrapper would break every standard health-check consumer.

### 3.2 Customer vs Operational Envelope

| Concern | Customer API (`/api/v1/*`) | Operational (`/health`, `/ready`) |
|---------|---------------------------|-----------------------------------|
| Envelope | `{ "data": ..., "meta": { "trace_id": "..." } }` | `{ "data": { ..., "trace_id": "..." } }` |
| Authentication | Required (JWT) | None |
| Rate limiting | Applied | Excluded |
| OpenAPI schema | Included | Excluded (`include_in_schema=False`) |
| Error format | `{ "error": { "code": "..." } }` | Standard HTTP status codes |
| Consumers | Browser, mobile app | Load balancer, ECS, monitoring |

### 3.3 Endpoint Listing

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness probe — returns 200 if the process is running |
| GET | `/ready` | Readiness probe — returns 200 if the process can serve traffic (database reachable) |

---

## 4. API Route Map

### 4.1 Identity (`/api/v1/identity`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/identity/me` | Current user profile and memberships |
| POST | `/identity/organizations` | Create organization |
| GET | `/identity/organizations/{org_id}` | Organization details |
| PATCH | `/identity/organizations/{org_id}` | Update settings |
| POST | `/identity/organizations/{org_id}/invitations` | Invite member |
| GET | `/identity/organizations/{org_id}/members` | List members |
| PATCH | `/identity/organizations/{org_id}/members/{user_id}` | Change role |
| DELETE | `/identity/organizations/{org_id}/members/{user_id}` | Remove member |

### 4.2 Catalog (`/api/v1/catalog`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/catalog/references` | List canonical references (paginated, filterable) |
| GET | `/catalog/references/{ref_id}` | Reference detail with market stats |
| GET | `/catalog/references/{ref_id}/price-history` | Price history |
| GET | `/catalog/brands` | List brands |
| GET | `/catalog/watch-lists` | User's watch lists |
| POST | `/catalog/watch-lists` | Create watch list |
| PUT | `/catalog/watch-lists/{id}` | Update watch list |
| DELETE | `/catalog/watch-lists/{id}` | Delete watch list |

#### B09 route behavior

- Implemented identity routes are `GET /identity/me`, `POST /identity/organizations`,
  `GET`/`PATCH /identity/organizations/{org_id}`, and
  `GET /identity/organizations/{org_id}/members`. The profile endpoint returns the
  authenticated user and all memberships, including organizations, without requiring
  an organization selector. Organization creation atomically creates the caller's
  owner membership. Organization reads and updates are limited to the selected
  organization; updates require the `members:manage` permission.
- Implemented catalog routes are `GET /catalog/brands`,
  `GET /catalog/references` (active references only; optional `q`, `brand_id`,
  `cursor`, and `limit` filters), `GET /catalog/references/{ref_id}`, and
  watch-list list/create/replace/delete routes. Watch-list operations are scoped to
  the authenticated organization; PUT replaces the name and complete reference set.
- These routes use the standard `{ data, meta }` success envelope and emit typed
  OpenAPI response schemas. Reference market statistics/price history and identity
  invitations/member-role changes/removal remain deferred until their valuation and
  invitation workflows are implemented.

### 4.3 Opportunities (`/api/v1/opportunities`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/opportunities` | Ranked opportunity feed (paginated, filterable) |
| GET | `/opportunities/{opp_id}` | Full deal analysis with cost waterfall, comps, risks |
| POST | `/opportunities/{opp_id}/feedback` | Record decision (PURCHASED/CONTACTED/DISMISSED) |
| GET | `/opportunities/{opp_id}/history` | Material version history |
| POST | `/opportunities/{opp_id}/trade-outcome` | Record realized trade outcome |

#### B10 feed and detail behavior

- `GET /opportunities` is scoped to the authenticated organization and supports the
  repository's cursor, sort, state, reference, brand, condition, ROI, profit,
  confidence, text, and organization-owned watch-list filters. Each result includes
  the listing summary, valuation and cost/risk breakdowns, the current user's
  decision, and the ADR-0004 freshness fields.
- `GET /opportunities/{opp_id}` returns the same valuation/listing detail plus
  `observation_at`. Opportunities not belonging to the selected organization return
  404. Both routes require `opportunities:read`.
- Valuation records currently retain comparable count and dispersion, but the schema
  has no individual comparable-record entity. The detail response therefore returns
  stored comparable aggregates and adjustment/risk details rather than fabricated
  comparable rows. Individual comparables remain deferred until their source model
  is introduced.

#### B11 feedback, history, and trade outcome behavior

- `POST /opportunities/{opp_id}/feedback` requires `feedback:write` and an
  `Idempotency-Key`. It records the dealer decision and moves the current material
  version from `published` to `dismissed`, `contacted`, or `purchased` atomically.
  Replaying the same key and payload returns the original feedback; reusing the key
  with a different payload or deciding on a non-published opportunity returns 409.
- `GET /opportunities/{opp_id}/history` requires `opportunities:read` and returns
  the tenant-scoped material versions in descending order, with their state and
  valuation summary. Any existing version in the selected organization can be used
  as the history lookup anchor.
- `POST /opportunities/{opp_id}/trade-outcome` requires `outcomes:write`, an
  `Idempotency-Key`, and an opportunity already in `purchased` state. The request
  records available acquisition/resale values, dealer-reported profit, and days to
  sell; money values must be JSON decimal strings (not JSON numbers), and actual
  profit is denominated in the acquisition currency. Feedback and outcome writes
  are audited in the same transaction. The database permits
  opportunity-independent outcomes, but this opportunity route always links the
  outcome to its tenant-scoped opportunity.

### 4.4 Watches (`/api/v1/watches`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/watches/{ref_id}/market` | Market detail: valuation bands, comps, price history |

### 4.5 Alerts (`/api/v1/alerts`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/alerts/rules` | List alert rules |
| POST | `/alerts/rules` | Create alert rule |
| GET | `/alerts/rules/{rule_id}` | Alert rule detail |
| PUT | `/alerts/rules/{rule_id}` | Update alert rule |
| DELETE | `/alerts/rules/{rule_id}` | Delete alert rule |
| POST | `/alerts/rules/{rule_id}/test` | Send test notification |
| GET | `/alerts/deliveries` | Alert delivery history |

#### B12 alert and activity behavior

- Alert-rule reads require `opportunities:read`; create, replace, delete, and test
  actions require `alerts:create`. Rules are organization-scoped. The DELETE route
  disables a rule rather than removing it so existing delivery records retain their
  rule reference.
- Rule filters accept `reference_ids`, `conditions`, `min_profit`, and
  `max_acquisition`; money filters are decimal strings. Channels are `in_app`,
  `push`, or `telegram`. Delivery history is limited to the authenticated user's
  deliveries in the selected organization.
- The test route requires an `Idempotency-Key` and writes a pending
  `notification.test_requested` outbox event. It returns 202 while queued (200 for
  an identical replay); delivery is performed asynchronously and is not reported as
  sent by the API.
- Activity routes require `opportunities:read` and return organization-scoped
  feedback and outcome records, newest first. Responses are bounded by a `limit`
  from 1 to 100. Outcomes may have no opportunity link when created outside the
  opportunity-specific workflow.

### 4.6 Activity (`/api/v1/activity`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/activity` | Team activity feed (decisions, outcomes) |
| GET | `/activity/outcomes` | Recorded trade outcomes |

### 4.7 Settings (`/api/v1/settings`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/settings/organization` | Organization assumptions (currency, tz, default fees) |
| PATCH | `/settings/organization` | Update organization assumptions |
| GET | `/settings/integrations` | Telegram/push connection status |
| POST | `/settings/integrations/telegram` | Link Telegram |
| DELETE | `/settings/integrations/telegram` | Unlink Telegram |
| POST | `/settings/integrations/push` | Register device token |
| DELETE | `/settings/integrations/push/{device_id}` | Unregister device |

#### B13 settings and integration behavior

- Organization settings reads require `opportunities:read`; patches require
  `members:manage`. Settings are merged into the organization's JSON settings so
  unrelated keys are preserved. Supported defaults are an ISO-style currency code,
  IANA time zone, and Decimal-string fee amounts matching the valuation cost model.
- Integration status and push registration are user-scoped within the selected
  organization. Push tokens are encrypted at rest with AES-GCM and never returned;
  the DELETE path uses an opaque device ID to avoid placing bearer-like tokens in
  request logs. The encryption key must remain stable for decrypting existing
  records and must be rotated only through a coordinated re-encryption procedure.
- Telegram linking uses the approved long-polling pattern. A short-lived random
  linking token is returned in a Telegram bot deep link; only its SHA-256 hash is
  stored. The polling worker completes the link by resolving the token and storing
  the chat ID encrypted. The link route is unavailable unless the bot token and
  username are configured.

### 4.8 Billing (`/api/v1/billing`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/billing/subscription` | Current subscription status |
| POST | `/billing/checkout` | Create Stripe Checkout session |
| POST | `/billing/portal` | Create Stripe Customer Portal session |
| POST | `/billing/webhook` | Stripe webhook (unauthenticated, signature-verified) |

#### B13 billing behavior

- Subscription reads require `opportunities:read`; checkout and portal creation
  require `billing:manage`. Checkout accepts a configured `plan_id`; provider price
  IDs, API credentials, and browser return URLs come from server configuration.
- Stripe requests use a bounded timeout. Provider errors are logged without secrets
  and surfaced as 503. Returned redirect URLs are restricted to HTTPS Stripe hosts.
- Webhooks verify the Stripe timestamped HMAC signature with a five-minute replay
  window, cap payloads at 1 MB, and record event IDs transactionally with
  subscription updates, making retries idempotent. Unknown event types are
  acknowledged and recorded without changing entitlements. Supported subscription
  statuses are conservatively mapped to the persisted status enum.

### 4.9 Operations (`/api/v1/admin`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/admin/sources` | List sources with health |
| PATCH | `/admin/sources/{source_id}` | Enable/disable/pause source |
| GET | `/admin/jobs` | Job list with status |
| POST | `/admin/jobs/{job_id}/replay` | Replay job |
| GET | `/admin/dlq` | DLQ message list |
| POST | `/admin/dlq/{msg_id}/replay` | Replay DLQ message |
| DELETE | `/admin/dlq/{msg_id}` | Discard DLQ message |
| GET | `/admin/flags` | List feature flags |
| PATCH | `/admin/flags/{flag_id}` | Update feature flag |
| GET | `/admin/unmatched` | Unmatched/ambiguous listings |
| POST | `/admin/unmatched/{listing_id}/resolve` | Resolve unmatched listing |
| GET | `/admin/duplicates` | Duplicate review queue |
| GET | `/admin/audit` | Audit event log |

#### B13 operations behavior

- All admin routes require the server-side `admin:manage` permission (platform
  operator allowlist). Source controls, feature flags, unmatched listing resolution,
  duplicate groups, and audit events are backed by persisted records and audited.
- Source health is reported as `unknown` until a health/heartbeat record exists;
  the API does not infer operational health from listing fetch history.
- Job and DLQ endpoints return 503 until a queue backend is configured. The API
  does not fabricate job state or claim to replay/discard messages without a queue
  adapter.

### 4.10 WebSocket

| Endpoint | Purpose |
|----------|---------|
| `wss://api.chronoarb.com/ws?token=<JWT>` | Authenticated real-time updates |

**Events:**
- `opportunity.published` — New opportunity available
- `opportunity.updated` — Material version change
- `opportunity.expired` — Opportunity no longer active
- `alert.delivered` — Notification delivery confirmation

---

## 5. Pagination

Cursor-based pagination for all mutable feeds:

```json
// Request
GET /api/v1/opportunities?cursor=cur_01J...&limit=50&sort=score_desc

// Response
{
  "data": [ ... ],
  "meta": {
    "trace_id": "trc_01J...",
    "next_cursor": "cur_01JABC...",
    "has_more": true
  }
}
```

---

## 6. Idempotency

Retryable write endpoints accept `Idempotency-Key` header:

```
POST /api/v1/opportunities/opp_01J.../feedback
Idempotency-Key: idem_01JDEF...

// If retried with same key, returns 200 with original result.
// If different payload with same key, returns 422.
```

The API validates client keys as 1–255 printable ASCII characters. Shared helpers
derive a stable storage key scoped to organization, user, and operation, plus a
canonical payload fingerprint. A write service must use the durable database
uniqueness constraint and compare the payload on duplicate keys in its transaction;
header validation alone does not provide idempotency.

---

## 7. OpenAPI Generation

- OpenAPI spec generated from Pydantic v2 models using FastAPI's built-in support.
- Spec committed to `docs/api/openapi.yaml`.
- Breaking change detection runs in CI; unapproved breaking changes block merge.
- TypeScript client regenerated via `openapi-typescript` or equivalent.
- Dart client regenerated via `openapi-generator` or equivalent.
- Generated clients committed to `packages/api-client-ts/` and `packages/api-client-dart/`.

---

## 8. Authorization Model

Every protected endpoint requires:
1. Valid JWT (validated against Cognito JWKS)
2. Active membership in the organization identified by the request context
3. Role meeting the minimum required for the endpoint

Authorization is resolved from the JWT claims, never from client-supplied organization parameters. The `organization_id` in route paths is validated against the authenticated user's memberships.
