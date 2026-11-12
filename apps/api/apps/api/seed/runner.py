"""Idempotent seed runner for ChronoArb demo/development data.

Maps seed data definitions (see ``seed.data``) into SQLAlchemy ORM
instances. The runner is idempotent: running it multiple times produces
the same database state because it looks up existing records by their
natural key before inserting.
"""

from __future__ import annotations

from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.billing.infrastructure.models import Subscription
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.feedback.infrastructure.models import Feedback, TradeOutcome
from apps.api.identity.infrastructure.models import Membership, Organization, User
<<<<<<< HEAD
from apps.api.infrastructure.database import async_session
from apps.api.infrastructure.models import Base
=======
from apps.api.infrastructure.database import async_session, initialize_dev_sqlite_schema
>>>>>>> ff9d2453712b6ae8252250b05fe54c0830ca3bac
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.operations.infrastructure.models import AuditEvent, FeatureFlag
from apps.api.opportunities.domain.state_machine import transition_opportunity_state
from apps.api.opportunities.infrastructure.models import Opportunity
from apps.api.seed.data import (
    SEED_ALERT_DELIVERIES,
    SEED_ALERT_RULES,
    SEED_AUDIT_EVENTS,
    SEED_BRANDS,
    SEED_FEATURE_FLAGS,
    SEED_FEEDBACK,
    SEED_MEMBERSHIPS,
    SEED_NORMALIZED_LISTINGS,
    SEED_OPPORTUNITIES,
    SEED_ORGANIZATIONS,
    SEED_PARSED_LISTINGS,
    SEED_REFERENCES,
    SEED_SNAPSHOTS,
    SEED_SOURCES,
    SEED_SUBSCRIPTIONS,
    SEED_TRADE_OUTCOMES,
    SEED_USERS,
    SEED_VALUATIONS,
    SeedAlertDelivery,
    SeedAlertRule,
    SeedAuditEvent,
    SeedBrand,
    SeedFeatureFlag,
    SeedFeedback,
    SeedMembership,
    SeedNormalizedListing,
    SeedOpportunity,
    SeedOrganization,
    SeedParsedListing,
    SeedReference,
    SeedSnapshot,
    SeedSource,
    SeedSubscription,
    SeedTradeOutcome,
    SeedUser,
    SeedValuation,
)
from apps.api.valuation.infrastructure.models import Valuation
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


def _json_sanitize(value: object) -> object:
    """Recursively convert Decimal values to str for JSON column compatibility."""
    from decimal import Decimal

    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_sanitize(v) for v in value]
    return value


async def _get_org_by_slug(session: AsyncSession, slug: str) -> Organization | None:
    result = await session.execute(select(Organization).where(Organization.slug == slug))
    return result.scalar_one_or_none()


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_brand_by_slug(session: AsyncSession, slug: str) -> Brand | None:
    result = await session.execute(select(Brand).where(Brand.slug == slug))
    return result.scalar_one_or_none()


async def _get_source_by_key(session: AsyncSession, source_key: str) -> Source | None:
    result = await session.execute(select(Source).where(Source.source_key == source_key))
    return result.scalar_one_or_none()


async def _get_reference_by_brand_and_code(
    session: AsyncSession, brand_id: str, ref_code: str
) -> Reference | None:
    result = await session.execute(
        select(Reference)
        .where(Reference.brand_id == brand_id)
        .where(Reference.ref_code == ref_code)
    )
    return result.scalar_one_or_none()


async def _get_snapshot_by_natural_key(
    session: AsyncSession,
    source_id: str,
    external_id: str,
    adapter_version: str,
    checksum: str,
) -> RawSnapshot | None:
    result = await session.execute(
        select(RawSnapshot)
        .where(RawSnapshot.source_id == source_id)
        .where(RawSnapshot.external_id == external_id)
        .where(RawSnapshot.adapter_version == adapter_version)
        .where(RawSnapshot.checksum == checksum)
    )
    return result.scalar_one_or_none()


async def _get_normalized_listing_by_source_external(
    session: AsyncSession,
    source_id: str,
    external_id: str,
) -> NormalizedListing | None:
    result = await session.execute(
        select(NormalizedListing)
        .join(ParsedListing, ParsedListing.id == NormalizedListing.parsed_listing_id)
        .join(RawSnapshot, RawSnapshot.id == ParsedListing.snapshot_id)
        .where(RawSnapshot.source_id == source_id)
        .where(RawSnapshot.external_id == external_id)
    )
    return result.scalar_one_or_none()


