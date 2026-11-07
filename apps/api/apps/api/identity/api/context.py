from __future__ import annotations

from dataclasses import dataclass

from apps.api.identity.api.auth import UnauthorizedError, get_current_subject
from apps.api.identity.infrastructure.repositories import MembershipRepository, UserRepository
from apps.api.infrastructure.database import get_db
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

_organization_header = Header(alias="X-Organization-ID")
_subject_dependency = Depends(get_current_subject)
_database_dependency = Depends(get_db)


@dataclass(frozen=True)
class OrganizationContext:
    organization_id: str
    user_id: str
    role: str


async def get_organization_context(
    organization_id: str = _organization_header,
    subject: str = _subject_dependency,
    session: AsyncSession = _database_dependency,
) -> OrganizationContext:
    if not organization_id:
        raise UnauthorizedError
    user = await UserRepository(session).get_by_cognito_sub(subject)
    if user is None:
        raise UnauthorizedError
    membership = await MembershipRepository(session).get_by_user_and_org(
        user.id,
        organization_id,
    )
    if membership is None:
        raise UnauthorizedError
    return OrganizationContext(
        organization_id=organization_id,
        user_id=user.id,
        role=membership.role,
    )
