from __future__ import annotations

from apps.api.main import app

Route = tuple[str, str]

CONTRACT_ROUTES: frozenset[Route] = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/ready"),
        ("GET", "/api/v1/identity/me"),
        ("POST", "/api/v1/identity/organizations"),
        ("GET", "/api/v1/identity/organizations/{org_id}"),
        ("PATCH", "/api/v1/identity/organizations/{org_id}"),
        ("POST", "/api/v1/identity/organizations/{org_id}/invitations"),
        ("GET", "/api/v1/identity/organizations/{org_id}/members"),
        ("PATCH", "/api/v1/identity/organizations/{org_id}/members/{user_id}"),
        ("DELETE", "/api/v1/identity/organizations/{org_id}/members/{user_id}"),
        ("GET", "/api/v1/catalog/references"),
        ("GET", "/api/v1/catalog/references/{ref_id}"),
        ("GET", "/api/v1/catalog/references/{ref_id}/price-history"),
        ("GET", "/api/v1/catalog/brands"),
        ("GET", "/api/v1/catalog/watch-lists"),
        ("POST", "/api/v1/catalog/watch-lists"),
        ("PUT", "/api/v1/catalog/watch-lists/{id}"),
        ("DELETE", "/api/v1/catalog/watch-lists/{id}"),
        ("GET", "/api/v1/watches/{ref_id}/market"),
        ("GET", "/api/v1/opportunities"),
        ("GET", "/api/v1/opportunities/{opp_id}"),
        ("POST", "/api/v1/opportunities/{opp_id}/feedback"),
        ("GET", "/api/v1/opportunities/{opp_id}/history"),
        ("POST", "/api/v1/opportunities/{opp_id}/trade-outcome"),
        ("GET", "/api/v1/alerts/rules"),
        ("POST", "/api/v1/alerts/rules"),
        ("GET", "/api/v1/alerts/rules/{rule_id}"),
        ("PUT", "/api/v1/alerts/rules/{rule_id}"),
        ("DELETE", "/api/v1/alerts/rules/{rule_id}"),
        ("POST", "/api/v1/alerts/rules/{rule_id}/test"),
        ("GET", "/api/v1/alerts/deliveries"),
        ("GET", "/api/v1/activity"),
        ("GET", "/api/v1/activity/outcomes"),
        ("GET", "/api/v1/settings/organization"),
        ("PATCH", "/api/v1/settings/organization"),
        ("GET", "/api/v1/settings/integrations"),
        ("POST", "/api/v1/settings/integrations/telegram"),
        ("DELETE", "/api/v1/settings/integrations/telegram"),
        ("POST", "/api/v1/settings/integrations/push"),
        ("DELETE", "/api/v1/settings/integrations/push/{token}"),
        ("GET", "/api/v1/billing/subscription"),
        ("POST", "/api/v1/billing/checkout"),
        ("POST", "/api/v1/billing/portal"),
        ("POST", "/api/v1/billing/webhook"),
        ("GET", "/api/v1/admin/sources"),
        ("PATCH", "/api/v1/admin/sources/{source_id}"),
        ("GET", "/api/v1/admin/jobs"),
        ("POST", "/api/v1/admin/jobs/{job_id}/replay"),
        ("GET", "/api/v1/admin/dlq"),
        ("POST", "/api/v1/admin/dlq/{msg_id}/replay"),
        ("DELETE", "/api/v1/admin/dlq/{msg_id}"),
        ("GET", "/api/v1/admin/flags"),
        ("PATCH", "/api/v1/admin/flags/{flag_id}"),
        ("GET", "/api/v1/admin/unmatched"),
        ("POST", "/api/v1/admin/unmatched/{listing_id}/resolve"),
        ("GET", "/api/v1/admin/duplicates"),
        ("GET", "/api/v1/admin/audit"),
        ("WS", "/ws"),
    }
)

OPERATIONAL_ROUTES: frozenset[Route] = frozenset({("GET", "/health"), ("GET", "/ready")})
WEBSOCKET_ROUTE: Route = ("WS", "/ws")

# Remove each route from this set as its implementation lands in a phase.
EXPECTED_MISSING_ROUTES: frozenset[Route] = frozenset(
    CONTRACT_ROUTES
    - {
        ("GET", "/health"),
        ("GET", "/ready"),
        ("GET", "/api/v1/identity/me"),
        ("GET", "/api/v1/opportunities"),
        ("GET", "/api/v1/alerts/rules"),
        ("POST", "/api/v1/alerts/rules"),
        ("POST", "/api/v1/opportunities/{opp_id}/feedback"),
        ("POST", "/api/v1/billing/webhook"),
    }
)


def _registered_routes() -> set[Route]:
    registered: set[Route] = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None)
        if methods is not None:
            registered.update((method, path) for method in methods)
        elif path == WEBSOCKET_ROUTE[1]:
            registered.add(WEBSOCKET_ROUTE)
    return registered


def test_contract_routes_match_registered_routes() -> None:
    actual = _registered_routes() & CONTRACT_ROUTES
    assert actual == CONTRACT_ROUTES - EXPECTED_MISSING_ROUTES


def test_documented_contract_routes_match_openapi() -> None:
    actual = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
        if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    } & CONTRACT_ROUTES
    documented = CONTRACT_ROUTES - OPERATIONAL_ROUTES - {WEBSOCKET_ROUTE}
    expected_missing = EXPECTED_MISSING_ROUTES - {WEBSOCKET_ROUTE}
    assert actual == documented - expected_missing
