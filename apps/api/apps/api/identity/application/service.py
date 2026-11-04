from __future__ import annotations

from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.identity.infrastructure.repositories import (
    MembershipRepository,
    OrganizationRepository,
    UserRepository,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


class OrganizationSlugConflictError(Exception):
    pass


class OrganizationNotFoundError(Exception):
    pass


class IdentityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.organizations = OrganizationRepository(session)
        self.memberships = MembershipRepository(session)

    async def current_user(self, user_id: str) -> tuple[User, list[Membership]]:
        user = await self.users.get_by_id(User, user_id)
        if user is None:
            raise LookupError("Authenticated user no longer exists")
        return user, await self.memberships.list_for_user(user_id)

    async def create_organization(self, user_id: str, *, name: str, slug: str) -> Organization:
        if await self.organizations.get_by_slug(slug) is not None:
            raise OrganizationSlugConflictError

        organization = Organization(id=generate_ulid("org"), name=name, slug=slug)
        membership = Membership(
            id=generate_ulid("mem"),
            organization_id=organization.id,
            user_id=user_id,
            role="owner",
        )
        self.session.add_all([organization, membership])
        try:
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise OrganizationSlugConflictError from error
        return organization

    async def get_organization(self, organization_id: str, requested_id: str) -> Organization:
        if organization_id != requested_id:
            raise OrganizationNotFoundError
        organization = await self.organizations.get_by_id(Organization, organization_id)
        if organization is None:
            raise OrganizationNotFoundError
        return organization

    async def update_organization(
        self,
        organization_id: str,
        requested_id: str,
        *,
        name: str | None,
        settings: dict[str, object] | None,
        update_settings: bool,
    ) -> Organization:
        organization = await self.get_organization(organization_id, requested_id)
        if name is not None:
            organization.name = name
        if update_settings:
            organization.settings = settings
        await self.session.commit()
        return organization

    async def list_members(self, organization_id: str) -> list[Membership]:
        return await self.memberships.list_members(organization_id)
