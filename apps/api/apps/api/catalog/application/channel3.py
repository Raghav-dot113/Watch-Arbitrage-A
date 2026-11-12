from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

Channel3Condition = Literal["used", "new", "all"]


class _Channel3Model(BaseModel):
    model_config = ConfigDict(extra="allow")


class Channel3Price(_Channel3Model):
    amount: Decimal = Field(validation_alias=AliasChoices("amount", "price"))
    currency: str = "USD"
    compare_at_price: Decimal | None = None


class Channel3Brand(_Channel3Model):
    id: str
    name: str


class Channel3Image(_Channel3Model):
    url: str
    cleaned_url: str | None = None
    is_main_image: bool | None = None
    shot_type: str | None = None
    alt_text: str | None = None


class Channel3Offer(_Channel3Model):
    url: str
    domain: str
    price: Channel3Price
    availability: str
    condition: str | None = None
    max_commission_rate: Decimal | None = None


class Channel3Product(_Channel3Model):
    id: str
    title: str
    description: str | None = None
    brands: list[Channel3Brand] = Field(default_factory=list)
    images: list[Channel3Image] = Field(default_factory=list)
    category: dict[str, object] | None = None
    materials: list[str] | None = None
    key_features: list[str] | None = None
    offers: list[Channel3Offer] = Field(default_factory=list)
    structured_attributes: dict[str, object] = Field(default_factory=dict)


class Channel3SearchResponse(_Channel3Model):
    products: list[Channel3Product]
    next_page_token: str | None = None
    fetched_at: datetime
    filtered_out_count: int
    provider_pages_fetched: int


class Channel3SearchGateway(Protocol):
    async def search(
        self,
        *,
        query: str,
        limit: int,
        page_token: str | None,
        condition: Channel3Condition = "used",
        in_stock_only: bool = False,
    ) -> Channel3SearchResponse: ...


class Channel3NotConfiguredError(Exception):
    """Raised when the Channel3 API key is missing."""


class Channel3UnavailableError(Exception):
    """Raised when Channel3 cannot return a valid search response."""

    def __init__(self, status_code: int | None = None) -> None:
        super().__init__("Channel3 search is unavailable")
        self.status_code = status_code
