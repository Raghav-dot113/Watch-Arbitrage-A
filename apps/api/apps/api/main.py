from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apps.api.alerts.api.routes import router as alerts_router
from apps.api.billing.api.routes import router as billing_router
from apps.api.catalog.api.routes import router as catalog_router
from apps.api.feedback.api.routes import activity_router
from apps.api.feedback.api.routes import router as feedback_router
from apps.api.identity.api.routes import router as identity_router
from apps.api.infrastructure.database import (
    initialize_dev_sqlite_schema,
    is_dev_sqlite_database,
)
from apps.api.infrastructure.model_registry import get_model_metadata
from apps.api.integrations.api.routes import router as integrations_router
from apps.api.middleware.error_handler import (
    register_api_error_handlers,
)
from apps.api.middleware.tracing import TraceIdMiddleware
from apps.api.openapi import configure_openapi, generate_operation_id
from apps.api.operations.api.routes import router as admin_router
from apps.api.opportunities.api.routes import router as opportunities_router
from apps.api.org_settings.api.routes import router as settings_router
from apps.api.routes.health import health_handler
from apps.api.routes.ready import ready_handler
from apps.api.schemas import HealthResponse, ReadyResponse
from apps.api.settings import settings
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

get_model_metadata()


class _TraceIdLoggerFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = getattr(record, "trace_id", "unknown")
        return True


logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
    force=True,
)
logger = logging.getLogger("chronoarb.api")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    if is_dev_sqlite_database():
        await initialize_dev_sqlite_schema()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        generate_unique_id_function=generate_operation_id,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origin_allowlist),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-Organization-ID",
            "X-Trace-Id",
        ],
        expose_headers=["X-Trace-Id"],
    )
    app.add_middleware(TraceIdMiddleware)

    register_api_error_handlers(app)

    app.add_api_route(
        "/health",
        health_handler,
        methods=["GET"],
        name="health",
        summary="Check API liveness",
        description=(
            "Returns whether the API process is running. "
            "This endpoint does not require authentication."
        ),
        response_model=HealthResponse,
        include_in_schema=False,
    )
    app.add_api_route(
        "/ready",
        ready_handler,
        methods=["GET"],
        name="ready",
        summary="Check API readiness",
        description=(
            "Returns whether the API and its database dependency are ready to serve traffic."
        ),
        response_model=ReadyResponse,
        responses={
            503: {
                "description": "A required dependency is unavailable.",
                "model": ReadyResponse,
            }
        },
        include_in_schema=False,
    )
    app.include_router(identity_router)
    app.include_router(catalog_router)
    app.include_router(opportunities_router)
    app.include_router(feedback_router)
    app.include_router(activity_router)
    app.include_router(alerts_router)
    app.include_router(settings_router)
    app.include_router(integrations_router)
    app.include_router(billing_router)
    app.include_router(admin_router)
    configure_openapi(app)

    logger.info("app_started", extra={"trace_id": "bootstrap"})

    return app


app = create_app()
