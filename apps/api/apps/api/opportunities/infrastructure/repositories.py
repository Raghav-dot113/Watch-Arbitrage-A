from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from apps.api.catalog.infrastructure.models import (
    Brand,
    Reference,
    Source,
    WatchList,
    WatchListEntry,
)
from apps.api.feedback.infrastructure.models import Feedback
from apps.api.infrastructure.pagination import decode_cursor, encode_cursor
from apps.api.infrastructure.repository import TenantRepository
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.opportunities.infrastructure.models import Opportunity
from apps.api.valuation.infrastructure.models import Valuation
from sqlalchemy import and_, func, literal, or_, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.errors import ValidationError

_MIN_SORT_VALUE = Decimal("-999999999999999999")
_SORTS = {"newest", "score_desc", "profit_desc", "roi_desc"}


@dataclass(frozen=True)
class OpportunityPage:
    items: list[RowMapping]
    next_cursor: str | None
    has_more: bool


class OpportunityRepository(TenantRepository[Opportunity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Opportunity)

    def _latest_versions(self):
        return (
            select(
                Opportunity.organization_id.label("organization_id"),
                Opportunity.listing_id.label("listing_id"),
                func.max(Opportunity.material_version).label("material_version"),
            )
            .group_by(Opportunity.organization_id, Opportunity.listing_id)
            .subquery("latest_opportunity_versions")
        )

    def _feed_query(self, user_id: str | None = None):
        latest = self._latest_versions()
        my_decision = (
            select(Feedback.decision)
            .where(
                Feedback.organization_id == Opportunity.organization_id,
                Feedback.opportunity_id == Opportunity.id,
                Feedback.user_id == user_id,
            )
            .order_by(Feedback.created_at.desc(), Feedback.id.desc())
            .limit(1)
            .scalar_subquery()
            if user_id is not None
            else literal(None)
        )
        return (
            select(
                Opportunity.id.label("id"),
                Opportunity.material_version.label("material_version"),
                Opportunity.state.label("state"),
                Opportunity.published_at.label("published_at"),
                Opportunity.organization_id.label("organization_id"),
                Opportunity.listing_id.label("listing_id"),
                Opportunity.valuation_id.label("valuation_id"),
                Reference.id.label("reference_id"),
                Brand.name.label("brand_name"),
                Reference.ref_code.label("ref_code"),
                Reference.model_name.label("model_name"),
                func.coalesce(
                    ParsedListing.listing_title,
                    Reference.model_name,
                    Reference.ref_code,
                ).label("title"),
                Source.source_key.label("source_key"),
                Source.display_name.label("source_display_name"),
                NormalizedListing.condition.label("condition"),
                NormalizedListing.set_status.label("set_status"),
                NormalizedListing.seller_geography.label("seller_geography"),
                ParsedListing.listing_price.label("listing_price"),
                ParsedListing.price_currency.label("listing_price_currency"),
                Valuation.all_in_acquisition.label("all_in_acquisition"),
                Valuation.expected_exit_price.label("expected_exit_price"),
                Valuation.exit_price_currency.label("exit_price_currency"),
                Valuation.expected_net_profit.label("expected_net_profit"),
                Valuation.roi.label("roi"),
                Opportunity.score.label("score"),
                Opportunity.positive_factors.label("positive_factors"),
                Opportunity.negative_factors.label("negative_factors"),
                my_decision.label("my_decision"),
                Valuation.confidence.label("confidence"),
                Valuation.model_version.label("valuation_version"),
                Valuation.cost_assumptions_version.label("cost_assumptions_version"),
                NormalizedListing.observation_at.label("observation_at"),
            )
            .join(
                latest,
                and_(
                    Opportunity.organization_id == latest.c.organization_id,
                    Opportunity.listing_id == latest.c.listing_id,
                    Opportunity.material_version == latest.c.material_version,
                ),
            )
            .join(Valuation, Valuation.id == Opportunity.valuation_id)
            .join(NormalizedListing, NormalizedListing.id == Opportunity.listing_id)
            .join(ParsedListing, ParsedListing.id == NormalizedListing.parsed_listing_id)
            .join(RawSnapshot, RawSnapshot.id == ParsedListing.snapshot_id)
            .join(Source, Source.id == RawSnapshot.source_id)
            .join(Reference, Reference.id == NormalizedListing.reference_id)
            .join(Brand, Brand.id == Reference.brand_id)
        )

    async def list_feed(
        self,
        organization_id: str,
        *,
        user_id: str | None = None,
        limit: int = 25,
        cursor: str | None = None,
        sort: str = "score_desc",
        state: str | None = "published",
        reference_id: str | None = None,
        brand_id: str | None = None,
        condition: str | None = None,
        min_roi: Decimal | None = None,
        min_profit: Decimal | None = None,
        min_confidence: Decimal | None = None,
        q: str | None = None,
        watch_list_id: str | None = None,
    ) -> OpportunityPage:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if sort not in _SORTS:
            raise ValueError(f"Unsupported opportunity sort: {sort}")

        statement = self._feed_query(user_id).where(Opportunity.organization_id == organization_id)
        if state is not None:
            statement = statement.where(Opportunity.state == state)
        if reference_id is not None:
            statement = statement.where(Reference.id == reference_id)
        if brand_id is not None:
            statement = statement.where(Brand.id == brand_id)
        if condition is not None:
            statement = statement.where(NormalizedListing.condition == condition)
        if min_roi is not None:
            statement = statement.where(Valuation.roi >= min_roi)
        if min_profit is not None:
            statement = statement.where(Valuation.expected_net_profit >= min_profit)
        if min_confidence is not None:
            statement = statement.where(Valuation.confidence >= min_confidence)
        if q:
            search = f"%{q}%"
            statement = statement.where(
                or_(
                    ParsedListing.listing_title.ilike(search),
                    Reference.ref_code.ilike(search),
                    Reference.model_name.ilike(search),
                    Brand.name.ilike(search),
                )
            )
        if watch_list_id is not None:
            statement = (
                statement.join(
                    WatchListEntry,
                    WatchListEntry.reference_id == Reference.id,
                )
                .join(WatchList, WatchList.id == WatchListEntry.watch_list_id)
                .where(
                    WatchList.id == watch_list_id,
                    WatchList.organization_id == organization_id,
                )
            )

        if sort == "newest":
            sort_column = func.coalesce(Opportunity.published_at, Opportunity.created_at)
        elif sort == "score_desc":
            sort_column = func.coalesce(Opportunity.score, _MIN_SORT_VALUE)
        elif sort == "profit_desc":
            sort_column = func.coalesce(Valuation.expected_net_profit, _MIN_SORT_VALUE)
        else:
            sort_column = func.coalesce(Valuation.roi, _MIN_SORT_VALUE)

        statement = statement.add_columns(sort_column.label("_cursor_sort_value"))
        if cursor is not None:
            decoded = decode_cursor(cursor)
            if decoded.sort_key != sort:
                raise ValidationError("Cursor sort does not match requested sort")
            value: Any
            if sort == "newest":
                try:
                    value = datetime.fromisoformat(decoded.sort_value)
                except ValueError as error:
                    raise ValidationError("Cursor sort value is invalid") from error
            else:
                try:
                    value = Decimal(decoded.sort_value)
                except InvalidOperation as error:
                    raise ValidationError("Cursor sort value is invalid") from error
            statement = statement.where(
                or_(
                    sort_column < value,
                    and_(sort_column == value, Opportunity.id > decoded.id),
                )
            )

        statement = statement.order_by(sort_column.desc(), Opportunity.id.asc())
        result = await self.session.execute(statement.limit(limit + 1))
        rows = list(result.mappings().all())
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = None
        if has_more and items:
            last = items[-1]
            cursor_value = last["_cursor_sort_value"]
            serialized_value = (
                cursor_value.isoformat()
                if isinstance(cursor_value, datetime)
                else str(cursor_value)
            )
            next_cursor = encode_cursor(sort, serialized_value, last["id"])
        return OpportunityPage(items, next_cursor, has_more)

    async def get_detail(
        self, opportunity_id: str, organization_id: str, user_id: str | None = None
    ) -> RowMapping | None:
        statement = self._feed_query(user_id).where(
            Opportunity.organization_id == organization_id,
            Opportunity.id == opportunity_id,
        )
        result = await self.session.execute(statement)
        return result.mappings().one_or_none()

    async def list_versions(self, listing_id: str, organization_id: str) -> list[Opportunity]:
        result = await self.session.execute(
            select(Opportunity)
            .where(
                Opportunity.organization_id == organization_id,
                Opportunity.listing_id == listing_id,
            )
            .order_by(Opportunity.material_version.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, id: str, organization_id: str) -> Opportunity | None:
        result = await self.session.execute(
            self._feed_query()
            .where(
                Opportunity.id == id,
                Opportunity.organization_id == organization_id,
            )
            .with_only_columns(Opportunity)
        )
        return result.scalar_one_or_none()
