from __future__ import annotations

import logging

# Import ORM modules at composition boundaries so Base.metadata contains the
# complete application schema for migrations and test database creation.
import apps.api.catalog.infrastructure.models
import apps.api.idempotency.infrastructure.models
import apps.api.identity.infrastructure.models
import apps.api.listings.infrastructure.models
import apps.api.operations.infrastructure.models
import apps.api.valuation.infrastructure.models  # noqa: F401
from apps.api.alerts.api.router import router as alerts_router
from apps.api.billing.api.router import router as billing_router
from apps.api.feedback.api.router import router as feedback_router
from apps.api.identity.api.auth import UnauthorizedError
from apps.api.identity.api.router import router as identity_router
from apps.api.identity.application.service import IdentitySubjectNotFoundError
from apps.api.middleware.error_handler import (
    error_response,
    register_api_error_handlers,
)
from apps.api.middleware.tracing import TraceIdMiddleware
from apps.api.opportunities.api.router import router as opportunities_router
from apps.api.routes.health import health_handler
from apps.api.routes.ready import ready_handler
from apps.api.schemas import HealthResponse, ReadyResponse
from apps.api.settings import settings
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s trace_id=%(trace_id)s %(message)s",
)
logger = logging.getLogger("chronoarb.api")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    app.add_middleware(TraceIdMiddleware)
    register_api_error_handlers(app)

    async def unauthorized_handler(
        request: Request,
        _exc: UnauthorizedError | IdentitySubjectNotFoundError,
    ) -> JSONResponse:
        if isinstance(_exc, IdentitySubjectNotFoundError):
            logger.info(
                "authenticated_subject_not_found",
                extra={"trace_id": getattr(request.state, "trace_id", "unknown")},
            )
        return error_response(
            request,
            status_code=401,
            code="UNAUTHORIZED",
            message="Authentication is required or the identity is invalid.",
        )

    app.add_exception_handler(UnauthorizedError, unauthorized_handler)
    app.add_exception_handler(IdentitySubjectNotFoundError, unauthorized_handler)

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
    app.include_router(identity_router)
    app.include_router(opportunities_router)
    app.include_router(billing_router)
    app.include_router(feedback_router)
    app.include_router(alerts_router)
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

    logger.info("app_started", extra={"trace_id": "bootstrap"})

    return app


app = create_app()
