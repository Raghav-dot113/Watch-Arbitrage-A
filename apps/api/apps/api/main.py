from __future__ import annotations

import logging

# Import ORM modules at composition boundaries so Base.metadata contains the
# complete application schema for migrations and test database creation.
import apps.api.catalog.infrastructure.models
import apps.api.identity.infrastructure.models
import apps.api.listings.infrastructure.models
import apps.api.valuation.infrastructure.models  # noqa: F401
from apps.api.alerts.api.router import router as alerts_router
from apps.api.billing.api.router import router as billing_router
from apps.api.feedback.api.router import router as feedback_router
from apps.api.identity.api.auth import UnauthorizedError
from apps.api.identity.api.router import router as identity_router
from apps.api.identity.application.services import IdentitySubjectNotFoundError
from apps.api.middleware.error_handler import (
    generic_exception_handler,
    pydantic_validation_handler,
)
from apps.api.middleware.tracing import TraceIdMiddleware
from apps.api.opportunities.api.router import router as opportunities_router
from apps.api.routes.health import health_handler
from apps.api.routes.ready import ready_handler
from apps.api.schemas import ApiError, HealthResponse, ReadyResponse
from apps.api.settings import settings
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
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

    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)

    async def unauthorized_handler(
        request: Request,
        _exc: UnauthorizedError | IdentitySubjectNotFoundError,
    ) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", "unknown")
        error = ApiError(
            code="UNAUTHORIZED",
            message="Authentication is required or the identity is invalid.",
            trace_id=trace_id,
            retryable=False,
        )
        return JSONResponse(
            status_code=401,
            content={"error": error.model_dump()},
        )

    app.add_exception_handler(UnauthorizedError, unauthorized_handler)
    app.add_exception_handler(IdentitySubjectNotFoundError, unauthorized_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

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
