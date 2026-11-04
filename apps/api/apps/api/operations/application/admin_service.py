from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.api.catalog.infrastructure.models import Reference, Source
from apps.api.duplicates.infrastructure.models import DuplicateGroup, DuplicateGroupMember
from apps.api.listings.infrastructure.models import NormalizedListing, ParsedListing, RawSnapshot
from apps.api.operations.application.audit import record_audit_event
from apps.api.operations.infrastructure.models import AuditEvent, FeatureFlag
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class AdminResourceNotFoundError(Exception):
    pass


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_sources(self, *, limit: int) -> list[dict[str, Any]]:
        last_fetched = (
            select(func.max(RawSnapshot.fetched_at))
            .where(RawSnapshot.source_id == Source.id)
            .correlate(Source)
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(Source, last_fetched.label("last_fetched_at"))
            .order_by(Source.source_key, Source.id)
            .limit(limit)
        )
        return [
            {
                "id": source.id,
                "source_key": source.source_key,
                "display_name": source.display_name,
                "adapter_version": source.adapter_version,
                "access_mode": source.access_mode,
                "is_enabled": source.is_enabled,
                "health_status": "unknown",
                "last_fetched_at": fetched_at,
            }
            for source, fetched_at in result.all()
        ]

    async def set_source_enabled(
        self,
        source_id: str,
        is_enabled: bool,
        user_id: str,
        *,
        trace_id: str,
    ) -> dict[str, Any]:
        result = await self.session.execute(
            select(Source).where(Source.id == source_id).with_for_update(of=Source)
        )
        source = result.scalar_one_or_none()
        if source is None:
            raise AdminResourceNotFoundError
        source.is_enabled = is_enabled
        last_fetched_at = await self.session.scalar(
            select(func.max(RawSnapshot.fetched_at)).where(RawSnapshot.source_id == source.id)
        )
        await record_audit_event(
            self.session,
            user_id=user_id,
            action="admin.source_enabled" if is_enabled else "admin.source_disabled",
            resource_type="source",
            resource_id=source.id,
            details={"is_enabled": is_enabled},
            trace_id=trace_id,
        )
        await self.session.commit()
        return {
            "id": source.id,
            "source_key": source.source_key,
            "display_name": source.display_name,
            "adapter_version": source.adapter_version,
            "access_mode": source.access_mode,
            "is_enabled": source.is_enabled,
            "health_status": "unknown",
            "last_fetched_at": last_fetched_at,
        }

    async def list_feature_flags(self, *, limit: int) -> list[FeatureFlag]:
        result = await self.session.execute(
            select(FeatureFlag).order_by(FeatureFlag.key, FeatureFlag.id).limit(limit)
        )
        return list(result.scalars().all())

    async def update_feature_flag(
        self,
        flag_id: str,
        patch: dict[str, Any],
        user_id: str,
        *,
        trace_id: str,
    ) -> FeatureFlag:
        result = await self.session.execute(
            select(FeatureFlag).where(FeatureFlag.id == flag_id).with_for_update(of=FeatureFlag)
        )
        flag = result.scalar_one_or_none()
        if flag is None:
            raise AdminResourceNotFoundError
        if "enabled" in patch:
            flag.enabled = patch["enabled"]
        if "organization_ids" in patch:
            organization_ids = patch["organization_ids"]
            if organization_ids is not None and len(organization_ids) != len(set(organization_ids)):
                raise ValueError("organization_ids must be unique")
            flag.organization_ids = organization_ids
        if "rollout_pct" in patch:
            flag.rollout_pct = patch["rollout_pct"]
        if "expires_at" in patch:
            flag.expires_at = patch["expires_at"]
        await record_audit_event(
            self.session,
            user_id=user_id,
            action="admin.feature_flag_updated",
            resource_type="feature_flag",
            resource_id=flag.id,
            details={"fields": sorted(patch)},
            trace_id=trace_id,
        )
        await self.session.commit()
        return flag

    async def list_audit_events(self, *, limit: int) -> list[AuditEvent]:
        result = await self.session.execute(
            select(AuditEvent)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_unmatched_listings(self, *, limit: int) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(
                NormalizedListing.id,
                NormalizedListing.reference_id,
                Source.source_key,
                ParsedListing.listing_title,
                ParsedListing.external_url,
                NormalizedListing.match_method,
                NormalizedListing.observation_at,
            )
            .join(ParsedListing, ParsedListing.id == NormalizedListing.parsed_listing_id)
            .join(RawSnapshot, RawSnapshot.id == ParsedListing.snapshot_id)
            .join(Source, Source.id == RawSnapshot.source_id)
            .where(NormalizedListing.match_confidence.is_(None))
            .order_by(NormalizedListing.observation_at.desc(), NormalizedListing.id.desc())
            .limit(limit)
        )
        return [
            {
                "id": row.id,
                "reference_id": row.reference_id,
                "source_key": row.source_key,
                "title": row.listing_title,
                "external_url": row.external_url,
                "match_method": row.match_method,
                "observation_at": row.observation_at,
            }
            for row in result.all()
        ]

    async def resolve_unmatched_listing(
        self,
        listing_id: str,
        reference_id: str,
        user_id: str,
        *,
        trace_id: str,
    ) -> dict[str, Any]:
        result = await self.session.execute(
            select(NormalizedListing)
            .where(
                NormalizedListing.id == listing_id,
                NormalizedListing.match_confidence.is_(None),
            )
            .with_for_update(of=NormalizedListing)
        )
        listing = result.scalar_one_or_none()
        if listing is None:
            raise AdminResourceNotFoundError
        details = await self.session.execute(
            select(Source.source_key, ParsedListing.listing_title, ParsedListing.external_url)
            .join(RawSnapshot, RawSnapshot.source_id == Source.id)
            .join(ParsedListing, ParsedListing.snapshot_id == RawSnapshot.id)
            .where(ParsedListing.id == listing.parsed_listing_id)
        )
        listing_details = details.one()
        reference = await self.session.get(Reference, reference_id)
        if reference is None or not reference.is_active:
            raise ValueError("reference_id must identify an active catalog reference")
        listing.reference_id = reference_id
        listing.match_method = "manual_review"
        listing.match_confidence = Decimal("1.0000")
        listing.match_features = {"resolution": "operator"}
        await record_audit_event(
            self.session,
            user_id=user_id,
            action="admin.unmatched_listing_resolved",
            resource_type="normalized_listing",
            resource_id=listing.id,
            details={"reference_id": reference_id},
            trace_id=trace_id,
        )
        await self.session.commit()
        return {
            "id": listing.id,
            "reference_id": listing.reference_id,
            "source_key": listing_details.source_key,
            "title": listing_details.listing_title,
            "external_url": listing_details.external_url,
            "match_method": listing.match_method,
            "observation_at": listing.observation_at,
        }

    async def list_duplicate_groups(self, *, limit: int) -> list[dict[str, Any]]:
        group_ids = (
            select(DuplicateGroup.id)
            .order_by(DuplicateGroup.created_at.desc(), DuplicateGroup.id)
            .limit(limit)
            .subquery()
        )
        result = await self.session.execute(
            select(DuplicateGroup, DuplicateGroupMember.listing_id)
            .join(group_ids, group_ids.c.id == DuplicateGroup.id)
            .outerjoin(DuplicateGroupMember, DuplicateGroupMember.group_id == DuplicateGroup.id)
            .order_by(DuplicateGroup.created_at.desc(), DuplicateGroup.id, DuplicateGroupMember.id)
        )
        groups: dict[str, dict[str, Any]] = {}
        for group, listing_id in result.all():
            if group.id not in groups:
                groups[group.id] = {
                    "id": group.id,
                    "representative_id": group.representative_id,
                    "method": group.method,
                    "confidence": group.confidence,
                    "listing_ids": [],
                    "created_at": group.created_at,
                }
            if listing_id is not None:
                groups[group.id]["listing_ids"].append(listing_id)
        return list(groups.values())[:limit]
