from __future__ import annotations

import pytest

from chronoarb.domain.permissions import Permission, has_permission

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
    "platform_ops": frozenset({"admin:manage", "sources:manage", "jobs:manage"}),
}
PERMISSIONS: tuple[Permission, ...] = (
    "opportunities:read",
    "alerts:create",
    "feedback:write",
    "outcomes:write",
    "members:manage",
    "billing:manage",
    "admin:manage",
    "sources:manage",
    "jobs:manage",
)


@pytest.mark.parametrize(
    ("role", "permission"),
    [(role, permission) for role in ROLE_PERMISSIONS for permission in PERMISSIONS],
)
def test_role_permission_matrix(role: str, permission: Permission) -> None:
    assert has_permission(role, permission) is (permission in ROLE_PERMISSIONS[role])


def test_unknown_role_is_denied() -> None:
    assert not has_permission("unknown", "opportunities:read")
