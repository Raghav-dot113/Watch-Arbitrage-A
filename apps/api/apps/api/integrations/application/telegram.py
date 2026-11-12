from __future__ import annotations

import asyncio
import html
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
from apps.api.settings import settings

logger = logging.getLogger("chronoarb.integrations.telegram")

TELEGRAM_API_BASE = "https://api.telegram.org"


@dataclass(frozen=True)
class TelegramSendResult:
    success: bool
    provider_message_id: str | None = None
    error_message: str | None = None
    status_code: int | None = None


def escape_html(value: Any) -> str:
    """Escapes user and provider inputs for safe inclusion in Telegram HTML messages."""
    return html.escape(str(value) if value is not None else "")


def _first_value(opportunity: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = opportunity.get(key)
        if value is not None and value != "":
            return value
    return None


def _as_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError):
        return None


def _as_yes_no(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return "Yes" if value.strip().lower() in {"true", "yes", "1", "full"} else "No"
    return "Yes" if bool(value) else "No"


def _format_confidence(value: Any) -> str | None:
    confidence = _as_decimal(value)
    if confidence is None:
        return None
    if Decimal("0") <= confidence <= Decimal("1"):
        confidence *= Decimal("100")
    if not Decimal("0") <= confidence <= Decimal("100"):
        return None
    return f"{confidence:.0f}%"


def _format_data_age(value: Any) -> str | None:
    observed_at = value
    if isinstance(value, str):
        try:
            observed_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(observed_at, datetime):
        return None
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    seconds = max(0, int((datetime.now(UTC) - observed_at).total_seconds()))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h {minutes % 60}m"
    return f"{hours // 24}d {hours % 24}h"


def format_opportunity_alert(
    opportunity: dict[str, Any],
    *,
    base_url: str = "http://localhost:3000",
    rule_name: str | None = None,
) -> str:
    """Formats an opportunity into a high-visibility, actionable HTML alert for dealers."""
    brand = escape_html(_first_value(opportunity, "brand", "brand_name") or "Watch")
    model = escape_html(_first_value(opportunity, "model", "model_name", "title") or "Opportunity")
    reference = escape_html(
        _first_value(opportunity, "reference_number", "reference", "ref_code") or "N/A"
    )
    condition = escape_html(_first_value(opportunity, "condition") or "Pre-owned")
    source = escape_html(
        _first_value(opportunity, "source_name", "source_display_name", "source") or "Market Feed"
    )
    currency = escape_html(
        _first_value(
            opportunity,
            "currency",
            "normalized_currency",
            "listing_price_currency",
            "exit_price_currency",
        )
        or "USD"
    )

    box_raw = _first_value(opportunity, "has_box", "box")
    papers_raw = _first_value(opportunity, "has_papers", "papers")
    if box_raw is None and papers_raw is None:
        set_status = str(_first_value(opportunity, "set_status") or "").lower()
        if set_status == "full_set":
            box, papers = "Yes", "Yes"
        elif set_status in {"watch_only", "no_box_no_papers"}:
            box, papers = "No", "No"
        else:
            box, papers = "—", "—"
    else:
        box = _as_yes_no(box_raw)
        papers = _as_yes_no(papers_raw)

    ask_price = _as_decimal(
        _first_value(
            opportunity,
            "ask_price",
            "price",
            "normalized_price",
            "listing_price",
        )
    )
    market_value = _as_decimal(
        _first_value(
            opportunity,
            "estimated_market_value",
            "market_value",
            "expected_exit_price",
            "expected_net_resale",
        )
    )
    opp_id = _first_value(opportunity, "id", "opportunity_id") or ""
    material_version = opportunity.get("material_version", 1)
    confidence = _format_confidence(opportunity.get("confidence"))
    valuation_version = _first_value(
        opportunity,
        "valuation_version",
        "model_version",
        "valuation_model_version",
    )
    cost_assumptions_version = _first_value(opportunity, "cost_assumptions_version")
    data_age = _format_data_age(_first_value(opportunity, "observation_at", "listed_at"))

    ask_str = f"{currency} {ask_price:,.2f}" if ask_price is not None else "Price on Request"
    val_str = f"{currency} {market_value:,.2f}" if market_value is not None else "N/A"

    spread_section = ""
    if ask_price is not None and market_value is not None:
        spread = market_value - ask_price
        pct = (spread / ask_price * Decimal(100)) if ask_price > 0 else Decimal(0)
        spread_sign = "+" if spread >= 0 else ""
        spread_section = (
            f"<b>Spread:</b> <code>{spread_sign}{currency} {spread:,.2f} ({pct:+.1f}%)</code>\n"
        )

    opp_url = f"{base_url.rstrip('/')}/opportunities/{opp_id}" if opp_id else base_url
    rule_header = f" | Rule: <i>{escape_html(rule_name)}</i>" if rule_name else ""

    metadata: list[str] = []
    if confidence is not None:
        metadata.append(f"Confidence {confidence}")
    if data_age is not None:
        metadata.append(f"Data age {data_age}")
    if valuation_version is not None:
        metadata.append(f"Valuation {escape_html(valuation_version)}")
    if cost_assumptions_version is not None:
        metadata.append(f"Costs {escape_html(cost_assumptions_version)}")

    lines = [
        f"🚨 <b>ChronoArb Deal Alert</b>{rule_header}",
        "",
        f"⌚ <b>{brand} — {model}</b>",
        f"<b>Ref:</b> <code>{reference}</code>",
        f"<b>Condition:</b> {condition} | <b>Box:</b> {box} | <b>Papers:</b> {papers}",
        "",
        f"<b>Ask Price:</b> <code>{ask_str}</code>",
        f"<b>Est. Market:</b> <code>{val_str}</code>",
    ]
    if spread_section:
        lines.append(spread_section.strip())

    lines.extend(
        [
            f"<b>Source:</b> {source}",
            "",
            f'🔗 <a href="{escape_html(opp_url)}">View Deal in ChronoArb</a>',
        ]
    )
    if metadata:
        lines.extend(["", f"📊 <i>{' • '.join(metadata)} • Material v{material_version}</i>"])
    return "\n".join(lines)


def format_test_alert(
    *,
    organization_id: str | None = None,
    rule_id: str | None = None,
    trace_id: str | None = None,
) -> str:
    """Formats a test alert confirming successful Telegram channel configuration."""
    now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    org_str = escape_html(organization_id or "default")
    rule_str = escape_html(rule_id or "manual_test")
    trace_str = escape_html(trace_id or "direct")

    return (
        "🔔 <b>ChronoArb Alert Integration Test</b>\n\n"
        "Your Telegram alert integration is active and connected to your ChronoArb workspace!\n"
        "You will receive instant alerts for qualifying dealer opportunities right here on "
        "your phone.\n\n"
        f"• <b>Workspace:</b> <code>{org_str}</code>\n"
        f"• <b>Rule ID:</b> <code>{rule_str}</code>\n"
        f"• <b>Trace ID:</b> <code>{trace_str}</code>\n"
        f"• <b>Timestamp:</b> <code>{now_str}</code>\n\n"
        "<i>ChronoArb Dealer Acquisition Intelligence</i>"
    )


class TelegramService:
    """Asynchronous client for Telegram Bot API adhering to ChronoArb reliability standards."""

    def __init__(
        self,
        bot_token: str | None = None,
        *,
        timeout: float | None = None,
        max_retries: int = 2,
    ) -> None:
        self._bot_token = (
            bot_token.strip()
            if bot_token
            else settings.telegram_bot_token.get_secret_value().strip()
        )
        self._timeout = (
            timeout if timeout is not None else settings.provider_request_timeout_seconds
        )
        self._max_retries = max(0, min(max_retries, 5))

    @property
    def is_configured(self) -> bool:
        return bool(self._bot_token)

    async def send_message(
        self,
        chat_id: str,
        text: str,
        *,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False,
        trace_id: str | None = None,
    ) -> TelegramSendResult:
        if not self.is_configured:
            return TelegramSendResult(
                success=False,
                error_message="Telegram bot token is not configured in settings or environment.",
            )
        clean_chat_id = str(chat_id).strip()
        if not clean_chat_id:
            return TelegramSendResult(
                success=False,
                error_message="Telegram chat_id is required.",
            )

        endpoint = f"{TELEGRAM_API_BASE}/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": clean_chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        attempts = 0
        last_error = ""
        last_status_code: int | None = None

        while attempts <= self._max_retries:
            attempts += 1
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(endpoint, json=payload)
                    last_status_code = response.status_code

                    if response.is_success:
                        data = response.json()
                        message_id = str(data.get("result", {}).get("message_id") or "")
                        logger.info(
                            "Telegram message sent successfully",
                            extra={
                                "trace_id": trace_id,
                                "chat_id": clean_chat_id,
                                "message_id": message_id,
                            },
                        )
                        return TelegramSendResult(
                            success=True,
                            provider_message_id=message_id,
                            status_code=last_status_code,
                        )

                    # Handle 4xx Client Errors (non-retryable)
                    if 400 <= last_status_code < 500:
                        try:
                            err_body = response.json()
                            desc = err_body.get("description", response.text)
                        except Exception:
                            desc = response.text
                        last_error = f"Telegram API client error ({last_status_code}): {desc}"
                        logger.warning(
                            "Telegram API rejected request (non-retryable)",
                            extra={
                                "trace_id": trace_id,
                                "chat_id": clean_chat_id,
                                "status_code": last_status_code,
                                "error": desc,
                            },
                        )
                        return TelegramSendResult(
                            success=False,
                            error_message=last_error,
                            status_code=last_status_code,
                        )

                    # 5xx Server Error - eligible for bounded retry
                    last_error = f"Telegram API server error ({last_status_code})"

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = f"Network or timeout error contacting Telegram API: {exc}"
                logger.warning(
                    "Transient error contacting Telegram API",
                    extra={
                        "trace_id": trace_id,
                        "attempt": attempts,
                        "error": str(exc),
                    },
                )

            if attempts <= self._max_retries:
                backoff = 0.5 * (2 ** (attempts - 1))
                await asyncio.sleep(backoff)

        logger.error(
            "Exhausted retries delivering Telegram notification",
            extra={
                "trace_id": trace_id,
                "chat_id": clean_chat_id,
                "last_error": last_error,
            },
        )
        return TelegramSendResult(
            success=False,
            error_message=last_error,
            status_code=last_status_code,
        )

    async def send_test_alert(
        self,
        chat_id: str,
        *,
        organization_id: str | None = None,
        rule_id: str | None = None,
        trace_id: str | None = None,
    ) -> TelegramSendResult:
        """Sends a formatted test alert to the specified chat ID."""
        text = format_test_alert(
            organization_id=organization_id,
            rule_id=rule_id,
            trace_id=trace_id,
        )
        return await self.send_message(chat_id, text, trace_id=trace_id)

    async def send_opportunity_alert(
        self,
        chat_id: str,
        opportunity: dict[str, Any],
        *,
        rule_name: str | None = None,
        base_url: str = "http://localhost:3000",
        trace_id: str | None = None,
    ) -> TelegramSendResult:
        """Sends a formatted opportunity alert to the specified chat ID."""
        text = format_opportunity_alert(
            opportunity,
            base_url=base_url,
            rule_name=rule_name,
        )
        return await self.send_message(chat_id, text, trace_id=trace_id)