async def _get_opportunity_by_seed_key(
    session: AsyncSession,
    organization_id: str,
    source_id: str,
    external_id: str,
    material_version: int,
) -> Opportunity | None:
    result = await session.execute(
        select(Opportunity)
        .join(NormalizedListing, NormalizedListing.id == Opportunity.listing_id)
        .join(ParsedListing, ParsedListing.id == NormalizedListing.parsed_listing_id)
        .join(RawSnapshot, RawSnapshot.id == ParsedListing.snapshot_id)
        .where(
            Opportunity.organization_id == organization_id,
            Opportunity.material_version == material_version,
            RawSnapshot.source_id == source_id,
            RawSnapshot.external_id == external_id,
        )
    )
    return result.scalar_one_or_none()


async def _seed_organizations(
    session: AsyncSession, orgs: list[SeedOrganization]
) -> dict[str, Organization]:
    """Seed organizations, returning a slug->org map for downstream use."""
    org_map: dict[str, Organization] = {}
    for seed in orgs:
        org = await _get_org_by_slug(session, seed.slug)
        if org is None:
            org = Organization(
                id=generate_ulid("org"),
                name=seed.name,
                slug=seed.slug,
                settings=seed.settings,
            )
            session.add(org)
            await session.flush()
            org_map[seed.slug] = org
        else:
            org_map[seed.slug] = org
    return org_map


async def _seed_users(session: AsyncSession, users: list[SeedUser]) -> dict[str, User]:
    """Seed users, returning an email->user map for downstream use."""
    user_map: dict[str, User] = {}
    for seed in users:
        user = await _get_user_by_email(session, seed.email)
        if user is None:
            user = User(
                id=generate_ulid("usr"),
                cognito_sub=seed.cognito_sub,
                email=seed.email,
                display_name=seed.display_name,
            )
            session.add(user)
            await session.flush()
            user_map[seed.email] = user
        else:
            user_map[seed.email] = user
    return user_map


async def _seed_brands(session: AsyncSession, brands: list[SeedBrand]) -> dict[str, Brand]:
    """Seed brands, returning a slug->brand map for downstream use."""
    brand_map: dict[str, Brand] = {}
    for seed in brands:
        brand = await _get_brand_by_slug(session, seed.slug)
        if brand is None:
            brand = Brand(id=generate_ulid("brd"), name=seed.name, slug=seed.slug)
            session.add(brand)
            await session.flush()
            brand_map[seed.slug] = brand
        else:
            brand_map[seed.slug] = brand
    return brand_map


async def _seed_sources(session: AsyncSession, sources: list[SeedSource]) -> dict[str, Source]:
    """Seed sources, returning a source_key->source map for downstream use."""
    source_map: dict[str, Source] = {}
    for seed in sources:
        source = await _get_source_by_key(session, seed.source_key)
        if source is None:
            source = Source(
                id=generate_ulid("src"),
                source_key=seed.source_key,
                display_name=seed.display_name,
                adapter_version=seed.adapter_version,
                access_mode=seed.access_mode,
                rate_policy=seed.rate_policy,
                approval_ref=seed.approval_ref,
                is_enabled=seed.is_enabled,
            )
            session.add(source)
            await session.flush()
            source_map[seed.source_key] = source
        else:
            source_map[seed.source_key] = source
    return source_map


