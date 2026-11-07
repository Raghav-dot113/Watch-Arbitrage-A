# ADR 0010: PayPal subscriptions and AG Grid opportunity feed

- Status: Accepted
- Date: 2026-11-07
- Decision owners: Product owner (explicit task approval), engineering

## Context

The MVP analysis and existing billing API used Stripe Billing, Checkout, and the
Customer Portal. The product owner explicitly approved replacing Stripe with
PayPal subscriptions, including the API, subscription lifecycle webhooks, and
configuration. The customer dashboard also needs a sortable/filterable
opportunity feed.

The referenced PayPal/AG Grid hackathon repository has no discoverable license
file. Its source is not copied. The application uses AG Grid Community as a
dependency and implements its own integration. AG Studio is not included.

## Decision

- PayPal Subscriptions is the sole billing provider for new subscriptions.
- PayPal credentials, configured plan IDs, return URLs, and webhook ID are
  server-side configuration. The browser only receives the approved PayPal URL.
- PayPal webhook signatures are verified using PayPal's
  `verify-webhook-signature` API before event processing.
- Webhook event IDs are persisted transactionally with organization-scoped
  subscription updates for replay safety.
- Existing Stripe database columns and webhook receipts are retained as inert
  legacy data during the forward-only migration. They are not read to grant
  entitlements. Existing Stripe subscriptions do not transfer to PayPal; affected
  organizations must enroll again.
- AG Grid Community powers the opportunity table. AG Studio and paid AG Grid
  modules are out of scope.

## Consequences

- Deployments must configure a PayPal app, subscription plans, and the webhook
  URL before billing can be enabled.
- Subscription cancellation is initiated through the API; PayPal lifecycle
  events remain authoritative for subsequent status changes.
- Operators must coordinate the Stripe-to-PayPal cutover and communicate
  re-enrollment to existing subscribers before deploying.
- Removing the legacy Stripe columns and event table requires a later
  expand/contract migration after verifying no rollback or retention need.
- The opportunity feed gains client-side sorting/filtering and AG Grid keyboard
  navigation while retaining the existing API, tenant scope, and empty/error
  states.
