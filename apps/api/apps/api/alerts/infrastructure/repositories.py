from __future__ import annotations

from apps.api.alerts.infrastructure.models import AlertRule
from apps.api.infrastructure.repository import TenantRepository
from apps.api.pagination import Page, decode_cursor, encode_cursor
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class AlertRuleRepository(TenantRepository[AlertRule]):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, AlertRule)

    async def list_for_org(
        self,
        organization_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> Page[AlertRule]:
        query = (
            select(AlertRule)
            .where(AlertRule.organization_id == organization_id)
            .order_by(AlertRule.created_at.desc(), AlertRule.id.desc())
        )
        if cursor is not None:
            cursor_created_at, cursor_id = decode_cursor(cursor)
            query = query.where(
                or_(
                    AlertRule.created_at < cursor_created_at,
                    and_(
                        AlertRule.created_at == cursor_created_at,
                        AlertRule.id < cursor_id,
                    ),
                )
            )
        result = await self.session.execute(query.limit(limit + 1))
        rows = list(result.scalars().all())
        items = rows[:limit]
        has_more = len(rows) > limit
        next_cursor = None
        if has_more and items:
            next_cursor = encode_cursor(items[-1].created_at, items[-1].id)
        return Page(items=items, next_cursor=next_cursor, has_more=has_more)
