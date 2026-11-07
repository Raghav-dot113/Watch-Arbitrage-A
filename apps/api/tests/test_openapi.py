from __future__ import annotations

from apps.api.export_openapi import OPENAPI_PATH, check_openapi, render_openapi
from apps.api.main import app


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
