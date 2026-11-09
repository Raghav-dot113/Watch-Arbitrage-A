from __future__ import annotations

from typing import Any

from apps.api.feedback.api.schemas import FeedbackRequest, FeedbackResponse
from apps.api.feedback.infrastructure.models import Feedback
from apps.api.feedback.infrastructure.repositories import FeedbackRepository
from apps.api.idempotency.application.service import (
    IdempotencyKeyReuseError,
    IdempotencyResult,
    IdempotencyService,
)
from apps.api.valuation.infrastructure.repositories import OpportunityRepository
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


class OpportunityNotFoundError(Exception):
    pass


class FeedbackService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._feedback = FeedbackRepository(session)
        self._opportunities = OpportunityRepository(session)

    async def create(
        self,
        *,
        organization_id: str,
        user_id: str,
        opportunity_id: str,
        idempotency_key: str,
        request: FeedbackRequest,
    ) -> IdempotencyResult:
        request_body = {
            "opportunity_id": opportunity_id,
            "decision": request.decision,
            "notes": request.notes,
        }
        legacy_record = await self._feedback.get_by_idempotency_key(
            organization_id,
            idempotency_key,
        )
        if legacy_record is not None:
            if (
                legacy_record.opportunity_id != opportunity_id
                or legacy_record.decision != request.decision
                or legacy_record.notes != request.notes
            ):
                raise IdempotencyKeyReuseError
            return IdempotencyResult(
                status_code=200,
                response_body=FeedbackResponse.model_validate(legacy_record).model_dump(
                    mode="json"
                ),
                replayed=True,
            )

        async def create_feedback() -> tuple[int, dict[str, Any]]:
            opportunity = await self._opportunities.get_by_id(
                opportunity_id,
                organization_id,
            )
            if opportunity is None:
                raise OpportunityNotFoundError
            feedback = Feedback(
                id=generate_ulid("fbk"),
                organization_id=organization_id,
                user_id=user_id,
                opportunity_id=opportunity_id,
                decision=request.decision,
                notes=request.notes,
                idempotency_key=IdempotencyService.scoped_key(
                    organization_id,
                    "POST:/api/v1/opportunities/{opp_id}/feedback",
                    idempotency_key,
                ),
            )
            await self._feedback.save(feedback)
            response = FeedbackResponse.model_validate(feedback)
            return 201, response.model_dump(mode="json")

        return await IdempotencyService(self._session).execute(
            organization_id=organization_id,
            route_key="POST:/api/v1/opportunities/{opp_id}/feedback",
            key=idempotency_key,
            request_body=request_body,
            operation=create_feedback,
        )
