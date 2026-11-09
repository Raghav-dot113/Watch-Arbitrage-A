from __future__ import annotations

from apps.api.infrastructure.repository import TenantRepository
from apps.api.integrations.infrastructure.models import ProviderIntegration, PushDevice
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class ProviderIntegrationRepository(TenantRepository[ProviderIntegration]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ProviderIntegration)

    async def get_for_user(
        self,
        organization_id: str,
        user_id: str,
        provider: str,
    ) -> ProviderIntegration | None:
        result = await self.session.execute(
            select(ProviderIntegration).where(
                ProviderIntegration.organization_id == organization_id,
                ProviderIntegration.user_id == user_id,
                ProviderIntegration.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def get_for_update(
        self,
        organization_id: str,
        user_id: str,
        provider: str,
    ) -> ProviderIntegration | None:
        result = await self.session.execute(
            select(ProviderIntegration)
            .where(
                ProviderIntegration.organization_id == organization_id,
                ProviderIntegration.user_id == user_id,
                ProviderIntegration.provider == provider,
            )
            .with_for_update(of=ProviderIntegration)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, organization_id: str, user_id: str) -> list[ProviderIntegration]:
        result = await self.session.execute(
            select(ProviderIntegration)
            .where(
                ProviderIntegration.organization_id == organization_id,
                ProviderIntegration.user_id == user_id,
            )
            .order_by(ProviderIntegration.provider)
        )
        return list(result.scalars().all())


class PushDeviceRepository(TenantRepository[PushDevice]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PushDevice)

    async def get_by_hash(
        self,
        token_hash: str,
        organization_id: str,
        user_id: str,
    ) -> PushDevice | None:
        result = await self.session.execute(
            select(PushDevice).where(
                PushDevice.token_hash == token_hash,
                PushDevice.organization_id == organization_id,
                PushDevice.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hash_any(self, token_hash: str) -> PushDevice | None:
        result = await self.session.execute(
            select(PushDevice).where(PushDevice.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self,
        device_id: str,
        organization_id: str,
        user_id: str,
    ) -> PushDevice | None:
        result = await self.session.execute(
            select(PushDevice).where(
                PushDevice.id == device_id,
                PushDevice.organization_id == organization_id,
                PushDevice.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_for_user(self, organization_id: str, user_id: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(PushDevice)
            .where(
                PushDevice.organization_id == organization_id,
                PushDevice.user_id == user_id,
            )
        )
        return result.scalar_one()

    async def list_for_user(self, organization_id: str, user_id: str) -> list[PushDevice]:
        result = await self.session.execute(
            select(PushDevice)
            .where(
                PushDevice.organization_id == organization_id,
                PushDevice.user_id == user_id,
            )
            .order_by(PushDevice.created_at.desc(), PushDevice.id.desc())
        )
        return list(result.scalars().all())
