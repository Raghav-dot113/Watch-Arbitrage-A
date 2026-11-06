from __future__ import annotations

from apps.api.infrastructure.repository import BaseRepository
from apps.api.listings.infrastructure.models import (
    DuplicateGroup,
    DuplicateGroupMember,
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from sqlalchemy import select


class ListingRepository(BaseRepository[RawSnapshot]):
    async def get_snapshot(
        self,
        source_id: str,
        external_id: str,
        adapter_version: str,
        checksum: str,
    ) -> RawSnapshot | None:
        result = await self.session.execute(
            select(RawSnapshot).where(
                RawSnapshot.source_id == source_id,
                RawSnapshot.external_id == external_id,
                RawSnapshot.adapter_version == adapter_version,
                RawSnapshot.checksum == checksum,
            )
        )
        return result.scalar_one_or_none()

    async def get_parsed_listing(self, snapshot_id: str) -> ParsedListing | None:
        result = await self.session.execute(
            select(ParsedListing).where(ParsedListing.snapshot_id == snapshot_id)
        )
        return result.scalar_one_or_none()

    async def get_normalized_listing(self, parsed_listing_id: str) -> NormalizedListing | None:
        result = await self.session.execute(
            select(NormalizedListing).where(
                NormalizedListing.parsed_listing_id == parsed_listing_id
            )
        )
        return result.scalar_one_or_none()


class DuplicateRepository(BaseRepository[DuplicateGroup]):
    async def get_group(self, group_id: str) -> DuplicateGroup | None:
        return await self.session.get(DuplicateGroup, group_id)

    async def list_members(self, group_id: str) -> list[DuplicateGroupMember]:
        result = await self.session.execute(
            select(DuplicateGroupMember)
            .where(DuplicateGroupMember.group_id == group_id)
            .order_by(DuplicateGroupMember.created_at, DuplicateGroupMember.id)
        )
        return list(result.scalars().all())
