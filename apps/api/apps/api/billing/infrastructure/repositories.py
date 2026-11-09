from __future__ import annotations

from apps.api.billing.infrastructure.models import Subscription
from apps.api.infrastructure.repository import TenantRepository
from apps.api.integrations.infrastructure.models import PayPalWebhookEvent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tenant_repository: TenantRepository[Subscription] = TenantRepository(
            session, Subscription
        )

    async def get_by_id(self, id: str, organization_id: str) -> Subscription | None:
        return await self.tenant_repository.get_by_id(Subscription, id, organization_id)

    async def get_latest_for_org(self, organization_id: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .where(
                Subscription.organization_id == organization_id,
                Subscription.paypal_subscription_id.is_not(None),
            )
            .order_by(Subscription.created_at.desc(), Subscription.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_paypal_subscription_id(
        self, paypal_subscription_id: str
    ) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.paypal_subscription_id == paypal_subscription_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()


class PayPalWebhookEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, event_id: str) -> PayPalWebhookEvent | None:
        return await self.session.get(PayPalWebhookEvent, event_id)
