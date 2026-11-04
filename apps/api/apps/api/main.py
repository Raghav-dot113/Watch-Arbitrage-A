from __future__ import annotations

import logging

from apps.api.alerts.api.routes import router as alerts_router
from apps.api.alerts.infrastructure import models as _alert_models  # noqa: F401
from apps.api.billing.api.routes import router as billing_router
from apps.api.billing.infrastructure import models as _billing_models  # noqa: F401
from apps.api.catalog.api.routes import router as catalog_router
from apps.api.catalog.infrastructure import models as _catalog_models  # noqa: F401
from apps.api.duplicates.infrastructure import models as _duplicate_models  # noqa: F401
from apps.api.feedback.api.routes import activity_router
from apps.api.feedback.api.routes import router as feedback_router
from apps.api.feedback.infrastructure import models as _feedback_models  # noqa: F401
from apps.api.identity.api.routes import router as identity_router
from apps.api.identity.infrastructure import models as _identity_models  # noqa: F401
from apps.api.integrations.api.routes import router as integrations_router
from apps.api.integrations.infrastructure import models as _integration_models  # noqa: F401
from apps.api.listings.infrastructure import models as _listing_models  # noqa: F401
from apps.api.middleware.error_handler import (
    generic_exception_handler,
    http_exception_handler,
    pydantic_validation_handler,
)
from apps.api.middleware.tracing import TraceIdMiddleware
from apps.api.operations.api.routes import router as admin_router
from apps.api.operations.infrastructure import models as _operations_models  # noqa: F401
from apps.api.opportunities.api.routes import router as opportunities_router
from apps.api.opportunities.infrastructure import models as _opportunity_models  # noqa: F401
from apps.api.org_settings.api.routes import router as settings_router
from apps.api.routes.health import health_handler
from apps.api.routes.ready import ready_handler
from apps.api.settings import settings
from apps.api.valuation.infrastructure import models as _valuation_models  # noqa: F401
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

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

    app.add_exception_handler(RequestValidationError, pydantic_validation_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    app.add_api_route(
        "/health",
        health_handler,
        methods=["GET"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/ready",
        ready_handler,
        methods=["GET"],
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

    logger.info("app_started", extra={"trace_id": "bootstrap"})

    return app


app = create_app()
