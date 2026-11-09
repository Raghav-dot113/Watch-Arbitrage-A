from typing import Literal

type SubscriptionStatus = Literal["trialing", "active", "past_due", "canceled", "unpaid"]

__all__ = ["SubscriptionStatus"]
