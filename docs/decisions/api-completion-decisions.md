# API Completion Decisions

- **Use the checked-in API design as the canonical route inventory.** The
  supplied checklist includes `GET /api/v1/identity/organizations`, while
  `docs/architecture/api-design.md` does not. Keep the existing endpoint and
  test it, but track it as an additional compatibility route until the API
  design is updated. The API design inventory contains 58 routes; the task
  checklist has one additional HTTP route and therefore 59 rows when its
  WebSocket and operational routes are counted.
- **Use the API design's error envelope example (`error.code`).** The convention
  table says `error_code`, but the normative response example and error table
  use `error.code`; this is the more concrete and consistent response shape.
- **Use HTTP 422 for idempotency key/body mismatch.** The API design §6 says
  mismatched payloads return 422, while the task brief says 409. The API design
  is the stated contract source of truth; do not silently substitute 409.
- **Keep the requested legacy routes as deprecated aliases** when adding the
  canonical opportunity feedback and billing webhook paths. This preserves
  existing clients while conforming to the route checklist.
