from __future__ import annotations

from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.repository import BaseRepository, TenantRepository
from sqlalchemy import select
from sqlalchemy.orm import joinedload


class OrganizationRepository(BaseRepository[Organization]):
    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.session.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()


class UserRepository(BaseRepository[User]):
    async def get_by_cognito_sub(self, cognito_sub: str) -> User | None:
        result = await self.session.execute(select(User).where(User.cognito_sub == cognito_sub))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


class MembershipRepository(TenantRepository[Membership]):
    async def get_by_user_and_org(self, user_id: str, organization_id: str) -> Membership | None:
        result = await self.session.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .where(Membership.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def list_members(self, organization_id: str) -> list[Membership]:
        result = await self.session.execute(
            select(Membership)
            .options(joinedload(Membership.user))
            .where(Membership.organization_id == organization_id)
            .order_by(Membership.created_at, Membership.id)
        )
        return list(result.scalars().all())

    async def list_for_user(self, user_id: str) -> list[Membership]:
        result = await self.session.execute(
            select(Membership)
            .options(joinedload(Membership.organization))
            .where(Membership.user_id == user_id)
            .order_by(Membership.created_at, Membership.organization_id)
        )
        return list(result.scalars().all())
