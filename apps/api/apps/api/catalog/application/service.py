from __future__ import annotations

from apps.api.catalog.infrastructure.models import (
    Brand,
    Reference,
    WatchList,
    WatchListEntry,
)
from apps.api.catalog.infrastructure.repositories import (
    BrandRepository,
    ReferencePage,
    ReferenceRepository,
    WatchListRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


class WatchListNotFoundError(Exception):
    pass


class InvalidWatchListReferencesError(Exception):
    pass


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.brands = BrandRepository(session)
        self.references = ReferenceRepository(session)
        self.watch_lists = WatchListRepository(session)

    async def list_brands(self) -> list[Brand]:
        return await self.brands.list_all_ordered()

    async def search_references(
        self,
        *,
        q: str | None,
        brand_id: str | None,
        cursor: str | None,
        limit: int,
    ) -> ReferencePage:
        return await self.references.search(
            q=q,
            brand_id=brand_id,
            cursor=cursor,
            limit=limit,
        )

    async def get_reference(self, reference_id: str) -> Reference | None:
        return await self.references.get_with_details(reference_id)

    async def list_watch_lists(self, organization_id: str) -> list[WatchList]:
        return await self.watch_lists.list_with_entries(organization_id)

    async def create_watch_list(
        self,
        organization_id: str,
        *,
        name: str,
        reference_ids: list[str],
    ) -> WatchList:
        await self._validate_reference_ids(reference_ids)
        watch_list = WatchList(
            id=generate_ulid("wl"),
            organization_id=organization_id,
            name=name,
        )
        self.session.add(watch_list)
        await self.session.flush()
        entries = [
            WatchListEntry(
                id=generate_ulid("wle"),
                watch_list=watch_list,
                reference_id=reference_id,
            )
            for reference_id in reference_ids
        ]
        self.session.add_all(entries)
        await self.session.commit()
        return await self.watch_lists.get_by_id(watch_list.id, organization_id) or watch_list

    async def update_watch_list(
        self,
        organization_id: str,
        watch_list_id: str,
        *,
        name: str,
        reference_ids: list[str],
    ) -> WatchList:
        watch_list = await self.watch_lists.get_by_id(watch_list_id, organization_id)
        if watch_list is None:
            raise WatchListNotFoundError
        await self._validate_reference_ids(reference_ids)
        for entry in list(watch_list.entries):
            watch_list.entries.remove(entry)
            await self.session.delete(entry)
        watch_list.name = name
        entries = [
            WatchListEntry(
                id=generate_ulid("wle"),
                watch_list=watch_list,
                reference_id=reference_id,
            )
            for reference_id in reference_ids
        ]
        self.session.add_all(entries)
        await self.session.commit()
        return await self.watch_lists.get_by_id(watch_list.id, organization_id) or watch_list

    async def delete_watch_list(self, organization_id: str, watch_list_id: str) -> None:
        watch_list = await self.watch_lists.get_by_id(watch_list_id, organization_id)
        if watch_list is None:
            raise WatchListNotFoundError
        for entry in watch_list.entries:
            await self.session.delete(entry)
        await self.session.delete(watch_list)
        await self.session.commit()

    async def _validate_reference_ids(self, reference_ids: list[str]) -> None:
        if len(set(reference_ids)) != len(reference_ids):
            raise InvalidWatchListReferencesError
        active_ids = await self.references.get_active_ids(set(reference_ids))
        if active_ids != set(reference_ids):
            raise InvalidWatchListReferencesError
