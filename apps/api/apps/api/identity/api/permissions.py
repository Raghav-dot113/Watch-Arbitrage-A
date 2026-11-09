from __future__ import annotations

from collections.abc import Awaitable, Callable

from apps.api.identity.api.context import OrganizationContext, get_organization_context
from fastapi import Depends, HTTPException

from chronoarb.domain.permissions import Permission, has_permission

_organization_context_dependency = Depends(get_organization_context)


def require_permission(
    permission: Permission,
) -> Callable[..., Awaitable[OrganizationContext]]:
    async def dependency(
        context: OrganizationContext = _organization_context_dependency,
    ) -> OrganizationContext:
        if not has_permission(context.role, permission):
            raise HTTPException(status_code=403, detail="Insufficient organization permission")
        return context

    return dependency
