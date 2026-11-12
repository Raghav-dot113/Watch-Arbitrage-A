from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from apps.api.integrations.api.schemas import PushDeviceCreateRequest
from apps.api.integrations.application.crypto import (
    digest_token,
    encrypt_provider_secret,
)
from apps.api.integrations.infrastructure.models import ProviderIntegration, PushDevice
from apps.api.integrations.infrastructure.repositories import (
    ProviderIntegrationRepository,
    PushDeviceRepository,
)
from apps.api.operations.application.audit import record_audit_event
from apps.api.settings import settings
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid

_TELEGRAM_USERNAME = re.compile(r"^[A-Za-z0-9_]{5,32}$")
_TELEGRAM_LINK_TTL = timedelta(minutes=10)


class TelegramLinkUnavailableError(Exception):
    pass


class DeviceTokenConflictError(Exception):
    pass


class ProviderIntegrationNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class TelegramLink:
    url: str
    expires_at: datetime


class IntegrationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.integrations = ProviderIntegrationRepository(session)
        self.devices = PushDeviceRepository(session)

    async def get_status(self, organization_id: str, user_id: str) -> dict[str, object]:
        telegram = await self.integrations.get_for_user(organization_id, user_id, "telegram")
        status = "disconnected"
        expires_at: datetime | None = None
        if telegram is not None:
            status = telegram.status
            expires_at = telegram.link_expires_at
            if status == "pending" and (expires_at is None or expires_at <= datetime.now(UTC)):
                status = "disconnected"
                expires_at = None
        elif settings.telegram_chat_id:
            status = "connected"
        devices = await self.devices.list_for_user(organization_id, user_id)
        return {
            "telegram_status": status,
            "telegram_link_expires_at": expires_at,
            "push_devices": devices,
        }

    async def connect_telegram_chat(
        self,
        organization_id: str,
        user_id: str,
        chat_id: str,
        *,
        trace_id: str,
    ) -> ProviderIntegration:
        clean_chat_id = str(chat_id).strip()
        if not clean_chat_id:
            raise ValueError("chat_id cannot be empty")
        integration = await self.integrations.get_for_update(organization_id, user_id, "telegram")
        now = datetime.now(UTC)
        if integration is None:
            integration = ProviderIntegration(
                id=generate_ulid("int"),
                organization_id=organization_id,
                user_id=user_id,
                provider="telegram",
                status="connected",
                external_id_ciphertext=encrypt_provider_secret(clean_chat_id),
                link_token_hash=None,
                link_expires_at=None,
            )
            self.session.add(integration)
        else:
            integration.status = "connected"
            integration.external_id_ciphertext = encrypt_provider_secret(clean_chat_id)
            integration.link_token_hash = None
            integration.link_expires_at = None
            integration.updated_at = now

        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="integration.telegram_linked",
            resource_type="provider_integration",
            resource_id=integration.id,
            trace_id=trace_id,
        )
        await self.session.commit()
        return integration

    async def get_effective_telegram_chat_id(
        self,
        organization_id: str,
        user_id: str,
    ) -> str | None:
        integration = await self.integrations.get_for_user(organization_id, user_id, "telegram")
        if (
            integration is not None
            and integration.status == "connected"
            and integration.external_id_ciphertext
        ):
            from apps.api.integrations.application.crypto import decrypt_provider_secret

            try:
                return decrypt_provider_secret(integration.external_id_ciphertext)
            except Exception:
                pass
        if settings.telegram_chat_id:
            return settings.telegram_chat_id
        return None

    async def start_telegram_link(
        self,
        organization_id: str,
        user_id: str,
        *,
        trace_id: str,
    ) -> TelegramLink:
        username = settings.telegram_bot_username.lstrip("@")
        if (
            not username
            or _TELEGRAM_USERNAME.fullmatch(username) is None
            or not settings.telegram_bot_token.get_secret_value()
        ):
            raise TelegramLinkUnavailableError
        integration = await self.integrations.get_for_update(organization_id, user_id, "telegram")
        now = datetime.now(UTC)
        expires_at = now + _TELEGRAM_LINK_TTL
        token = secrets.token_urlsafe(32)
        if integration is None:
            integration = ProviderIntegration(
                id=generate_ulid("int"),
                organization_id=organization_id,
                user_id=user_id,
                provider="telegram",
                status="pending",
                link_token_hash=digest_token(token),
                link_expires_at=expires_at,
            )
            self.session.add(integration)
        else:
            integration.status = "pending"
            integration.external_id_ciphertext = None
            integration.link_token_hash = digest_token(token)
            integration.link_expires_at = expires_at
            integration.updated_at = now

        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="integration.telegram_link_requested",
            resource_type="provider_integration",
            resource_id=integration.id,
            trace_id=trace_id,
        )
        await self.session.commit()
        return TelegramLink(
            url=f"https://t.me/{username}?start={token}",
            expires_at=expires_at,
        )

    async def complete_telegram_link(
        self,
        token: str,
        chat_id: str,
    ) -> ProviderIntegration:
        token_hash = digest_token(token)
        result = await self.session.execute(
            select(ProviderIntegration)
            .where(
                ProviderIntegration.provider == "telegram",
                ProviderIntegration.status == "pending",
                ProviderIntegration.link_token_hash == token_hash,
                ProviderIntegration.link_expires_at > datetime.now(UTC),
            )
            .with_for_update(of=ProviderIntegration)
        )
        integration = result.scalar_one_or_none()
        if integration is None:
            raise ProviderIntegrationNotFoundError
        integration.external_id_ciphertext = encrypt_provider_secret(chat_id)
        integration.status = "connected"
        integration.link_token_hash = None
        integration.link_expires_at = None
        integration.updated_at = datetime.now(UTC)
        await record_audit_event(
            self.session,
            organization_id=integration.organization_id,
            user_id=integration.user_id,
            action="integration.telegram_linked",
            resource_type="provider_integration",
            resource_id=integration.id,
        )
        await self.session.commit()
        return integration

    async def unlink_telegram(
        self,
        organization_id: str,
        user_id: str,
        *,
        trace_id: str,
    ) -> None:
        integration = await self.integrations.get_for_update(organization_id, user_id, "telegram")
        if integration is None:
            return
        integration.status = "disconnected"
        integration.external_id_ciphertext = None
        integration.link_token_hash = None
        integration.link_expires_at = None
        integration.updated_at = datetime.now(UTC)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="integration.telegram_unlinked",
            resource_type="provider_integration",
            resource_id=integration.id,
            trace_id=trace_id,
        )
        await self.session.commit()

    async def register_push_device(
        self,
        organization_id: str,
        user_id: str,
        payload: PushDeviceCreateRequest,
        *,
        trace_id: str,
    ) -> tuple[PushDevice, bool]:
        token_hash = digest_token(payload.device_token)
        existing = await self.devices.get_by_hash_any(token_hash)
        if existing is not None:
            if existing.organization_id != organization_id or existing.user_id != user_id:
                raise DeviceTokenConflictError
            existing.platform = payload.platform
            existing.token_ciphertext = encrypt_provider_secret(payload.device_token)
            existing.updated_at = datetime.now(UTC)
            await self.session.commit()
            return existing, False

        device = PushDevice(
            id=generate_ulid("dev"),
            organization_id=organization_id,
            user_id=user_id,
            platform=payload.platform,
            token_hash=token_hash,
            token_ciphertext=encrypt_provider_secret(payload.device_token),
        )
        self.session.add(device)
        try:
            await record_audit_event(
                self.session,
                organization_id=organization_id,
                user_id=user_id,
                action="integration.push_device_registered",
                resource_type="push_device",
                resource_id=device.id,
                details={"platform": payload.platform},
                trace_id=trace_id,
            )
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raced = await self.devices.get_by_hash_any(token_hash)
            if raced is None:
                raise
            if raced.organization_id != organization_id or raced.user_id != user_id:
                raise DeviceTokenConflictError from None
            return raced, False
        return device, True

    async def unregister_push_device(
        self,
        organization_id: str,
        user_id: str,
        device_id: str,
        *,
        trace_id: str,
    ) -> None:
        device = await self.devices.get_by_id_for_user(device_id, organization_id, user_id)
        if device is None:
            raise ProviderIntegrationNotFoundError
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="integration.push_device_unregistered",
            resource_type="push_device",
            resource_id=device.id,
            details={"platform": device.platform},
            trace_id=trace_id,
        )
        await self.session.delete(device)
        await self.session.commit()
