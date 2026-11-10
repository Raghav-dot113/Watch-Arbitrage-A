from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import math
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any, TypeGuard

from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.database import get_db
from apps.api.settings import settings
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_BEARER = HTTPBearer(auto_error=False)
_MAX_TOKEN_LENGTH = 8192
_MAX_SUBJECT_LENGTH = 256
_MAX_TOKEN_LIFETIME_SECONDS = 900


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    DEALER = "dealer"
    VIEWER = "viewer"
    PLATFORM_OPS = "platform_ops"


class Permission(StrEnum):
    OPPORTUNITIES_READ = "opportunities:read"
    ALERTS_CREATE = "alerts:create"
    FEEDBACK_WRITE = "feedback:write"
    OUTCOMES_WRITE = "outcomes:write"
    MEMBERS_MANAGE = "members:manage"
    BILLING_MANAGE = "billing:manage"
    SOURCES_MANAGE = "sources:manage"
    CATALOG_MANAGE = "catalog:manage"
    JOBS_MANAGE = "jobs:manage"
    ADMIN_MANAGE = "admin:manage"


class UnauthorizedError(Exception):
    """Compatibility exception for legacy auth shims and tests."""


async def get_current_subject(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError
    if settings.auth_mode not in {"dev", "test"}:
        raise UnauthorizedError

    signing_secret = _secret_value(settings.dev_jwt_secret)
    if len(signing_secret.encode("utf-8")) < 32:
        raise UnauthorizedError

    claims = _verify_dev_token(credentials.credentials, signing_secret)
    if claims is None:
        raise UnauthorizedError
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise UnauthorizedError
    return subject


async def verify_production_token(token: str) -> str:
    if settings.auth_mode != "production":
        raise UnauthorizedError
    if not token or len(token) > _MAX_TOKEN_LENGTH:
        raise UnauthorizedError
    raise UnauthorizedError


_DEALER_PERMISSIONS = frozenset(
    {
        Permission.OPPORTUNITIES_READ,
        Permission.ALERTS_CREATE,
        Permission.FEEDBACK_WRITE,
        Permission.OUTCOMES_WRITE,
    }
)
_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: _DEALER_PERMISSIONS
    | frozenset({Permission.MEMBERS_MANAGE, Permission.BILLING_MANAGE}),
    Role.ADMIN: _DEALER_PERMISSIONS | frozenset({Permission.MEMBERS_MANAGE}),
    Role.DEALER: _DEALER_PERMISSIONS,
    Role.VIEWER: frozenset({Permission.OPPORTUNITIES_READ}),
    Role.PLATFORM_OPS: frozenset(
        {
            Permission.SOURCES_MANAGE,
            Permission.CATALOG_MANAGE,
            Permission.JOBS_MANAGE,
            Permission.ADMIN_MANAGE,
        }
    ),
}


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    user_id: str
    email: str


@dataclass(frozen=True)
class AuthContext:
    subject: str
    user_id: str
    email: str
    organization_id: str | None
    role: Role

    @property
    def permissions(self) -> frozenset[Permission]:
        return _ROLE_PERMISSIONS[self.role]

    def allows(self, permission: Permission) -> bool:
        return permission in self.permissions


def _secret_value(value: SecretStr | str) -> str:
    if hasattr(value, "get_secret_value"):
        return value.get_secret_value()
    return str(value)


