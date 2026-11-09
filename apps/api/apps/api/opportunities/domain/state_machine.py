from __future__ import annotations

from typing import Literal

OpportunityState = Literal["published", "dismissed", "contacted", "purchased", "expired"]
FeedbackDecision = Literal["purchased", "contacted", "dismissed"]

_DECISION_STATES: dict[FeedbackDecision, OpportunityState] = {
    "purchased": "purchased",
    "contacted": "contacted",
    "dismissed": "dismissed",
}


class InvalidOpportunityTransitionError(Exception):
    pass


def transition_opportunity_state(
    current_state: str,
    decision: FeedbackDecision,
) -> OpportunityState:
    if current_state != "published":
        raise InvalidOpportunityTransitionError(
            f"Cannot apply a dealer decision to an opportunity in {current_state!r} state"
        )
    return _DECISION_STATES[decision]