async def _seed_memberships(
    session: AsyncSession,
    memberships: list[SeedMembership],
    user_map: dict[str, User],
    org_map: dict[str, Organization],
) -> None:
    """Seed memberships linking users to organizations."""
    for seed in memberships:
        user = user_map.get(seed.user_email)
        org = org_map.get(seed.organization_slug)
        if user is None or org is None:
            continue
        existing = await session.execute(
            select(Membership)
            .where(Membership.user_id == user.id)
            .where(Membership.organization_id == org.id)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        membership = Membership(
            id=generate_ulid("mem"),
            organization_id=org.id,
            user_id=user.id,
            role=seed.role,
        )
        session.add(membership)


async def _seed_references(
    session: AsyncSession, references: list[SeedReference], brand_map: dict[str, Brand]
) -> None:
    """Seed catalog references linked to brands."""
    for seed in references:
        brand = brand_map.get(seed.brand_slug)
        if brand is None:
            continue
        existing = await _get_reference_by_brand_and_code(session, brand.id, seed.ref_code)
        if existing is not None:
            continue
        reference = Reference(
            id=generate_ulid("ref"),
            brand_id=brand.id,
            ref_code=seed.ref_code,
            model_name=seed.model_name,
            generation=seed.generation,
            attributes=seed.attributes,
            is_active=seed.is_active,
        )
        session.add(reference)


async def _seed_snapshots(
    session: AsyncSession,
    snapshots: list[SeedSnapshot],
    source_map: dict[str, Source],
) -> None:
    """Seed raw snapshots idempotently by (source, external_id, adapter_version, checksum)."""
    for seed in snapshots:
        source = source_map.get(seed.source_key)
        if source is None:
            continue
        existing = await _get_snapshot_by_natural_key(
            session,
            source.id,
            seed.external_id,
            seed.adapter_version,
            seed.checksum,
        )
        if existing is not None:
            continue
        snapshot = RawSnapshot(
            id=generate_ulid("snp"),
            source_id=source.id,
            external_id=seed.external_id,
            adapter_version=seed.adapter_version,
            checksum=seed.checksum,
            raw_payload=seed.raw_payload,
            fetched_at=seed.fetched_at,
        )
        session.add(snapshot)


async def _seed_parsed_listings(
    session: AsyncSession,
    parsed: list[SeedParsedListing],
    source_map: dict[str, Source],
) -> None:
    """Seed parsed listings, linked one-to-one to raw snapshots."""
    for seed in parsed:
        source = source_map.get(seed.source_key)
        if source is None:
            continue
        snapshot = await session.execute(
            select(RawSnapshot)
            .where(RawSnapshot.source_id == source.id)
            .where(RawSnapshot.external_id == seed.external_id)
        )
        snapshot_row = snapshot.scalar_one_or_none()
        if snapshot_row is None:
            continue
        existing = await session.execute(
            select(ParsedListing).where(ParsedListing.snapshot_id == snapshot_row.id)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        listing = ParsedListing(
            id=generate_ulid("prs"),
            snapshot_id=snapshot_row.id,
            parser_version=seed.parser_version,
            listing_price=seed.listing_price,
            price_currency=seed.price_currency,
            listing_title=seed.listing_title,
            description=seed.description,
            parsed_attributes=seed.parsed_attributes,
            external_url=seed.external_url,
            listed_at=seed.listed_at,
        )
        session.add(listing)


async def _seed_normalized_listings(
    session: AsyncSession,
    normalized: list[SeedNormalizedListing],
    source_map: dict[str, Source],
    brand_map: dict[str, Brand],
) -> None:
    """Seed normalized listings, linked one-to-one to parsed listings."""
    for seed in normalized:
        source = source_map.get(seed.source_key)
        if source is None:
            continue
        brand = brand_map.get(seed.reference_slug)
        if brand is None:
            continue
        reference = await _get_reference_by_brand_and_code(session, brand.id, seed.ref_code)
        if reference is None:
            continue
        snapshot = await session.execute(
            select(RawSnapshot)
            .where(RawSnapshot.source_id == source.id)
            .where(RawSnapshot.external_id == seed.external_id)
        )
        snapshot_row = snapshot.scalar_one_or_none()
        if snapshot_row is None:
            continue
        parsed = await session.execute(
            select(ParsedListing).where(ParsedListing.snapshot_id == snapshot_row.id)
        )
        parsed_row = parsed.scalar_one_or_none()
        if parsed_row is None:
            continue
        existing = await _get_normalized_listing_by_source_external(
            session, source.id, seed.external_id
        )
        if existing is not None:
            continue
        listing = NormalizedListing(
            id=generate_ulid("nls"),
            parsed_listing_id=parsed_row.id,
            reference_id=reference.id,
            normalization_version=seed.normalization_version,
            match_confidence=seed.match_confidence,
            match_method=seed.match_method,
            match_features=_json_sanitize(seed.match_features),
            condition=seed.condition,
            set_status=seed.set_status,
            seller_geography=seed.seller_geography,
            normalized_price=seed.normalized_price,
            normalized_currency=seed.normalized_currency,
            fx_rate=seed.fx_rate,
            fx_source=seed.fx_source,
            fx_date=seed.fx_date,
            observation_at=seed.observation_at,
            status=seed.status,
        )
        session.add(listing)


async def _seed_valuations(
    session: AsyncSession,
    valuations: list[SeedValuation],
    source_map: dict[str, Source],
) -> None:
    """Seed valuations idempotently by (listing, model_version)."""
    for seed in valuations:
        source = source_map.get(seed.source_key)
        if source is None:
            continue
        normalized = await _get_normalized_listing_by_source_external(
            session, source.id, seed.external_id
        )
        if normalized is None:
            continue
        existing = await session.execute(
            select(Valuation)
            .where(Valuation.listing_id == normalized.id)
            .where(Valuation.model_version == seed.model_version)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        valuation = Valuation(
            id=generate_ulid("val"),
            listing_id=normalized.id,
            model_version=seed.model_version,
            config_version=seed.config_version,
            cost_assumptions_version=seed.cost_assumptions_version,
            expected_exit_price=seed.expected_exit_price,
            exit_price_currency=seed.exit_price_currency,
            all_in_acquisition=seed.all_in_acquisition,
            expected_net_resale=seed.expected_net_resale,
            expected_net_profit=seed.expected_net_profit,
            roi=seed.roi,
            low_estimate=seed.low_estimate,
            high_estimate=seed.high_estimate,
            confidence=seed.confidence,
            comparable_count=seed.comparable_count,
            sample_dispersion=seed.sample_dispersion,
            adjustment_details=_json_sanitize(seed.adjustment_details),
            risk_reserve_details=_json_sanitize(seed.risk_reserve_details),
            cost_breakdown=_json_sanitize(seed.cost_breakdown),
        )
        session.add(valuation)


async def _seed_opportunities(
    session: AsyncSession,
    opportunities: list[SeedOpportunity],
    org_map: dict[str, Organization],
    source_map: dict[str, Source],
) -> None:
    """Seed opportunities idempotently by (organization, listing, material_version)."""
    for seed in opportunities:
        org = org_map.get(seed.organization_slug)
        if org is None:
            continue
        source = source_map.get(seed.source_key)
        if source is None:
            continue
        normalized = await _get_normalized_listing_by_source_external(
            session, source.id, seed.external_id
        )
        if normalized is None:
            continue
        valuation = await session.execute(
            select(Valuation)
            .where(Valuation.listing_id == normalized.id)
            .order_by(Valuation.created_at.desc())
        )
        valuation_row = valuation.scalar_one_or_none()
        if valuation_row is None:
            continue
        existing = await session.execute(
            select(Opportunity)
            .where(Opportunity.organization_id == org.id)
            .where(Opportunity.listing_id == normalized.id)
            .where(Opportunity.material_version == seed.material_version)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        opportunity = Opportunity(
            id=generate_ulid("opp"),
            organization_id=org.id,
            listing_id=normalized.id,
            valuation_id=valuation_row.id,
            material_version=seed.material_version,
            score=seed.score,
            state=seed.state,
            positive_factors=_json_sanitize(seed.positive_factors),
            negative_factors=_json_sanitize(seed.negative_factors),
            published_at=seed.published_at,
            state_changed_at=seed.state_changed_at,
        )
        session.add(opportunity)


async def _seed_alert_rules(
    session: AsyncSession,
    rules: list[SeedAlertRule],
    org_map: dict[str, Organization],
    user_map: dict[str, User],
) -> dict[tuple[str, str], AlertRule]:
    rule_map: dict[tuple[str, str], AlertRule] = {}
    for seed in rules:
        org = org_map.get(seed.organization_slug)
        user = user_map.get(seed.created_by_email)
        if org is None or user is None:
            continue
        key = (seed.organization_slug, seed.name)
        result = await session.execute(
            select(AlertRule).where(
                AlertRule.organization_id == org.id,
                AlertRule.name == seed.name,
            )
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            rule = AlertRule(
                id=generate_ulid("alr"),
                organization_id=org.id,
                created_by=user.id,
                name=seed.name,
                filters=_json_sanitize(seed.filters),
                channels=seed.channels,
                cooldown_minutes=seed.cooldown_minutes,
                is_enabled=seed.is_enabled,
            )
            session.add(rule)
        rule_map[key] = rule
    return rule_map


async def _seed_alert_deliveries(
    session: AsyncSession,
    deliveries: list[SeedAlertDelivery],
    org_map: dict[str, Organization],
    user_map: dict[str, User],
    source_map: dict[str, Source],
    rule_map: dict[tuple[str, str], AlertRule],
) -> None:
    for seed in deliveries:
        org = org_map.get(seed.organization_slug)
        user = user_map.get(seed.user_email)
        source = source_map.get(seed.source_key)
        rule = rule_map.get((seed.organization_slug, seed.rule_name))
        if org is None or user is None or source is None or rule is None:
            continue
        existing = await session.execute(
            select(AlertDelivery).where(AlertDelivery.idempotency_key == seed.idempotency_key)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        opportunity = await _get_opportunity_by_seed_key(
            session,
            org.id,
            source.id,
            seed.external_id,
            seed.material_version,
        )
        if opportunity is None:
            continue
        session.add(
            AlertDelivery(
                id=generate_ulid("ald"),
                organization_id=org.id,
                rule_id=rule.id,
                user_id=user.id,
                opportunity_id=opportunity.id,
                material_version=seed.material_version,
                channel=seed.channel,
                idempotency_key=seed.idempotency_key,
                delivery_status=seed.delivery_status,
                provider_message_id=seed.provider_message_id,
            )
        )


async def _seed_feedback(
    session: AsyncSession,
    feedback_items: list[SeedFeedback],
    org_map: dict[str, Organization],
    user_map: dict[str, User],
    source_map: dict[str, Source],
) -> None:
    for seed in feedback_items:
        org = org_map.get(seed.organization_slug)
        user = user_map.get(seed.user_email)
        source = source_map.get(seed.source_key)
        if org is None or user is None or source is None:
            continue
        existing = await session.execute(
            select(Feedback).where(Feedback.idempotency_key == seed.idempotency_key)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        opportunity = await _get_opportunity_by_seed_key(
            session,
            org.id,
            source.id,
            seed.external_id,
            seed.material_version,
        )
        if opportunity is None:
            continue
        opportunity.state = transition_opportunity_state(opportunity.state, seed.decision)
        opportunity.state_changed_at = seed.created_at
        session.add(
            Feedback(
                id=generate_ulid("fbk"),
                organization_id=org.id,
                user_id=user.id,
                opportunity_id=opportunity.id,
                decision=seed.decision,
                notes=seed.notes,
                idempotency_key=seed.idempotency_key,
                created_at=seed.created_at,
            )
        )


async def _seed_trade_outcomes(
    session: AsyncSession,
    outcomes: list[SeedTradeOutcome],
    org_map: dict[str, Organization],
    user_map: dict[str, User],
    source_map: dict[str, Source],
    brand_map: dict[str, Brand],
) -> None:
    for seed in outcomes:
        org = org_map.get(seed.organization_slug)
        user = user_map.get(seed.user_email)
        source = source_map.get(seed.source_key)
        brand = brand_map.get(seed.reference_slug)
        if org is None or user is None or source is None or brand is None:
            continue
        existing = await session.execute(
            select(TradeOutcome).where(TradeOutcome.idempotency_key == seed.idempotency_key)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        opportunity = await _get_opportunity_by_seed_key(
            session,
            org.id,
            source.id,
            seed.external_id,
            seed.material_version,
        )
        reference = await _get_reference_by_brand_and_code(session, brand.id, seed.ref_code)
        if opportunity is None or reference is None:
            continue
        session.add(
            TradeOutcome(
                id=generate_ulid("out"),
                organization_id=org.id,
                user_id=user.id,
                opportunity_id=opportunity.id,
                reference_id=reference.id,
                acquisition_price=seed.acquisition_price,
                acquisition_currency=seed.acquisition_currency,
                resale_price=seed.resale_price,
                resale_currency=seed.resale_currency,
                actual_profit=seed.actual_profit,
                days_to_sell=seed.days_to_sell,
                idempotency_key=seed.idempotency_key,
                created_at=seed.created_at,
            )
        )


async def _seed_subscriptions(
    session: AsyncSession,
    subscriptions: list[SeedSubscription],
    org_map: dict[str, Organization],
) -> None:
    for seed in subscriptions:
        org = org_map.get(seed.organization_slug)
        if org is None:
            continue
        existing = await session.execute(
            select(Subscription).where(
                Subscription.paypal_subscription_id == seed.paypal_subscription_id
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue
        session.add(
            Subscription(
                id=generate_ulid("sub"),
                organization_id=org.id,
                paypal_payer_id=seed.paypal_payer_id,
                paypal_subscription_id=seed.paypal_subscription_id,
                status=seed.status,
                plan_id=seed.plan_id,
                current_period_start=seed.current_period_start,
                current_period_end=seed.current_period_end,
                trial_end=seed.trial_end,
            )
        )


async def _seed_feature_flags(
    session: AsyncSession,
    flags: list[SeedFeatureFlag],
    org_map: dict[str, Organization],
) -> None:
    for seed in flags:
        result = await session.execute(select(FeatureFlag).where(FeatureFlag.key == seed.key))
        if result.scalar_one_or_none() is not None:
            continue
        session.add(
            FeatureFlag(
                id=generate_ulid("flg"),
                key=seed.key,
                description=seed.description,
                enabled=seed.enabled,
                organization_ids=(
                    [org_map[slug].id for slug in seed.organization_slugs if slug in org_map]
                    if seed.organization_slugs is not None
                    else None
                ),
                rollout_pct=seed.rollout_pct,
                expires_at=seed.expires_at,
            )
        )


async def _seed_audit_events(
    session: AsyncSession,
    events: list[SeedAuditEvent],
    org_map: dict[str, Organization],
    user_map: dict[str, User],
) -> None:
    for seed in events:
        result = await session.execute(
            select(AuditEvent).where(
                AuditEvent.action == seed.action,
                AuditEvent.resource_type == seed.resource_type,
                AuditEvent.resource_id == seed.resource_id,
            )
        )
        if result.scalar_one_or_none() is not None:
            continue
        org = org_map.get(seed.organization_slug) if seed.organization_slug else None
        user = user_map.get(seed.user_email) if seed.user_email else None
        session.add(
            AuditEvent(
                id=generate_ulid("aud"),
                organization_id=org.id if org else None,
                user_id=user.id if user else None,
                action=seed.action,
                resource_type=seed.resource_type,
                resource_id=seed.resource_id,
                details=_json_sanitize(seed.details),
            )
        )


async def seed_database(session: AsyncSession | None = None) -> dict[str, int]:
    """Run the full seed pipeline against the given session (or a new one).

    Returns a dict of counts per entity type. The operation is idempotent.
    """
    counts: dict[str, int] = {
        "organizations": 0,
        "users": 0,
        "memberships": 0,
        "brands": 0,
        "sources": 0,
        "references": 0,
        "snapshots": 0,
        "parsed_listings": 0,
        "normalized_listings": 0,
        "valuations": 0,
        "opportunities": 0,
        "alert_rules": 0,
        "alert_deliveries": 0,
        "feedback": 0,
        "trade_outcomes": 0,
        "subscriptions": 0,
        "feature_flags": 0,
        "audit_events": 0,
    }

    own_session = session is None
    if own_session:
        await initialize_dev_sqlite_schema()
        async with async_session() as session:
            return await _seed_within_session(session, counts)
    assert session is not None
    return await _seed_within_session(session, counts)


async def _seed_within_session(session: AsyncSession, counts: dict[str, int]) -> dict[str, int]:
    # Create all tables if they don't exist
    async with session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    org_map = await _seed_organizations(session, SEED_ORGANIZATIONS)
    counts["organizations"] = len(org_map)

    user_map = await _seed_users(session, SEED_USERS)
    counts["users"] = len(user_map)

    brand_map = await _seed_brands(session, SEED_BRANDS)
    counts["brands"] = len(brand_map)

    source_map = await _seed_sources(session, SEED_SOURCES)
    counts["sources"] = len(source_map)

    await _seed_memberships(session, SEED_MEMBERSHIPS, user_map, org_map)
    counts["memberships"] = len(SEED_MEMBERSHIPS)

    await _seed_references(session, SEED_REFERENCES, brand_map)
    counts["references"] = len(SEED_REFERENCES)

    await _seed_snapshots(session, SEED_SNAPSHOTS, source_map)
    await _seed_parsed_listings(session, SEED_PARSED_LISTINGS, source_map)
    await _seed_normalized_listings(session, SEED_NORMALIZED_LISTINGS, source_map, brand_map)
    await _seed_valuations(session, SEED_VALUATIONS, source_map)
    await _seed_opportunities(session, SEED_OPPORTUNITIES, org_map, source_map)
    await session.flush()

    rule_map = await _seed_alert_rules(session, SEED_ALERT_RULES, org_map, user_map)
    await _seed_alert_deliveries(
        session,
        SEED_ALERT_DELIVERIES,
        org_map,
        user_map,
        source_map,
        rule_map,
    )
    await _seed_feedback(session, SEED_FEEDBACK, org_map, user_map, source_map)
    await _seed_trade_outcomes(
        session,
        SEED_TRADE_OUTCOMES,
        org_map,
        user_map,
        source_map,
        brand_map,
    )
    await _seed_subscriptions(session, SEED_SUBSCRIPTIONS, org_map)
    await _seed_feature_flags(session, SEED_FEATURE_FLAGS, org_map)
    await _seed_audit_events(session, SEED_AUDIT_EVENTS, org_map, user_map)

    counts["snapshots"] = len(SEED_SNAPSHOTS)
    counts["parsed_listings"] = len(SEED_PARSED_LISTINGS)
    counts["normalized_listings"] = len(SEED_NORMALIZED_LISTINGS)
    counts["valuations"] = len(SEED_VALUATIONS)
    counts["opportunities"] = len(SEED_OPPORTUNITIES)
    counts["alert_rules"] = len(SEED_ALERT_RULES)
    counts["alert_deliveries"] = len(SEED_ALERT_DELIVERIES)
    counts["feedback"] = len(SEED_FEEDBACK)
    counts["trade_outcomes"] = len(SEED_TRADE_OUTCOMES)
    counts["subscriptions"] = len(SEED_SUBSCRIPTIONS)
    counts["feature_flags"] = len(SEED_FEATURE_FLAGS)
    counts["audit_events"] = len(SEED_AUDIT_EVENTS)

    await session.commit()
    return counts


async def reset_and_seed(session: AsyncSession | None = None) -> dict[str, int]:
    """Delete all seed-relevant tables and re-seed from scratch.

    This is destructive: it removes seeded data and all records in the
    organizations, catalog, listing, opportunity, alert, feedback, billing,
    feature-flag, and audit tables. Intended for local development only.
    """
    own_session = session is None
    if own_session:
        await initialize_dev_sqlite_schema()
        async with async_session() as session:
            return await _reset_and_seed_within_session(session)
    assert session is not None
    return await _reset_and_seed_within_session(session)


async def _reset_and_seed_within_session(session: AsyncSession) -> dict[str, int]:
    # Delete in dependency order (children first)
    await session.execute(text("DELETE FROM alert_deliveries"))
    await session.execute(text("DELETE FROM feedbacks"))
    await session.execute(text("DELETE FROM trade_outcomes"))
    await session.execute(text("DELETE FROM alert_rules"))
    await session.execute(text("DELETE FROM subscriptions"))
    await session.execute(text("DELETE FROM feature_flags"))
    await session.execute(text("DELETE FROM audit_events"))
    await session.execute(text("DELETE FROM opportunities"))
    await session.execute(text("DELETE FROM valuations"))
    await session.execute(text("DELETE FROM normalized_listings"))
    await session.execute(text("DELETE FROM parsed_listings"))
    await session.execute(text("DELETE FROM raw_snapshots"))
    await session.execute(text("DELETE FROM watch_list_entries"))
    await session.execute(text("DELETE FROM watch_lists"))
    await session.execute(text("DELETE FROM aliases"))
    await session.execute(text('DELETE FROM "references"'))
    await session.execute(text("DELETE FROM brands"))
    await session.execute(text("DELETE FROM sources"))
    await session.execute(text("DELETE FROM memberships"))
    await session.execute(text("DELETE FROM users"))
    await session.execute(text("DELETE FROM organizations"))
    await session.commit()

    counts: dict[str, int] = {}
    return await _seed_within_session(session, counts)
