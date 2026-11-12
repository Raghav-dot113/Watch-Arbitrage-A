from __future__ import annotations

import re

from apps.api.alerts.api.schemas import AlertRuleCreateRequest, AlertRuleResponse
from apps.api.catalog.api.schemas import WatchListCreateRequest, WatchListResponse
from apps.api.export_openapi import OPENAPI_PATH, check_openapi, render_openapi
from apps.api.main import app
from apps.api.opportunities.api.schemas import OpportunityFeedItem


class TestOpenApi:
    def test_committed_spec_matches_app(self):
        assert OPENAPI_PATH.exists(), "Committed OpenAPI spec is missing"
        assert OPENAPI_PATH.read_text(encoding="utf-8") == render_openapi(), (
            "Committed OpenAPI spec is out of date; run the OpenAPI export target"
        )

    def test_check_returns_false_when_document_is_missing(self, tmp_path):
        assert check_openapi(tmp_path / "missing.yaml") is False

    def test_rendered_spec_is_deterministic(self):
        assert app.openapi() == app.openapi()
        assert render_openapi() == render_openapi()

    def test_check_detects_a_schema_change(self, tmp_path):
        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text(render_openapi(), encoding="utf-8")
        assert check_openapi(spec_path) is True

        async def new_route() -> dict[str, str]:
            return {"status": "new"}

        app.add_api_route(
            "/openapi-freshness-test",
            new_route,
            methods=["GET"],
            summary="Freshness test route",
        )
        try:
            app.openapi_schema = None
            assert check_openapi(spec_path) is False
        finally:
            app.routes.pop()
            app.openapi_schema = None

    def test_operational_routes_are_not_in_schema(self):
        paths = app.openapi().get("paths", {})
        assert "/health" not in paths
        assert "/ready" not in paths

    def test_api_operations_have_unique_readable_ids_and_error_envelopes(self):
        operations = [
            operation
            for path_item in app.openapi()["paths"].values()
            for method, operation in path_item.items()
            if method in {"get", "post", "put", "patch", "delete"}
        ]
        operation_ids = [operation["operationId"] for operation in operations]

        assert len(operation_ids) == len(set(operation_ids))
        assert all(
            re.fullmatch(r"[a-z][A-Za-z0-9]*_[a-z][A-Za-z0-9]*", operation_id)
            for operation_id in operation_ids
        )
        for operation in operations:
            assert operation["summary"]
            assert operation["description"]
            assert not operation["description"].startswith("Performs the ")
            assert operation["tags"]
            error_codes = [code for code in operation["responses"] if 400 <= int(code) < 500]
            assert error_codes
            for code in error_codes:
                response = operation["responses"][code]
                assert (
                    response["content"]["application/json"]["schema"]["$ref"]
                    == "#/components/schemas/ApiErrorResponse"
                )
        assert set(app.openapi()["components"]["schemas"]["ApiError"]["required"]) == {
            "code",
            "message",
            "field_errors",
            "trace_id",
            "retryable",
        }

    def test_servers_and_bearer_jwt_security_are_documented(self):
        schema = app.openapi()
        assert [server["url"] for server in schema["servers"]] == [
            "http://127.0.0.1:8000",
            "https://api.chronoarb.example.com",
        ]
        security_scheme = schema["components"]["securitySchemes"]["BearerJWT"]
        assert security_scheme["type"] == "http"
        assert security_scheme["scheme"] == "bearer"
        assert security_scheme["bearerFormat"] == "JWT"
        assert "development tokens" in security_scheme["description"]
        assert "OIDC" in security_scheme["description"]

    def test_main_flow_schemas_include_safe_examples(self):
        schemas = app.openapi()["components"]["schemas"]
        for schema_name in (
            "OpportunityFeedItem",
            "WatchListCreateRequest",
            "WatchListResponse",
            "AlertRuleCreateRequest",
            "AlertRuleResponse",
        ):
            assert schemas[schema_name]["examples"]
        opportunity_query_examples = {
            parameter["name"]: parameter["example"]
            for parameter in app.openapi()["paths"]["/api/v1/opportunities"]["get"]["parameters"]
            if "example" in parameter
        }
        assert opportunity_query_examples["sort"] == "profit_desc"

    def test_main_flow_examples_validate_against_their_models(self):
        for model in (
            OpportunityFeedItem,
            WatchListCreateRequest,
            WatchListResponse,
            AlertRuleCreateRequest,
            AlertRuleResponse,
        ):
            examples = model.model_config["json_schema_extra"]["examples"]
            for example in examples:
                model.model_validate(example)
