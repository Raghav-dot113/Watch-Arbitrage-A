"""Seed data definitions for ChronoArb demo/development data.

All seed data is defined as plain Python dataclasses/dicts so the seed
runner can remain agnostic of the ORM. The runner is responsible for
mapping these definitions into ORM instances idempotently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class SeedOrganization:
    name: str
    slug: str
    settings: dict[str, object] | None = None


@dataclass(frozen=True)
class SeedUser:
    cognito_sub: str
    email: str
    display_name: str | None = None


@dataclass(frozen=True)
class SeedMembership:
    user_email: str
    organization_slug: str
    role: str


@dataclass(frozen=True)
class SeedBrand:
    name: str
    slug: str


@dataclass(frozen=True)
class SeedSource:
    source_key: str
    display_name: str
    adapter_version: str
    access_mode: str
    rate_policy: dict[str, object] | None = None
    approval_ref: str | None = None
    is_enabled: bool = True


@dataclass(frozen=True)
class SeedReference:
    brand_slug: str
    ref_code: str
    model_name: str | None = None
    generation: str | None = None
    attributes: dict[str, object] | None = None
    is_active: bool = True


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

SEED_ORGANIZATIONS: list[SeedOrganization] = [
    SeedOrganization(
        name="ChronoArb Demo",
        slug="demo",
        settings={"currency": "USD", "timezone": "America/New_York"},
    ),
    SeedOrganization(
        name="Acme Watch Co.",
        slug="acme-watch",
        settings={"currency": "EUR", "timezone": "Europe/Berlin"},
    ),
]

# ---------------------------------------------------------------------------
# Users (cognito_sub is the Cognito identity provider subject)
# ---------------------------------------------------------------------------

SEED_USERS: list[SeedUser] = [
    SeedUser(
        cognito_sub="cognito:demo_owner",
        email="owner@demo.example.com",
        display_name="Demo Owner",
    ),
    SeedUser(
        cognito_sub="cognito:demo_dealer",
        email="dealer@demo.example.com",
        display_name="Demo Dealer",
    ),
    SeedUser(
        cognito_sub="cognito:demo_viewer",
        email="viewer@demo.example.com",
        display_name="Demo Viewer",
    ),
    SeedUser(
        cognito_sub="cognito:acme_owner",
        email="owner@acme.example.com",
        display_name="Acme Owner",
    ),
    SeedUser(
        cognito_sub="cognito:platform_ops",
        email="ops@chronoarb.example.com",
        display_name="Platform Ops",
    ),
]

# ---------------------------------------------------------------------------
# Memberships (link users to organizations with roles)
# ---------------------------------------------------------------------------

SEED_MEMBERSHIPS: list[SeedMembership] = [
    # Demo org memberships
    SeedMembership(user_email="owner@demo.example.com", organization_slug="demo", role="owner"),
    SeedMembership(user_email="dealer@demo.example.com", organization_slug="demo", role="dealer"),
    SeedMembership(user_email="viewer@demo.example.com", organization_slug="demo", role="viewer"),
    # Acme org memberships
    SeedMembership(
        user_email="owner@acme.example.com",
        organization_slug="acme-watch",
        role="owner",
    ),
]

# ---------------------------------------------------------------------------
# Catalog brands
# ---------------------------------------------------------------------------

SEED_BRANDS: list[SeedBrand] = [
    SeedBrand(name="Rolex", slug="rolex"),
    SeedBrand(name="Omega", slug="omega"),
    SeedBrand(name="Patek Philippe", slug="patek-philippe"),
    SeedBrand(name="Audemars Piguet", slug="audemars-piguet"),
    SeedBrand(name="Cartier", slug="cartier"),
    SeedBrand(name="TAG Heuer", slug="tag-heuer"),
]

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

SEED_SOURCES: list[SeedSource] = [
    SeedSource(
        source_key="ebay",
        display_name="eBay",
        adapter_version="1.0.0",
        access_mode="public",
        rate_policy={"requests_per_minute": 60, "concurrency": 5},
        approval_ref="ebay-api-partner-2024",
        is_enabled=True,
    ),
    SeedSource(
        source_key="chrono24",
        display_name="Chrono24",
        adapter_version="2.1.0",
        access_mode="partner",
        rate_policy={"requests_per_minute": 30, "concurrency": 3},
        approval_ref="chrono24-affiliate-v2",
        is_enabled=True,
    ),
    SeedSource(
        source_key="watchbox",
        display_name="WatchBox",
        adapter_version="1.5.0",
        access_mode="partner",
        rate_policy={"requests_per_minute": 20, "concurrency": 2},
        approval_ref="watchbox-inventory-feed",
        is_enabled=True,
    ),
    SeedSource(
        source_key="christies",
        display_name="Christie's",
        adapter_version="1.0.0",
        access_mode="contract",
        rate_policy={"requests_per_minute": 10, "concurrency": 1},
        approval_ref="christies-auction-feed-2025",
        is_enabled=False,
    ),
    SeedSource(
        source_key="sothebys",
        display_name="Sotheby's",
        adapter_version="1.0.0",
        access_mode="contract",
        rate_policy={"requests_per_minute": 10, "concurrency": 1},
        approval_ref="sothebys-auction-feed-2025",
        is_enabled=False,
    ),
]

# ---------------------------------------------------------------------------
# Catalog references (watch models linked to brands)
# ---------------------------------------------------------------------------

SEED_REFERENCES: list[SeedReference] = [
    # Rolex
    SeedReference(
        brand_slug="rolex",
        ref_code="126710",
        model_name="GMT-Master II",
        generation="Pepsi",
        attributes={"case_material": "Steel", "bezel": "Ceramic"},
    ),
    SeedReference(
        brand_slug="rolex",
        ref_code="124060",
        model_name="Submariner",
        generation="Date",
        attributes={"case_material": "Steel", "bezel": "Ceramic"},
    ),
    SeedReference(
        brand_slug="rolex",
        ref_code="126300",
        model_name="Datejust 41",
        generation="Fluted",
        attributes={"case_material": "Steel", "dial": "Silver"},
    ),
    SeedReference(
        brand_slug="rolex",
        ref_code="126610",
        model_name="Sea-Dweller",
        generation="Deepsea",
        attributes={"case_material": "Steel", "water_resistance": "3900m"},
    ),
    # Omega
    SeedReference(
        brand_slug="omega",
        ref_code="310.30.42",
        model_name="Speedmaster Professional",
        generation="Moonwatch",
        attributes={"case_material": "Steel", "movement": "Manual"},
    ),
    SeedReference(
        brand_slug="omega",
        ref_code="210.30.42",
        model_name="Speedmaster",
        generation="Co-Axial",
        attributes={"case_material": "Steel", "movement": "Automatic"},
    ),
    SeedReference(
        brand_slug="omega",
        ref_code="522.30.43",
        model_name="Seamaster 300M",
        generation="Spectre",
        attributes={"case_material": "Steel", "water_resistance": "300m"},
    ),
    # Patek Philippe
    SeedReference(
        brand_slug="patek-philippe",
        ref_code="5711",
        model_name="Nautilus",
        generation="Steel",
        attributes={"case_material": "Steel", "complication": "Date"},
    ),
    SeedReference(
        brand_slug="patek-philippe",
        ref_code="5726",
        model_name="Nautilus",
        generation="Travel Time",
        attributes={"case_material": "Steel", "complication": "GMT"},
    ),
    # Audemars Piguet
    SeedReference(
        brand_slug="audemars-piguet",
        ref_code="15500",
        model_name="Royal Oak",
        generation="Steel",
        attributes={"case_material": "Steel", "bezel": "Tapisserie"},
    ),
    SeedReference(
        brand_slug="audemars-piguet",
        ref_code="26331",
        model_name="Royal Oak Offshore",
        generation="Diver",
        attributes={"case_material": "Steel", "water_resistance": "300m"},
    ),
    # Cartier
    SeedReference(
        brand_slug="cartier",
        ref_code="WSSA003",
        model_name="Santos Dumont",
        generation="Small",
        attributes={"case_material": "Steel", "shape": "Square"},
    ),
    SeedReference(
        brand_slug="cartier",
        ref_code="W2SA0008",
        model_name="Ballon Bleu",
        generation="Medium",
        attributes={"case_material": "Steel", "shape": "Round"},
    ),
    # TAG Heuer
    SeedReference(
        brand_slug="tag-heuer",
        ref_code="CBK2118",
        model_name="Formula 1",
        generation="Quartz",
        attributes={"case_material": "Steel", "movement": "Quartz"},
    ),
    SeedReference(
        brand_slug="tag-heuer",
        ref_code="WBP2010",
        model_name="Aquaracer",
        generation="Professional",
        attributes={"case_material": "Steel", "water_resistance": "300m"},
    ),
]


# ---------------------------------------------------------------------------
# Raw snapshots (immutable raw evidence from each source)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedSnapshot:
    source_key: str
    external_id: str
    adapter_version: str
    checksum: str
    raw_payload: dict[str, object] | None = None
    fetched_at: datetime | None = None


@dataclass(frozen=True)
class SeedParsedListing:
    source_key: str
    external_id: str
    parser_version: str
    listing_price: Decimal | None = None
    price_currency: str | None = None
    listing_title: str | None = None
    description: str | None = None
    parsed_attributes: dict[str, object] | None = None
    external_url: str | None = None
    listed_at: datetime | None = None


@dataclass(frozen=True)
class SeedNormalizedListing:
    source_key: str
    external_id: str
    reference_slug: str
    ref_code: str
    normalization_version: str
    match_confidence: Decimal | None = None
    match_method: str | None = None
    match_features: dict[str, object] | None = None
    condition: str | None = None
    set_status: str | None = None
    seller_geography: str | None = None
    normalized_price: Decimal | None = None
    normalized_currency: str | None = None
    fx_rate: Decimal = Decimal("1")
    fx_source: str = "ecb"
    fx_date: date | None = None
    observation_at: datetime | None = None
    status: str = "active"


@dataclass(frozen=True)
class SeedValuation:
    source_key: str
    external_id: str
    model_version: str
    config_version: str
    cost_assumptions_version: str
    expected_exit_price: Decimal | None = None
    exit_price_currency: str | None = None
    all_in_acquisition: Decimal | None = None
    expected_net_resale: Decimal | None = None
    expected_net_profit: Decimal | None = None
    roi: Decimal | None = None
    low_estimate: Decimal | None = None
    high_estimate: Decimal | None = None
    confidence: Decimal | None = None
    comparable_count: int | None = None
    sample_dispersion: Decimal | None = None
    adjustment_details: dict[str, object] | None = None
    risk_reserve_details: dict[str, object] | None = None
    cost_breakdown: dict[str, object] | None = None


@dataclass(frozen=True)
class SeedOpportunity:
    organization_slug: str
    source_key: str
    external_id: str
    material_version: int
    score: Decimal | None = None
    state: str = "published"
    positive_factors: dict[str, object] | None = None
    negative_factors: dict[str, object] | None = None
    published_at: datetime | None = None
    state_changed_at: datetime | None = None


@dataclass(frozen=True)
class SeedAlertRule:
    organization_slug: str
    created_by_email: str
    name: str
    filters: dict[str, object]
    channels: list[str]
    cooldown_minutes: int = 60
    is_enabled: bool = True


@dataclass(frozen=True)
class SeedAlertDelivery:
    organization_slug: str
    rule_name: str
    user_email: str
    source_key: str
    external_id: str
    material_version: int
    channel: str
    idempotency_key: str
    delivery_status: Literal["pending", "sent", "failed", "suppressed"]
    provider_message_id: str | None = None


@dataclass(frozen=True)
class SeedFeedback:
    organization_slug: str
    user_email: str
    source_key: str
    external_id: str
    material_version: int
    decision: Literal["purchased", "contacted", "dismissed"]
    notes: str | None
    idempotency_key: str
    created_at: datetime


@dataclass(frozen=True)
class SeedTradeOutcome:
    organization_slug: str
    user_email: str
    source_key: str
    external_id: str
    material_version: int
    reference_slug: str
    ref_code: str
    acquisition_price: Decimal
    acquisition_currency: str
    resale_price: Decimal
    resale_currency: str
    actual_profit: Decimal
    days_to_sell: int
    idempotency_key: str
    created_at: datetime


@dataclass(frozen=True)
class SeedSubscription:
    organization_slug: str
    paypal_subscription_id: str
    status: Literal["trialing", "active", "past_due", "canceled", "unpaid"]
    plan_id: str
    current_period_start: datetime
    current_period_end: datetime
    trial_end: datetime | None = None
    paypal_payer_id: str | None = None


@dataclass(frozen=True)
class SeedFeatureFlag:
    key: str
    description: str
    enabled: bool = False
    organization_slugs: list[str] | None = None
    rollout_pct: int = 0
    expires_at: datetime | None = None


@dataclass(frozen=True)
class SeedAuditEvent:
    organization_slug: str | None
    user_email: str | None
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, object]


# ---------------------------------------------------------------------------
# Raw snapshots
# ---------------------------------------------------------------------------

SEED_SNAPSHOTS: list[SeedSnapshot] = [
    SeedSnapshot(
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        adapter_version="1.0.0",
        checksum="sha256:ebay-rolex-126710-001-v1",
        raw_payload={
            "title": "Rolex GMT-Master II Pepsi 126710BLRO",
            "price": 12500.00,
            "currency": "USD",
        },
    ),
    SeedSnapshot(
        source_key="chrono24",
        external_id="chrono24-rolex-124060-002",
        adapter_version="2.1.0",
        checksum="sha256:chrono24-rolex-124060-002-v2",
        raw_payload={
            "title": "Rolex Submariner Date 124060",
            "price": 9800.00,
            "currency": "EUR",
        },
    ),
    SeedSnapshot(
        source_key="watchbox",
        external_id="watchbox-omega-3103042-003",
        adapter_version="1.5.0",
        checksum="sha256:watchbox-omega-3103042-003-v1",
        raw_payload={
            "title": "Omega Speedmaster Professional Moonwatch 310.30.42",
            "price": 7200.00,
            "currency": "USD",
        },
    ),
    SeedSnapshot(
        source_key="ebay",
        external_id="ebay-patek-5711-004",
        adapter_version="1.0.0",
        checksum="sha256:ebay-patek-5711-004-v1",
        raw_payload={
            "title": "Patek Philippe Nautilus Steel 5711",
            "price": 68000.00,
            "currency": "USD",
        },
    ),
]


# ---------------------------------------------------------------------------
# Parsed listings
# ---------------------------------------------------------------------------

SEED_PARSED_LISTINGS: list[SeedParsedListing] = [
    SeedParsedListing(
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        parser_version="1.2.0",
        listing_price=Decimal("12500.00"),
        price_currency="USD",
        listing_title="Rolex GMT-Master II Pepsi 126710BLRO",
        description="Pre-owned Rolex GMT-Master II Pepsi with box and papers.",
        parsed_attributes={"case_material": "Steel", "bezel": "Ceramic", "dial": "Black"},
        external_url="https://ebay.com/itm/126710-001",
    ),
    SeedParsedListing(
        source_key="chrono24",
        external_id="chrono24-rolex-124060-002",
        parser_version="2.3.0",
        listing_price=Decimal("9800.00"),
        price_currency="EUR",
        listing_title="Rolex Submariner Date 124060",
        description="Rolex Submariner Date in excellent condition.",
        parsed_attributes={"case_material": "Steel", "bezel": "Ceramic", "dial": "Black"},
        external_url="https://chrono24.com/124060-002",
    ),
    SeedParsedListing(
        source_key="watchbox",
        external_id="watchbox-omega-3103042-003",
        parser_version="1.1.0",
        listing_price=Decimal("7200.00"),
        price_currency="USD",
        listing_title="Omega Speedmaster Professional Moonwatch 310.30.42",
        description="Omega Speedmaster Professional Moonwatch.",
        parsed_attributes={"case_material": "Steel", "movement": "Manual"},
        external_url="https://watchbox.com/omega-3103042-003",
    ),
    SeedParsedListing(
        source_key="ebay",
        external_id="ebay-patek-5711-004",
        parser_version="1.2.0",
        listing_price=Decimal("68000.00"),
        price_currency="USD",
        listing_title="Patek Philippe Nautilus Steel 5711",
        description="Patek Philippe Nautilus Steel 5711A.",
        parsed_attributes={"case_material": "Steel", "complication": "Date"},
        external_url="https://ebay.com/itm/5711-004",
    ),
]


# ---------------------------------------------------------------------------
# Normalized listings
# ---------------------------------------------------------------------------

SEED_NORMALIZED_LISTINGS: list[SeedNormalizedListing] = [
    SeedNormalizedListing(
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        reference_slug="rolex",
        ref_code="126710",
        normalization_version="1.0.0",
        match_confidence=Decimal("0.98"),
        match_method="reference_exact",
        match_features={"case_material": True, "bezel": True},
        condition="pre-owned",
        set_status="full_set",
        seller_geography="US",
        normalized_price=Decimal("12500.00"),
        normalized_currency="USD",
        fx_rate=Decimal("1"),
        fx_source="ecb",
        fx_date=date(2026, 10, 1),
        observation_at=datetime(2026, 10, 1, 8, 0, 0),
        status="active",
    ),
    SeedNormalizedListing(
        source_key="chrono24",
        external_id="chrono24-rolex-124060-002",
        reference_slug="rolex",
        ref_code="124060",
        normalization_version="1.0.0",
        match_confidence=Decimal("0.95"),
        match_method="reference_exact",
        match_features={"case_material": True, "bezel": True},
        condition="excellent",
        set_status="full_set",
        seller_geography="DE",
        normalized_price=Decimal("10500.00"),
        normalized_currency="USD",
        fx_rate=Decimal("1.0714"),
        fx_source="ecb",
        fx_date=date(2026, 10, 1),
        observation_at=datetime(2026, 10, 1, 8, 30, 0),
        status="active",
    ),
    SeedNormalizedListing(
        source_key="watchbox",
        external_id="watchbox-omega-3103042-003",
        reference_slug="omega",
        ref_code="310.30.42",
        normalization_version="1.0.0",
        match_confidence=Decimal("0.99"),
        match_method="reference_exact",
        match_features={"case_material": True, "movement": True},
        condition="like_new",
        set_status="papers_only",
        seller_geography="US",
        normalized_price=Decimal("7200.00"),
        normalized_currency="USD",
        fx_rate=Decimal("1"),
        fx_source="ecb",
        fx_date=date(2026, 10, 1),
        observation_at=datetime(2026, 10, 1, 9, 0, 0),
        status="active",
    ),
    SeedNormalizedListing(
        source_key="ebay",
        external_id="ebay-patek-5711-004",
        reference_slug="patek-philippe",
        ref_code="5711",
        normalization_version="1.0.0",
        match_confidence=Decimal("0.97"),
        match_method="reference_exact",
        match_features={"case_material": True, "complication": True},
        condition="pre-owned",
        set_status="full_set",
        seller_geography="US",
        normalized_price=Decimal("68000.00"),
        normalized_currency="USD",
        fx_rate=Decimal("1"),
        fx_source="ecb",
        fx_date=date(2026, 10, 1),
        observation_at=datetime(2026, 10, 1, 9, 30, 0),
        status="active",
    ),
]


# ---------------------------------------------------------------------------
# Valuations
# ---------------------------------------------------------------------------

SEED_VALUATIONS: list[SeedValuation] = [
    SeedValuation(
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        model_version="v1.0.0",
        config_version="v1.0.0",
        cost_assumptions_version="v1.0.0",
        expected_exit_price=Decimal("13500.00"),
        exit_price_currency="USD",
        all_in_acquisition=Decimal("12700.00"),
        expected_net_resale=Decimal("13200.00"),
        expected_net_profit=Decimal("500.00"),
        roi=Decimal("3.9370"),
        low_estimate=Decimal("12800.00"),
        high_estimate=Decimal("14200.00"),
        confidence=Decimal("0.85"),
        comparable_count=12,
        sample_dispersion=Decimal("450.00"),
        adjustment_details={"condition_adjustment": Decimal("-100.00")},
        risk_reserve_details={"liquidity_reserve": Decimal("200.00")},
        cost_breakdown={"shipping": Decimal("50.00"), "insurance": Decimal("150.00")},
    ),
    SeedValuation(
        source_key="chrono24",
        external_id="chrono24-rolex-124060-002",
        model_version="v1.0.0",
        config_version="v1.0.0",
        cost_assumptions_version="v1.0.0",
        expected_exit_price=Decimal("11200.00"),
        exit_price_currency="USD",
        all_in_acquisition=Decimal("10650.00"),
        expected_net_resale=Decimal("10900.00"),
        expected_net_profit=Decimal("250.00"),
        roi=Decimal("2.3474"),
        low_estimate=Decimal("10400.00"),
        high_estimate=Decimal("12000.00"),
        confidence=Decimal("0.80"),
        comparable_count=8,
        sample_dispersion=Decimal("300.00"),
        adjustment_details={"fx_adjustment": Decimal("50.00")},
        risk_reserve_details={"liquidity_reserve": Decimal("150.00")},
        cost_breakdown={"shipping": Decimal("75.00"), "insurance": Decimal("125.00")},
    ),
    SeedValuation(
        source_key="watchbox",
        external_id="watchbox-omega-3103042-003",
        model_version="v1.0.0",
        config_version="v1.0.0",
        cost_assumptions_version="v1.0.0",
        expected_exit_price=Decimal("7800.00"),
        exit_price_currency="USD",
        all_in_acquisition=Decimal("7350.00"),
        expected_net_resale=Decimal("7600.00"),
        expected_net_profit=Decimal("250.00"),
        roi=Decimal("3.4014"),
        low_estimate=Decimal("7300.00"),
        high_estimate=Decimal("8300.00"),
        confidence=Decimal("0.90"),
        comparable_count=15,
        sample_dispersion=Decimal("200.00"),
        adjustment_details={"condition_adjustment": Decimal("100.00")},
        risk_reserve_details={"liquidity_reserve": Decimal("100.00")},
        cost_breakdown={"shipping": Decimal("40.00"), "insurance": Decimal("110.00")},
    ),
    SeedValuation(
        source_key="ebay",
        external_id="ebay-patek-5711-004",
        model_version="v1.0.0",
        config_version="v1.0.0",
        cost_assumptions_version="v1.0.0",
        expected_exit_price=Decimal("72000.00"),
        exit_price_currency="USD",
        all_in_acquisition=Decimal("68500.00"),
        expected_net_resale=Decimal("71000.00"),
        expected_net_profit=Decimal("2500.00"),
        roi=Decimal("3.6496"),
        low_estimate=Decimal("69000.00"),
        high_estimate=Decimal("75000.00"),
        confidence=Decimal("0.75"),
        comparable_count=5,
        sample_dispersion=Decimal("1200.00"),
        adjustment_details={"market_premium": Decimal("1000.00")},
        risk_reserve_details={"liquidity_reserve": Decimal("500.00")},
        cost_breakdown={"shipping": Decimal("100.00"), "insurance": Decimal("400.00")},
    ),
]


# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------

SEED_OPPORTUNITIES: list[SeedOpportunity] = [
    SeedOpportunity(
        organization_slug="demo",
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        material_version=1,
        score=Decimal("85.00"),
        state="published",
        positive_factors={"high_liquidity": True, "strong_roi": True},
        negative_factors={"shipping_cost": Decimal("50.00")},
        published_at=datetime(2026, 10, 1, 10, 0, 0),
    ),
    SeedOpportunity(
        organization_slug="acme-watch",
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        material_version=1,
        score=Decimal("82.00"),
        state="published",
        positive_factors={"high_liquidity": True},
        negative_factors={"shipping_cost": Decimal("50.00")},
        published_at=datetime(2026, 10, 1, 10, 15, 0),
    ),
    SeedOpportunity(
        organization_slug="demo",
        source_key="chrono24",
        external_id="chrono24-rolex-124060-002",
        material_version=1,
        score=Decimal("78.00"),
        state="published",
        positive_factors={"steady_demand": True},
        negative_factors={"fx_risk": Decimal("150.00")},
        published_at=datetime(2026, 10, 1, 10, 30, 0),
    ),
    SeedOpportunity(
        organization_slug="demo",
        source_key="watchbox",
        external_id="watchbox-omega-3103042-003",
        material_version=1,
        score=Decimal("88.00"),
        state="published",
        positive_factors={"high_confidence": True},
        negative_factors={},
        published_at=datetime(2026, 10, 1, 11, 0, 0),
    ),
    SeedOpportunity(
        organization_slug="demo",
        source_key="ebay",
        external_id="ebay-patek-5711-004",
        material_version=1,
        score=Decimal("65.00"),
        state="published",
        positive_factors={"brand_premium": True},
        negative_factors={"high_entry_cost": Decimal("68000.00")},
        published_at=datetime(2026, 10, 1, 11, 30, 0),
    ),
]


SEED_ALERT_RULES: list[SeedAlertRule] = [
    SeedAlertRule(
        organization_slug="demo",
        created_by_email="owner@demo.example.com",
        name="High-value Rolex alerts",
        filters={"min_profit": "500.00"},
        channels=["in_app", "telegram"],
        cooldown_minutes=120,
    ),
    SeedAlertRule(
        organization_slug="acme-watch",
        created_by_email="owner@acme.example.com",
        name="Acme daily digest",
        filters={"min_profit": "1000.00"},
        channels=["in_app"],
        cooldown_minutes=1440,
    ),
]

SEED_ALERT_DELIVERIES: list[SeedAlertDelivery] = [
    SeedAlertDelivery(
        organization_slug="demo",
        rule_name="High-value Rolex alerts",
        user_email="owner@demo.example.com",
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        material_version=1,
        channel="in_app",
        idempotency_key="seed:b16:demo:rolex-126710:in-app",
        delivery_status="sent",
    ),
    SeedAlertDelivery(
        organization_slug="acme-watch",
        rule_name="Acme daily digest",
        user_email="owner@acme.example.com",
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        material_version=1,
        channel="in_app",
        idempotency_key="seed:b16:acme:rolex-126710:in-app",
        delivery_status="pending",
    ),
]

SEED_FEEDBACK: list[SeedFeedback] = [
    SeedFeedback(
        organization_slug="demo",
        user_email="dealer@demo.example.com",
        source_key="watchbox",
        external_id="watchbox-omega-3103042-003",
        material_version=1,
        decision="purchased",
        notes="Purchased for the demo trade history.",
        idempotency_key="seed:b16:feedback:demo:omega-3103042:purchased",
        created_at=datetime(2026, 10, 5, 15, 0, tzinfo=UTC),
    ),
    SeedFeedback(
        organization_slug="acme-watch",
        user_email="owner@acme.example.com",
        source_key="ebay",
        external_id="ebay-rolex-126710-001",
        material_version=1,
        decision="contacted",
        notes="Requested additional condition photos.",
        idempotency_key="seed:b16:feedback:acme:rolex-126710:contacted",
        created_at=datetime(2026, 10, 6, 10, 30, tzinfo=UTC),
    ),
]

SEED_TRADE_OUTCOMES: list[SeedTradeOutcome] = [
    SeedTradeOutcome(
        organization_slug="demo",
        user_email="dealer@demo.example.com",
        source_key="watchbox",
        external_id="watchbox-omega-3103042-003",
        material_version=1,
        reference_slug="omega",
        ref_code="310.30.42",
        acquisition_price=Decimal("7200.00"),
        acquisition_currency="USD",
        resale_price=Decimal("8100.00"),
        resale_currency="USD",
        actual_profit=Decimal("900.00"),
        days_to_sell=45,
        idempotency_key="seed:b16:outcome:demo:omega-3103042",
        created_at=datetime(2026, 11, 1, 12, 0, tzinfo=UTC),
    )
]

SEED_SUBSCRIPTIONS: list[SeedSubscription] = [
    SeedSubscription(
        organization_slug="demo",
        paypal_subscription_id="I-SEED-DEMO",
        status="active",
        plan_id="dealer-pro",
        current_period_start=datetime(2026, 11, 1, tzinfo=UTC),
        current_period_end=datetime(2026, 12, 1, tzinfo=UTC),
    ),
    SeedSubscription(
        organization_slug="acme-watch",
        paypal_subscription_id="I-SEED-ACME",
        status="trialing",
        plan_id="dealer-starter",
        current_period_start=datetime(2026, 11, 1, tzinfo=UTC),
        current_period_end=datetime(2026, 12, 1, tzinfo=UTC),
        trial_end=datetime(2026, 11, 15, tzinfo=UTC),
    ),
]

SEED_FEATURE_FLAGS: list[SeedFeatureFlag] = [
    SeedFeatureFlag(
        key="alerts.email_delivery",
        description="Enable email delivery for organization alerts.",
        enabled=True,
        rollout_pct=100,
    ),
    SeedFeatureFlag(
        key="valuation.v2",
        description="Enable the second-generation valuation model.",
        enabled=True,
        organization_slugs=["demo"],
        rollout_pct=50,
    ),
    SeedFeatureFlag(
        key="admin.job_replay",
        description="Enable job replay when a queue backend is available.",
        enabled=False,
        rollout_pct=0,
    ),
]

SEED_AUDIT_EVENTS: list[SeedAuditEvent] = [
    SeedAuditEvent(
        organization_slug="demo",
        user_email="owner@demo.example.com",
        action="seed.demo_data_loaded",
        resource_type="seed_run",
        resource_id="b16-demo",
        details={"packet": "B16", "source": "development_seed"},
    ),
    SeedAuditEvent(
        organization_slug="acme-watch",
        user_email="owner@acme.example.com",
        action="seed.demo_data_loaded",
        resource_type="seed_run",
        resource_id="b16-acme",
        details={"packet": "B16", "source": "development_seed"},
    ),
]


def seed_data_summary() -> str:
    """Return a human-readable summary of what will be seeded."""
    return (
        f"organizations={len(SEED_ORGANIZATIONS)} "
        f"users={len(SEED_USERS)} "
        f"memberships={len(SEED_MEMBERSHIPS)} "
        f"brands={len(SEED_BRANDS)} "
        f"sources={len(SEED_SOURCES)} "
        f"references={len(SEED_REFERENCES)} "
        f"snapshots={len(SEED_SNAPSHOTS)} "
        f"parsed_listings={len(SEED_PARSED_LISTINGS)} "
        f"normalized_listings={len(SEED_NORMALIZED_LISTINGS)} "
        f"valuations={len(SEED_VALUATIONS)} "
        f"opportunities={len(SEED_OPPORTUNITIES)} "
        f"alert_rules={len(SEED_ALERT_RULES)} "
        f"alert_deliveries={len(SEED_ALERT_DELIVERIES)} "
        f"feedback={len(SEED_FEEDBACK)} "
        f"trade_outcomes={len(SEED_TRADE_OUTCOMES)} "
        f"subscriptions={len(SEED_SUBSCRIPTIONS)} "
        f"feature_flags={len(SEED_FEATURE_FLAGS)} "
        f"audit_events={len(SEED_AUDIT_EVENTS)}"
    )
