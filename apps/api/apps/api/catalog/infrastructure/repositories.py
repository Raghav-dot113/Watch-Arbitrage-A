from __future__ import annotations

from dataclasses import dataclass

from apps.api.catalog.infrastructure.models import (
    Alias,
    Brand,
    Reference,
    Source,
    WatchList,
)
from apps.api.infrastructure.pagination import decode_cursor, encode_cursor
from apps.api.infrastructure.repository import BaseRepository
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


@dataclass(frozen=True)
class ReferencePage:
    items: list[Reference]
    next_cursor: str | None
    has_more: bool


class BrandRepository(BaseRepository[Brand]):
    async def list_all_ordered(self) -> list[Brand]:
        result = await self.session.execute(
            select(Brand).order_by(Brand.name, Brand.id)
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Brand | None:
        result = await self.session.execute(
            select(Brand).where(Brand.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Brand | None:
        result = await self.session.execute(
            select(Brand).where(Brand.slug == slug)
        )
        return result.scalar_one_or_none()


class SourceRepository(BaseRepository[Source]):
    pass


class ReferenceRepository(BaseRepository[Reference]):
    async def get_by_brand_and_ref_code(
        self, brand_id: str, ref_code: str
    ) -> Reference | None:
        result = await self.session.execute(
            select(Reference)
            .where(Reference.brand_id == brand_id)
            .where(Reference.ref_code == ref_code)
        )
        return result.scalar_one_or_none()

    async def get_with_details(self, reference_id: str) -> Reference | None:
        result = await self.session.execute(
            select(Reference)
            .options(joinedload(Reference.brand), joinedload(Reference.aliases))
            .where(Reference.id == reference_id, Reference.is_active.is_(True))
        )
        return result.unique().scalar_one_or_none()

    async def get_active_ids(self, reference_ids: set[str]) -> set[str]:
        if not reference_ids:
            return set()
        result = await self.session.execute(
            select(Reference.id).where(
                Reference.id.in_(reference_ids),
                Reference.is_active.is_(True),
            )
        )
        return set(result.scalars().all())

    async def search(
        self,
        *,
        q: str | None = None,
        active_only: bool = True,
        brand_id: str | None = None,
        cursor: str | None = None,
        limit: int = 25,
    ) -> ReferencePage:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        statement = select(Reference)
        if active_only:
            statement = statement.where(Reference.is_active.is_(True))
        if q:
            search_term = f"%{q}%"
            statement = statement.where(
                or_(
                    Reference.ref_code.ilike(search_term),
                    Reference.model_name.ilike(search_term),
                    Reference.generation.ilike(search_term),
                )
            )
        if brand_id is not None:
            statement = statement.where(Reference.brand_id == brand_id)
        if cursor is not None:
            decoded = decode_cursor(cursor)
            if decoded.sort_key != "ref_code_asc":
                from chronoarb.domain.errors import ValidationError

                raise ValidationError("Cursor sort does not match reference search")
            statement = statement.where(
                or_(
                    Reference.ref_code > decoded.sort_value,
                    and_(
                        Reference.ref_code == decoded.sort_value,
                        Reference.id > decoded.id,
                    ),
                )
            )
        result = await self.session.execute(
            statement.order_by(Reference.ref_code, Reference.id).limit(limit + 1)
        )
        rows = list(result.scalars().all())
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = encode_cursor("ref_code_asc", last.ref_code, last.id)
        return ReferencePage(items, next_cursor, has_more)

    async def list_references(self, *, cursor: str | None = None, limit: int = 25) -> ReferencePage:
        return await self.search(cursor=cursor, limit=limit)


class WatchListRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_org(
        self,
        model_cls: type[WatchList],
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WatchList]:
        if model_cls is not WatchList:
            raise TypeError("WatchListRepository only supports WatchList records")
        result = await self.session.execute(
            select(WatchList)
            .options(joinedload(WatchList.entries))
            .where(WatchList.organization_id == organization_id)
            .order_by(WatchList.created_at.desc(), WatchList.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    async def get_by_id(self, id: str, organization_id: str) -> WatchList | None:
        result = await self.session.execute(
            select(WatchList)
            .options(joinedload(WatchList.entries))
            .where(
                WatchList.id == id,
                WatchList.organization_id == organization_id,
            )
        )
        return result.unique().scalar_one_or_none()

    async def list_with_entries(self, organization_id: str) -> list[WatchList]:
        result = await self.session.execute(
            select(WatchList)
            .options(joinedload(WatchList.entries))
            .where(WatchList.organization_id == organization_id)
            .order_by(WatchList.created_at.desc(), WatchList.id.desc())
        )
        return list(result.unique().scalars().all())


class AliasRepository(BaseRepository[Alias]):
    async def find_by_alias_text(self, alias_text: str) -> list[Alias]:
        result = await self.session.execute(
            select(Alias).where(Alias.alias_text == alias_text)
        )
        return list(result.scalars().all())
