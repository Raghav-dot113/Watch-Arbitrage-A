from __future__ import annotations

import re
from typing import Any

from apps.api.schemas import ApiErrorResponse
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

OPERATION_DESCRIPTIONS = {
    "get_me": "Returns the authenticated user's profile and organization memberships.",
    "list_organizations": "Lists organizations where the authenticated user has membership.",
    "create_organization": "Creates an organization and adds the authenticated user as its owner.",
    "get_organization": "Returns an organization in the authenticated user's active organization.",
    "patch_organization": "Updates the name or settings of the active organization.",
    "list_organization_members": "Lists members in the authenticated user's organization scope.",
    "list_brands": "Lists brands available in the catalog.",
    "list_references": "Searches catalog references with optional brand and cursor filters.",
    "get_reference": "Returns catalog details and aliases for a reference.",
    "list_watch_lists": "Lists watch lists belonging to the authenticated organization.",
    "create_watch_list": "Creates a watch list for the authenticated organization.",
    "update_watch_list": "Replaces the name and catalog references in a watch list.",
    "delete_watch_list": "Disables a watch list in the authenticated organization.",
    "list_opportunities": "Lists published opportunities with filters and pagination.",
    "get_opportunity": ("Returns an opportunity's listing, valuation, and decision context."),
    "record_feedback": (
        "Records an idempotent contacted, dismissed, or purchased opportunity decision."
    ),
    "get_opportunity_history": "Lists decision and valuation history for an opportunity.",
    "record_trade_outcome": "Records an idempotent realized outcome for a purchased opportunity.",
    "list_activity": "Lists recent activity for the authenticated organization.",
    "list_trade_outcomes": "Lists realized trade outcomes for the authenticated organization.",
    "list_alert_rules": "Lists alert rules belonging to the authenticated organization.",
    "create_alert_rule": "Creates an alert rule for the authenticated organization.",
    "get_alert_rule": "Returns an alert rule in the authenticated organization.",
    "update_alert_rule": "Replaces an alert rule's settings in the authenticated organization.",
    "delete_alert_rule": "Disables an alert rule in the authenticated organization.",
    "request_alert_test": "Queues an idempotent test notification for an enabled alert rule.",
    "list_alert_deliveries": "Lists alert delivery attempts for the authenticated user.",
    "get_organization_settings": "Returns settings for the authenticated organization.",
    "patch_organization_settings": "Updates settings for the authenticated organization.",
    "get_integration_status": "Returns the current user's integration status.",
    "link_telegram": "Creates a short-lived link flow for the user's Telegram account.",
    "unlink_telegram": "Removes the current user's Telegram integration.",
    "register_push_device": "Registers or refreshes a push device for the authenticated user.",
    "unregister_push_device": "Removes a push device belonging to the authenticated user.",
    "get_subscription": "Returns subscription status for the authenticated organization.",
    "create_checkout_session": "Creates a subscription approval flow for the organization.",
    "cancel_subscription": "Cancels the authenticated organization's subscription.",
    "paypal_webhook": "Verifies and processes an idempotent PayPal webhook event.",
    "paypal_webhook_legacy": (
        "Processes the legacy PayPal webhook path; prefer the current webhook path."
    ),
    "list_sources": "Lists configured listing sources for platform operations.",
    "update_source": "Enables or disables a configured listing source.",
    "list_feature_flags": "Lists feature flags for platform operations.",
    "update_feature_flag": "Updates a feature flag's rollout configuration.",
    "list_audit_events": "Lists immutable audit events for platform operations.",
    "list_unmatched_listings": "Lists unmatched listings for platform operations.",
    "resolve_unmatched_listing": "Associates an unmatched listing with an active reference.",
    "list_duplicate_groups": "Lists listing duplicate groups for platform operations.",
    "list_jobs": "Reports queue job status; no queue backend is currently configured.",
    "replay_job": "Requests a queue job replay; no queue backend is currently configured.",
    "list_dead_letters": "Lists dead-letter messages; no queue backend is currently configured.",
    "replay_dead_letter": "Requests a dead-letter replay; no queue backend is configured.",
    "discard_dead_letter": "Requests dead-letter removal; no queue backend is configured.",
}

ROUTE_ERROR_STATUS_CODES: dict[str, tuple[int, ...]] = {
    "create_organization": (409,),
    "get_organization": (404,),
    "patch_organization": (404,),
    "list_organization_members": (404,),
    "get_reference": (404,),
    "update_watch_list": (404,),
    "delete_watch_list": (404,),
    "get_opportunity": (404,),
    "record_feedback": (404, 409),
    "get_opportunity_history": (404,),
    "record_trade_outcome": (404, 409),
    "get_alert_rule": (404,),
    "update_alert_rule": (404,),
    "delete_alert_rule": (404,),
    "request_alert_test": (404, 409),
    "get_organization_settings": (404,),
    "patch_organization_settings": (404,),
    "link_telegram": (503,),
    "register_push_device": (409, 503),
    "unregister_push_device": (404,),
    "create_checkout_session": (404, 409, 503),
    "cancel_subscription": (409, 503),
    "paypal_webhook": (400, 401, 413, 503),
    "paypal_webhook_legacy": (400, 401, 413, 503),
    "update_source": (404,),
    "update_feature_flag": (404,),
    "resolve_unmatched_listing": (404,),
    "list_jobs": (503,),
    "replay_job": (503,),
    "list_dead_letters": (503,),
    "replay_dead_letter": (503,),
    "discard_dead_letter": (503,),
}

