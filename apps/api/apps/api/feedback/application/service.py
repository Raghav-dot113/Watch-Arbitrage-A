from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from apps.api.feedback.api.schemas import (
    FeedbackCreateRequest,
    TradeOutcomeCreateRequest,
)
from apps.api.feedback.infrastructure.models import Feedback, TradeOutcome
from apps.api.feedback.infrastructure.repositories import (
    FeedbackRepository,
    TradeOutcomeRepository,
)
from apps.api.infrastructure.idempotency import make_idempotency_identity
from apps.api.operations.application.audit import record_audit_event
from apps.api.opportunities.domain.state_machine import (
    InvalidOpportunityTransitionError,
    OpportunityState,
    transition_opportunity_state,
)
from apps.api.opportunities.infrastructure.repositories import OpportunityRepository
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


class OpportunityNotFoundError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


class TradeOutcomeStateError(Exception):
    pass


@dataclass(frozen=True)
class FeedbackResult:
    feedback: Feedback
    opportunity_state: OpportunityState
    created: bool


@dataclass(frozen=True)
class TradeOutcomeResult:
    outcome: TradeOutcome
    created: bool


class FeedbackService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.feedbacks = FeedbackRepository(session)
        self.outcomes = TradeOutcomeRepository(session)
        self.opportunities = OpportunityRepository(session)

    async def list_activity(self, organization_id: str, *, limit: int) -> list[dict[str, Any]]:
        feedbacks = await self.feedbacks.list_by_org(organization_id, limit=limit)
        outcomes = await self.outcomes.list_by_org(organization_id, limit=limit)
        entries: list[dict[str, Any]] = [
            {
                "id": item.id,
                "event_type": "feedback",
                "user_id": item.user_id,
                "opportunity_id": item.opportunity_id,
                "reference_id": None,
                "decision": item.decision,
                "notes": item.notes,
                "acquisition_price": None,
                "acquisition_currency": None,
                "resale_price": None,
                "resale_currency": None,
                "actual_profit": None,
                "days_to_sell": None,
                "created_at": item.created_at,
            }
            for item in feedbacks
        ]
        entries.extend(
            {
                "id": item.id,
                "event_type": "outcome",
                "user_id": item.user_id,
                "opportunity_id": item.opportunity_id,
                "reference_id": item.reference_id,
                "decision": None,
                "notes": None,
                "acquisition_price": item.acquisition_price,
                "acquisition_currency": item.acquisition_currency,
                "resale_price": item.resale_price,
                "resale_currency": item.resale_currency,
                "actual_profit": item.actual_profit,
                "days_to_sell": item.days_to_sell,
                "created_at": item.created_at,
            }
            for item in outcomes
        )
        entries.sort(key=lambda item: (item["created_at"], item["id"]), reverse=True)
        return entries[:limit]

    async def list_outcomes(self, organization_id: str, *, limit: int) -> list[TradeOutcome]:
        return await self.outcomes.list_by_org(organization_id, limit=limit)

    async def record_feedback(
        self,
        opportunity_id: str,
        organization_id: str,
        user_id: str,
        idempotency_key: str,
        payload: FeedbackCreateRequest,
        *,
        trace_id: str,
    ) -> FeedbackResult:
        request_payload = payload.model_dump(mode="json")
        identity = make_idempotency_identity(
            key=idempotency_key,
            organization_id=organization_id,
            user_id=user_id,
            operation=f"feedback.create:{opportunity_id}",
            payload=request_payload,
        )
        existing = await self.feedbacks.get_by_idempotency_key(
            identity.storage_key, organization_id, user_id
        )
        if existing is not None:
            return self._feedback_replay(existing, payload)

        opportunity = await self.opportunities.get_current_for_update(
            opportunity_id, organization_id
        )
        if opportunity is None:
            raise OpportunityNotFoundError
        existing = await self.feedbacks.get_by_idempotency_key(
            identity.storage_key, organization_id, user_id
        )
        if existing is not None:
            return self._feedback_replay(existing, payload)
        try:
            new_state = transition_opportunity_state(
                opportunity.state,
                payload.decision,
            )
        except InvalidOpportunityTransitionError:
            raise

        opportunity.state = new_state
        opportunity.state_changed_at = datetime.now(UTC)
        feedback = Feedback(
            id=generate_ulid("fbk"),
            organization_id=organization_id,
            user_id=user_id,
            opportunity_id=opportunity.id,
            decision=payload.decision,
            notes=payload.notes,
            idempotency_key=identity.storage_key,
        )
        try:
            self.session.add(feedback)
            await record_audit_event(
                self.session,
                organization_id=organization_id,
                user_id=user_id,
                action="opportunity.feedback_recorded",
                resource_type="opportunity",
                resource_id=opportunity.id,
                details={
                    "feedback_id": feedback.id,
                    "decision": payload.decision,
                    "previous_state": "published",
                    "new_state": new_state,
                },
                trace_id=trace_id,
            )
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            if not self._is_idempotency_conflict(error, "uq_feedbacks_idempotency_key"):
                raise
            existing = await self.feedbacks.get_by_idempotency_key(
                identity.storage_key, organization_id, user_id
            )
            if existing is None:
                raise
            return self._feedback_replay(existing, payload)
        return FeedbackResult(feedback, new_state, True)

    async def list_history(
        self,
        opportunity_id: str,
        organization_id: str,
    ) -> list[dict[str, Any]]:
        opportunity = await self.opportunities.get_any_by_id(opportunity_id, organization_id)
        if opportunity is None:
            raise OpportunityNotFoundError
        versions = await self.opportunities.list_version_summaries(
            opportunity.listing_id, organization_id
        )
        return [self._history_item(version) for version in versions]

    @staticmethod
    def _history_item(row: RowMapping) -> dict[str, Any]:
        return {
            "id": row["id"],
            "listing_id": row["listing_id"],
            "material_version": row["material_version"],
            "state": row["state"],
            "score": row["score"],
            "published_at": row["published_at"],
            "state_changed_at": row["state_changed_at"],
            "created_at": row["created_at"],
            "valuation": {
                "id": row["valuation_id"],
                "model_version": row["model_version"],
                "cost_assumptions_version": row["cost_assumptions_version"],
                "expected_exit_price": row["expected_exit_price"],
                "exit_price_currency": row["exit_price_currency"],
                "expected_net_profit": row["expected_net_profit"],
                "roi": row["roi"],
                "confidence": row["confidence"],
            },
        }

    async def record_trade_outcome(
        self,
        opportunity_id: str,
        organization_id: str,
        user_id: str,
        idempotency_key: str,
        payload: TradeOutcomeCreateRequest,
        *,
        trace_id: str,
    ) -> TradeOutcomeResult:
        request_payload = payload.model_dump(mode="json")
        identity = make_idempotency_identity(
            key=idempotency_key,
            organization_id=organization_id,
            user_id=user_id,
            operation=f"trade_outcome.create:{opportunity_id}",
            payload=request_payload,
        )
        existing = await self.outcomes.get_by_idempotency_key(
            identity.storage_key, organization_id, user_id
        )
        if existing is not None:
            return self._outcome_replay(existing, payload)

        opportunity = await self.opportunities.get_current_for_update(
            opportunity_id, organization_id
        )
        if opportunity is None:
            raise OpportunityNotFoundError
        if opportunity.state != "purchased":
            raise TradeOutcomeStateError
        reference_id = await self.opportunities.get_reference_id(opportunity.id, organization_id)
        if reference_id is None:
            raise OpportunityNotFoundError

        outcome = TradeOutcome(
            id=generate_ulid("out"),
            organization_id=organization_id,
            user_id=user_id,
            opportunity_id=opportunity.id,
            reference_id=reference_id,
            acquisition_price=payload.acquisition_price,
            acquisition_currency=payload.acquisition_currency,
            resale_price=payload.resale_price,
            resale_currency=payload.resale_currency,
            actual_profit=payload.actual_profit,
            days_to_sell=payload.days_to_sell,
            idempotency_key=identity.storage_key,
        )
        try:
            self.session.add(outcome)
            await record_audit_event(
                self.session,
                organization_id=organization_id,
                user_id=user_id,
                action="trade_outcome.recorded",
                resource_type="trade_outcome",
                resource_id=outcome.id,
                details={"opportunity_id": opportunity.id, "reference_id": reference_id},
                trace_id=trace_id,
            )
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            if not self._is_idempotency_conflict(error, "uq_trade_outcomes_idempotency_key"):
                raise
            existing = await self.outcomes.get_by_idempotency_key(
                identity.storage_key, organization_id, user_id
            )
            if existing is None:
                raise
            return self._outcome_replay(existing, payload)
        return TradeOutcomeResult(outcome, True)

    @staticmethod
    def _feedback_replay(
        existing: Feedback,
        payload: FeedbackCreateRequest,
    ) -> FeedbackResult:
        if existing.decision != payload.decision or existing.notes != payload.notes:
            raise IdempotencyConflictError
        try:
            state = transition_opportunity_state("published", payload.decision)
        except InvalidOpportunityTransitionError:
            raise
        return FeedbackResult(existing, state, False)

    @staticmethod
    def _outcome_replay(
        existing: TradeOutcome,
        payload: TradeOutcomeCreateRequest,
    ) -> TradeOutcomeResult:
        stored_values = (
            existing.acquisition_price,
            existing.acquisition_currency,
            existing.resale_price,
            existing.resale_currency,
            existing.actual_profit,
            existing.days_to_sell,
        )
        requested_values = (
            payload.acquisition_price,
            payload.acquisition_currency,
            payload.resale_price,
            payload.resale_currency,
            payload.actual_profit,
            payload.days_to_sell,
        )
        if stored_values != requested_values:
            raise IdempotencyConflictError
        return TradeOutcomeResult(existing, False)

    @staticmethod
    def _is_idempotency_conflict(error: IntegrityError, constraint_name: str) -> bool:
        diagnostic = getattr(error.orig, "diag", None)
        if getattr(diagnostic, "constraint_name", None) == constraint_name:
            return True
        table_name = constraint_name.removeprefix("uq_").removesuffix("_idempotency_key")
        return f"{table_name}.idempotency_key" in str(error.orig)
