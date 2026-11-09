# API Endpoint Audit

This audit compares the endpoint checklist in the supplied task packet with
`docs/architecture/api-design.md`. The API design lists 58 contract routes,
including the two operational probes and the WebSocket route. The task packet
also explicitly asks to retain `GET /api/v1/identity/organizations`, which is
not listed in the API design. It is included below as an additional existing
route, for 59 audited rows total.

`Exists?` reflects the current route registration, not just ORM or service
foundations. The current API test suite could not be collected because Windows
Application Control blocked SQLAlchemy's `_collections_cy` extension; test
coverage therefore reflects test-file evidence, not a passing execution.

| Method | Path | Exists? | Envelope OK? | Perm OK? | Tests? | Action |
|---|---|---:|---|---|---|---|
| GET | `/health` | Yes | Yes (operational format) | N/A | Yes | Preserve and re-verify |
| GET | `/ready` | Yes | Yes (operational format) | N/A | Yes | Preserve and re-verify |
| GET | `/api/v1/identity/me` | Yes | Yes | Yes | Added | Implemented profile and memberships (Phase 1) |
| POST | `/api/v1/identity/organizations` | No | N/A | N/A | No | Create organization and owner membership atomically |
| GET | `/api/v1/identity/organizations/{org_id}` | No | N/A | N/A | No | Implement tenant-checked detail |
| PATCH | `/api/v1/identity/organizations/{org_id}` | No | N/A | N/A | No | Implement `members:manage` update |
| POST | `/api/v1/identity/organizations/{org_id}/invitations` | No | N/A | N/A | No | Add pending invitation workflow |
| GET | `/api/v1/identity/organizations/{org_id}/members` | No | N/A | N/A | No | Implement organization-scoped member list |
| PATCH | `/api/v1/identity/organizations/{org_id}/members/{user_id}` | No | N/A | N/A | No | Implement audited role change and last-owner protection |
| DELETE | `/api/v1/identity/organizations/{org_id}/members/{user_id}` | No | N/A | N/A | No | Implement audited removal and last-owner protection |
| GET | `/api/v1/catalog/references` | No | N/A | N/A | No | Implement filterable cursor-paginated catalog |
| GET | `/api/v1/catalog/references/{ref_id}` | No | N/A | N/A | No | Implement reference detail and market stats |
| GET | `/api/v1/catalog/references/{ref_id}/price-history` | No | N/A | N/A | No | Implement Decimal price history |
| GET | `/api/v1/catalog/brands` | No | N/A | N/A | No | Implement brand listing |
| GET | `/api/v1/catalog/watch-lists` | No | N/A | N/A | No | Implement tenant-scoped listing |
| POST | `/api/v1/catalog/watch-lists` | No | N/A | N/A | No | Implement `alerts:create` creation |
| PUT | `/api/v1/catalog/watch-lists/{id}` | No | N/A | N/A | No | Implement tenant-scoped update |
| DELETE | `/api/v1/catalog/watch-lists/{id}` | No | N/A | N/A | No | Implement tenant-scoped delete |
| GET | `/api/v1/watches/{ref_id}/market` | No | N/A | N/A | No | Implement market view with freshness metadata |
| GET | `/api/v1/opportunities` | Yes | Yes | Yes | Added; DB execution blocked | Added cursor pagination, feed envelope, and permission check (Phase 1) |
| GET | `/api/v1/opportunities/{opp_id}` | No | N/A | N/A | No | Implement tenant-scoped analysis detail |
| POST | `/api/v1/opportunities/{opp_id}/feedback` | Yes | Yes | Yes | Added; DB execution blocked | Added idempotent canonical route and deprecated alias (Phase 1) |
| GET | `/api/v1/opportunities/{opp_id}/history` | No | N/A | N/A | No | Implement material version history |
| POST | `/api/v1/opportunities/{opp_id}/trade-outcome` | No | N/A | N/A | No | Implement idempotent, audited outcome |
| GET | `/api/v1/alerts/rules` | Yes | Yes | Yes | Added; DB execution blocked | Added response envelope, pagination, and permission check (Phase 1) |
| POST | `/api/v1/alerts/rules` | Yes | Yes | Yes | Added; DB execution blocked | Added dealer permission, envelope, audit, and idempotency (Phase 1) |
| GET | `/api/v1/alerts/rules/{rule_id}` | No | N/A | N/A | No | Implement tenant-scoped detail |
| PUT | `/api/v1/alerts/rules/{rule_id}` | No | N/A | N/A | No | Implement validated update |
| DELETE | `/api/v1/alerts/rules/{rule_id}` | No | N/A | N/A | No | Implement tenant-scoped delete |
| POST | `/api/v1/alerts/rules/{rule_id}/test` | No | N/A | N/A | No | Enqueue idempotent outbox delivery |
| GET | `/api/v1/alerts/deliveries` | No | N/A | N/A | No | Implement cursor-paginated history |
| GET | `/api/v1/activity` | No | N/A | N/A | No | Implement organization-scoped team feed |
| GET | `/api/v1/activity/outcomes` | No | N/A | N/A | No | Implement cursor-paginated outcomes |
| GET | `/api/v1/settings/organization` | No | N/A | N/A | No | Implement organization assumptions read |
| PATCH | `/api/v1/settings/organization` | No | N/A | N/A | No | Implement validated, audited assumption update |
| GET | `/api/v1/settings/integrations` | No | N/A | N/A | No | Implement safe status response |
| POST | `/api/v1/settings/integrations/telegram` | No | N/A | N/A | No | Implement encrypted credential link |
| DELETE | `/api/v1/settings/integrations/telegram` | No | N/A | N/A | No | Implement audited unlink |
| POST | `/api/v1/settings/integrations/push` | No | N/A | N/A | No | Implement token-safe idempotent registration |
| DELETE | `/api/v1/settings/integrations/push/{token}` | No | N/A | N/A | No | Implement tenant-scoped unregister |
| GET | `/api/v1/billing/subscription` | No | N/A | N/A | No | Implement stored subscription read |
| POST | `/api/v1/billing/checkout` | No | N/A | N/A | No | Implement `billing:manage` gateway operation |
| POST | `/api/v1/billing/portal` | No | N/A | N/A | No | Implement `billing:manage` gateway operation |
| POST | `/api/v1/billing/webhook` | Yes | Yes | Signature | Added; DB execution blocked | Added signed idempotent route and deprecated alias; reconciliation remains |
| GET | `/api/v1/admin/sources` | No | N/A | N/A | No | Implement platform-ops-only list |
| PATCH | `/api/v1/admin/sources/{source_id}` | No | N/A | N/A | No | Implement audited source controls |
| GET | `/api/v1/admin/jobs` | No | N/A | N/A | No | Implement operations job list |
| POST | `/api/v1/admin/jobs/{job_id}/replay` | No | N/A | N/A | No | Implement idempotent replay |
| GET | `/api/v1/admin/dlq` | No | N/A | N/A | No | Implement DLQ list |
| POST | `/api/v1/admin/dlq/{msg_id}/replay` | No | N/A | N/A | No | Implement idempotent DLQ replay |
| DELETE | `/api/v1/admin/dlq/{msg_id}` | No | N/A | N/A | No | Implement audited soft discard |
| GET | `/api/v1/admin/flags` | No | N/A | N/A | No | Implement platform-ops-only list |
| PATCH | `/api/v1/admin/flags/{flag_id}` | No | N/A | N/A | No | Implement audited flag update |
| GET | `/api/v1/admin/unmatched` | No | N/A | N/A | No | Implement unmatched listing queue |
| POST | `/api/v1/admin/unmatched/{listing_id}/resolve` | No | N/A | N/A | No | Implement audited resolution |
| GET | `/api/v1/admin/duplicates` | No | N/A | N/A | No | Implement duplicate review queue |
| GET | `/api/v1/admin/audit` | No | N/A | N/A | No | Implement filtered cursor-paginated audit log |
| WS | `/ws` | No | N/A | N/A | No | Implement authenticated, organization-scoped events |
| GET | `/api/v1/identity/organizations` | Yes (additional route) | Yes | Yes | Yes | Preserve; add to formal API design contract |

## Phase 0 Baseline

- Registered contract routes: 5 of 58; the extra organization-list route is
  registered but absent from the API design route map.
- Route-coverage tests added with an explicit expected-missing set.
- The final checklist includes a WebSocket route, so the task packet's
  numbered list has 58 HTTP routes plus one WebSocket route (59 total rows
  including the two operational probes).

## Phase 1 Progress

- Eight of the 58 canonical routes are now registered. The extra organization
  list route remains registered outside the API design route map.
- Phase 1 added shared authorization, success/error envelopes, cursor
  pagination, transactional idempotency records, audit-event creation, and
  the current-user profile route.
- API integration-test files were added or extended for the changed routes;
  execution is still blocked at collection by Windows Application Control
  rejecting SQLAlchemy's `_collections_cy` extension.
