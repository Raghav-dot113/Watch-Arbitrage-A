from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from apps.api.opportunities.api.schemas import (
    OpportunityDetailResponse,
    OpportunityFeedItem,
    OpportunityListingResponse,
    OpportunityValuationResponse,
)
from apps.api.opportunities.infrastructure.repositories import OpportunityRepository
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession


class OpportunityService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = OpportunityRepository(session)

    async def list_feed(
        self,
        organization_id: str,
        *,
        user_id: str,
        limit: int,
        cursor: str | None,
        sort: str,
        state: str | None,
        reference_id: str | None,
        brand_id: str | None,
        condition: str | None,
        min_roi: Decimal | None,
        min_profit: Decimal | None,
        min_confidence: Decimal | None,
        q: str | None,
        watch_list_id: str | None,
    ) -> tuple[list[OpportunityFeedItem], str | None, bool]:
        page = await self.repository.list_feed(
            organization_id,
            user_id=user_id,
            limit=limit,
            cursor=cursor,
            sort=sort,
            state=state,
            reference_id=reference_id,
            brand_id=brand_id,
            condition=condition,
            min_roi=min_roi,
            min_profit=min_profit,
            min_confidence=min_confidence,
            q=q,
            watch_list_id=watch_list_id,
        )
        return (
            [self._feed_item(row) for row in page.items],
            page.next_cursor,
            page.has_more,
        )

    async def get_detail(
        self,
        opportunity_id: str,
        organization_id: str,
        *,
        user_id: str,
    ) -> OpportunityDetailResponse | None:
        row = await self.repository.get_detail(opportunity_id, organization_id, user_id)
        if row is None:
            return None
        return OpportunityDetailResponse(
            **self._feed_item(row).model_dump(),
            observation_at=self._datetime(row["observation_at"]),
        )

    def _feed_item(self, row: RowMapping) -> OpportunityFeedItem:
        observation_at = self._datetime(row["observation_at"])
        valuation = OpportunityValuationResponse(
            id=row["valuation_id"],
            listing_id=row["listing_id"],
            model_version=row["valuation_version"],
            config_version=row["config_version"],
            cost_assumptions_version=row["cost_assumptions_version"],
            expected_exit_price=row["expected_exit_price"],
            exit_price_currency=row["exit_price_currency"],
            all_in_acquisition=row["all_in_acquisition"],
            expected_net_resale=row["expected_net_resale"],
            expected_net_profit=row["expected_net_profit"],
            roi=row["roi"],
            low_estimate=row["low_estimate"],
            high_estimate=row["high_estimate"],
            confidence=row["confidence"],
            comparable_count=row["comparable_count"],
            sample_dispersion=row["sample_dispersion"],
            cost_breakdown=row["cost_breakdown"],
            adjustment_details=row["adjustment_details"],
            risk_reserve_details=row["risk_reserve_details"],
            created_at=row["valuation_created_at"],
        )
        listing = OpportunityListingResponse(
            id=row["listing_id"],
            title=row["title"],
            description=row["listing_description"],
            external_url=row["external_url"],
            listing_price=row["listing_price"],
            listing_price_currency=row["listing_price_currency"],
            normalized_price=row["normalized_price"],
            normalized_currency=row["normalized_currency"],
            condition=row["condition"],
            set_status=row["set_status"],
            seller_geography=row["seller_geography"],
            listed_at=row["listed_at"],
            reference_id=row["reference_id"],
            brand_name=row["brand_name"],
            ref_code=row["ref_code"],
            model_name=row["model_name"],
            generation=row["generation"],
            reference_attributes=row["reference_attributes"],
            parsed_attributes=row["parsed_attributes"],
            source_key=row["source_key"],
            source_display_name=row["source_display_name"],
            match_confidence=row["match_confidence"],
            match_method=row["match_method"],
            match_features=row["match_features"],
            fx_rate=row["fx_rate"],
            fx_source=row["fx_source"],
            fx_date=row["fx_date"],
        )
        return OpportunityFeedItem(
            id=row["id"],
            organization_id=row["organization_id"],
            listing_id=row["listing_id"],
            valuation_id=row["valuation_id"],
            material_version=row["material_version"],
            score=row["score"],
            state=row["state"],
            positive_factors=row["positive_factors"],
            negative_factors=row["negative_factors"],
            published_at=row["published_at"],
            state_changed_at=row["state_changed_at"],
            created_at=row["created_at"],
            data_age_seconds=self._data_age_seconds(observation_at),
            confidence=row["confidence"],
            valuation_version=row["valuation_version"],
            cost_assumptions_version=row["cost_assumptions_version"],
            my_decision=row["my_decision"],
            listing=listing,
            valuation=valuation,
        )

    @staticmethod
    def _datetime(value: object) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError("Opportunity observation timestamp is missing or invalid")
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @classmethod
    def _data_age_seconds(cls, observation_at: object) -> int:
        age = (datetime.now(UTC) - cls._datetime(observation_at)).total_seconds()
        return max(0, int(age))