def issue_dev_token(
    subject: str,
    *,
    secret: str | None = None,
    expires_in_seconds: int | None = None,
) -> str:
    """Issue a short-lived HS256 token for local development and tests."""
    if settings.environment not in {"local", "test"} or settings.auth_mode not in {"dev", "test"}:
        raise RuntimeError("Development tokens are only available in local or test dev mode")
    signing_secret = secret if secret is not None else _secret_value(settings.dev_jwt_secret)
    if len(signing_secret.encode("utf-8")) < 32:
        raise ValueError("Development JWT secret must contain at least 32 bytes")
    if not subject or len(subject) > _MAX_SUBJECT_LENGTH:
        raise ValueError("Token subject must be between 1 and 256 characters")

    lifetime = settings.auth_token_ttl_seconds if expires_in_seconds is None else expires_in_seconds
    if not 1 <= lifetime <= _MAX_TOKEN_LIFETIME_SECONDS:
        raise ValueError("Token lifetime must be between 1 and 900 seconds")

    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    claims = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": subject,
        "iat": now,
        "exp": now + lifetime,
    }
    encoded_header = _base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    encoded_claims = _base64url_encode(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{encoded_header}.{encoded_claims}".encode("ascii")
    signature = hmac.new(signing_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{signing_input.decode('ascii')}.{_base64url_encode(signature)}"


async def get_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    if settings.auth_mode not in {"dev", "test"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC authentication is not configured for this API deployment",
        )

    signing_secret = _secret_value(settings.dev_jwt_secret)
    if len(signing_secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Development authentication requires a configured 32-byte JWT secret",
        )
    claims = _verify_dev_token(credentials.credentials, signing_secret)
    if claims is None:
        raise _unauthorized()

    subject = claims["sub"]
    user_result = await session.execute(select(User).where(User.cognito_sub == subject))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise _unauthorized()

    return AuthenticatedUser(subject=subject, user_id=user.id, email=user.email)


async def get_current_auth_context(
    identity: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    organization_selector: Annotated[
        str | None, Header(alias="X-Organization-ID", max_length=128)
    ] = None,
) -> AuthContext:
    subject = identity.subject
    if subject in settings.platform_ops_subject_allowlist:
        if organization_selector is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Platform operators cannot select a tenant organization",
            )
        return AuthContext(
            subject=subject,
            user_id=identity.user_id,
            email=identity.email,
            organization_id=None,
            role=Role.PLATFORM_OPS,
        )

    membership_query = (
        select(Membership, Organization)
        .join(Organization, Organization.id == Membership.organization_id)
        .where(Membership.user_id == identity.user_id)
    )
    if organization_selector is not None:
        membership_query = membership_query.where(
            Membership.organization_id == organization_selector
        )
    memberships = (await session.execute(membership_query)).all()
    if not memberships:
        if organization_selector is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to an organization",
        )
    if len(memberships) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select an organization using X-Organization-ID",
        )

    membership, _organization = memberships[0]
    try:
        role = Role(membership.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization membership has an unsupported role",
        ) from exc
    if role is Role.PLATFORM_OPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform operator privileges require server-side allowlisting",
        )

    return AuthContext(
        subject=subject,
        user_id=identity.user_id,
        email=identity.email,
        organization_id=membership.organization_id,
        role=role,
    )


def require_permissions(
    *permissions: Permission,
) -> Callable[..., Awaitable[AuthContext]]:
    """Create a dependency that denies access unless the actor has every permission."""
    if not permissions:
        raise ValueError("At least one permission is required")

    async def authorize(
        actor: Annotated[AuthContext, Depends(get_current_auth_context)],
    ) -> AuthContext:
        if not all(actor.allows(permission) for permission in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return actor

    return authorize


def require_roles(*roles: Role) -> Callable[..., Awaitable[AuthContext]]:
    """Create a dependency that denies access unless the actor has one allowed role."""
    if not roles:
        raise ValueError("At least one role is required")

    async def authorize(
        actor: Annotated[AuthContext, Depends(get_current_auth_context)],
    ) -> AuthContext:
        if actor.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return actor

    return authorize


def _verify_dev_token(token: str, secret: str) -> dict[str, Any] | None:
    if not token or len(token) > _MAX_TOKEN_LENGTH:
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None

    try:
        header = json.loads(_base64url_decode(parts[0]))
        claims = json.loads(_base64url_decode(parts[1]))
        signature = _base64url_decode(parts[2])
    except (
        binascii.Error,
        UnicodeDecodeError,
        UnicodeEncodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None
    if not isinstance(header, dict) or header.get("alg") != "HS256":
        return None
    if not isinstance(claims, dict):
        return None

    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    now = time.time()
    subject = claims.get("sub")
    expires_at = claims.get("exp")
    issued_at = claims.get("iat")
    issuer = claims.get("iss")
    audience = claims.get("aud")
    valid_audience = audience is None or audience == settings.jwt_audience or (
        isinstance(audience, list) and settings.jwt_audience in audience
    )
    if issuer is not None and issuer != settings.jwt_issuer:
        return None
    if not valid_audience:
        return None
    if (
        not isinstance(subject, str)
        or not subject
        or len(subject) > _MAX_SUBJECT_LENGTH
        or not _is_numeric_date(expires_at)
        or expires_at <= now
    ):
        return None
    if issued_at is not None:
        if not _is_numeric_date(issued_at) or issued_at > now:
            return None
        if expires_at - issued_at > _MAX_TOKEN_LIFETIME_SECONDS:
            return None

    not_before = claims.get("nbf")
    if not_before is not None and (not _is_numeric_date(not_before) or not_before > now):
        return None
    return claims


def _is_numeric_date(value: object) -> TypeGuard[int | float]:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.b64decode(padded, altchars=b"-_", validate=True)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
