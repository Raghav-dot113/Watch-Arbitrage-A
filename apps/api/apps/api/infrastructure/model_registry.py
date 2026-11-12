"""Import all ORM models so shared metadata contains the complete schema."""

from apps.api.alerts.infrastructure import models as _alert_models  # noqa: F401
from apps.api.billing.infrastructure import models as _billing_models  # noqa: F401
from apps.api.catalog.infrastructure import models as _catalog_models  # noqa: F401
from apps.api.duplicates.infrastructure import models as _duplicate_models  # noqa: F401
from apps.api.feedback.infrastructure import models as _feedback_models  # noqa: F401
from apps.api.idempotency.infrastructure import models as _idempotency_models  # noqa: F401
from apps.api.identity.infrastructure import models as _identity_models  # noqa: F401
from apps.api.infrastructure.models import Base
from apps.api.integrations.infrastructure import models as _integration_models  # noqa: F401
from apps.api.listings.infrastructure import models as _listing_models  # noqa: F401
from apps.api.operations.infrastructure import models as _operations_models  # noqa: F401
from apps.api.opportunities.infrastructure import models as _opportunity_models  # noqa: F401
from apps.api.valuation.infrastructure import models as _valuation_models  # noqa: F401
from sqlalchemy import MetaData


def get_model_metadata() -> MetaData:
    return Base.metadata
