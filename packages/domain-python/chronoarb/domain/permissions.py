from __future__ import annotations

from typing import Literal

Permission = Literal[
    "opportunities:read",
    "alerts:create",
    "feedback:write",
    "outcomes:write",
    "members:manage",
    "billing:manage",
    "admin:manage",
    "sources:manage",
    "jobs:manage",
]

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "viewer": frozenset({"opportunities:read"}),
    "dealer": frozenset(
        {
            "opportunities:read",
            "alerts:create",
            "feedback:write",
            "outcomes:write",
        }
    ),
    "admin": frozenset(
        {
            "opportunities:read",
            "alerts:create",
            "feedback:write",
            "outcomes:write",
            "members:manage",
        }
    ),
    "owner": frozenset(
        {
            "opportunities:read",
            "alerts:create",
            "feedback:write",
            "outcomes:write",
            "members:manage",
            "billing:manage",
        }
    ),
    "platform_ops": frozenset(
        {
            "admin:manage",
            "sources:manage",
            "jobs:manage",
        }
    ),
}


def has_permission(role: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
