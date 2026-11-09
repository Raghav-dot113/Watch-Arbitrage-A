from __future__ import annotations

from apps.api.identity.api.schemas import (
    CurrentUserResponse,
    UserOrganizationResponse,
    UserResponse,
)
from apps.api.identity.infrastructure.repositories import (
    MembershipRepository,
    UserRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession


class IdentitySubjectNotFoundError(Exception):
    pass


class IdentityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._memberships = MembershipRepository(session)

    async def get_current_user_for_subject(self, cognito_sub: str) -> CurrentUserResponse:
        user = await self._users.get_by_cognito_sub(cognito_sub)
        if user is None:
            raise IdentitySubjectNotFoundError
        memberships = await self._memberships.list_memberships_for_user(user.id)
        return CurrentUserResponse(
            user=UserResponse.model_validate(user),
            memberships=[
                UserOrganizationResponse(
                    id=membership.organization.id,
                    name=membership.organization.name,
                    slug=membership.organization.slug,
                    role=membership.role,
                    created_at=membership.organization.created_at,
                )
                for membership in memberships
            ],
        )

    async def list_organizations_for_subject(
        self, cognito_sub: str
    ) -> list[UserOrganizationResponse]:
        current_user = await self.get_current_user_for_subject(cognito_sub)
        return current_user.memberships