ERROR_RESPONSES: dict[int, tuple[str, str, bool]] = {
    400: ("The request is invalid or could not be verified.", "REQUEST_ERROR", False),
    401: (
        "Authentication is required or the supplied credentials are invalid.",
        "UNAUTHORIZED",
        False,
    ),
    403: (
        "The authenticated user does not have permission for this operation.",
        "FORBIDDEN",
        False,
    ),
    404: (
        "The requested resource was not found in the authenticated scope.",
        "NOT_FOUND",
        False,
    ),
    405: (
        "The HTTP method is not allowed for this resource.",
        "METHOD_NOT_ALLOWED",
        False,
    ),
    409: ("The request conflicts with the current resource or prior state.", "CONFLICT", False),
    413: ("The request payload exceeds the accepted size.", "REQUEST_ERROR", False),
    422: ("One or more fields are invalid.", "VALIDATION_ERROR", False),
    500: ("An internal error occurred.", "INTERNAL_ERROR", True),
    503: ("A required service is unavailable.", "SERVICE_UNAVAILABLE", True),
}

SERVER_URLS = [
    {"url": "http://127.0.0.1:8000", "description": "Local development"},
    {
        "url": "https://api.chronoarb.example.com",
        "description": "Production placeholder; replace with the approved deployment URL.",
    },
]


def _camel_case(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", value)
    if not parts:
        return "api"
    first, *rest = parts
    return first.lower() + "".join(part[:1].upper() + part[1:] for part in rest)


def _snake_case(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def generate_operation_id(route: APIRoute) -> str:
    """Return a short, stable operationId based on its tag and endpoint name."""
    tag = route.tags[0] if route.tags else "api"
    return f"{_camel_case(tag)}_{_camel_case(route.name)}"


def _error_example(status_code: int) -> dict[str, Any]:
    description, code, retryable = ERROR_RESPONSES[status_code]
    return {
        "error": {
            "code": code,
            "message": description,
            "field_errors": {},
            "trace_id": "00000000-0000-4000-8000-000000000001",
            "retryable": retryable,
        }
    }


def _add_error_response(operation: dict[str, Any], status_code: int) -> None:
    description, _, _ = ERROR_RESPONSES[status_code]
    responses = operation.setdefault("responses", {})
    response = responses.setdefault(str(status_code), {})
    if response.get("description") in {None, "", "Validation Error"}:
        response["description"] = description
    content = response.setdefault("content", {})
    content["application/json"] = {
        "schema": {"$ref": "#/components/schemas/ApiErrorResponse"},
        "example": _error_example(status_code),
    }


def _add_error_schema(components: dict[str, Any]) -> None:
    schema = ApiErrorResponse.model_json_schema(
        ref_template="#/components/schemas/{model}",
    )
    definitions = schema.pop("$defs", {})
    schemas = components.setdefault("schemas", {})
    error_schema = definitions.get("ApiError")
    if error_schema is not None:
        error_schema["required"] = list(error_schema.get("properties", {}))
    schemas.update(definitions)
    schemas["ApiErrorResponse"] = schema


def configure_openapi(app: FastAPI) -> None:
    """Install APIMatic-friendly metadata and the application's real error schema."""

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema is not None:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            servers=SERVER_URLS,
        )
        components = schema.setdefault("components", {})
        _add_error_schema(components)

        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes.pop("HTTPBearer", None)
        security_schemes["BearerJWT"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "JWT bearer access token. Local and test environments use development "
                "tokens; production is expected to use OIDC-issued tokens. Never use a "
                "real token in examples."
            ),
        }

        for path_item in schema.get("paths", {}).values():
            for method, operation in path_item.items():
                if method not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                    continue
                operation_id = operation["operationId"]
                tags = operation.get("tags") or ["api"]
                tag_prefix = f"{_camel_case(tags[0])}_"
                endpoint_name = _snake_case(operation_id.removeprefix(tag_prefix))
                operation["tags"] = tags
                operation["description"] = (
                    OPERATION_DESCRIPTIONS.get(endpoint_name)
                    or f"Performs the {operation['summary'].lower()} operation."
                )

                for security in operation.get("security", []):
                    if "HTTPBearer" in security:
                        security["BearerJWT"] = security.pop("HTTPBearer")

                status_codes = {
                    405,
                    422,
                    500,
                    *ROUTE_ERROR_STATUS_CODES.get(endpoint_name, ()),
                }
                if operation.get("security"):
                    status_codes.update({401, 403})
                for status_code in status_codes:
                    _add_error_response(operation, status_code)

                if endpoint_name == "list_opportunities":
                    examples = {
                        "limit": 25,
                        "sort": "profit_desc",
                        "state": "published",
                        "min_profit": "250.00",
                        "min_confidence": "0.80",
                    }
                    for parameter in operation.get("parameters", []):
                        if parameter.get("name") in examples:
                            parameter["example"] = examples[parameter["name"]]

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
