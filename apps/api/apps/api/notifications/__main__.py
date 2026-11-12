"""Notification dispatcher process.

Usage:
    python -m apps.api.notifications --once
    python -m apps.api.notifications --interval 15
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import signal

from apps.api.infrastructure.database import (
    async_session,
    engine,
    initialize_dev_sqlite_schema,
)
from apps.api.integrations.application.telegram import TelegramService
from apps.api.notifications.application.service import DispatchSummary, NotificationService
from apps.api.settings import settings

logger = logging.getLogger("chronoarb.notifications")


async def _dispatch(limit: int) -> DispatchSummary:
    async with async_session() as session:
        return await NotificationService(session).dispatch_once(limit=limit)


async def _main(*, once: bool, interval: float, limit: int) -> int:
    if not settings.telegram_bot_token.get_secret_value().strip():
        logger.error(
            "TELEGRAM_BOT_TOKEN is not configured; set it in .env before starting notifications"
        )
        return 1

    await initialize_dev_sqlite_schema()
    stop_requested = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):  # Windows event loop fallback
            loop.add_signal_handler(sig, stop_requested.set)

    try:
        while True:
            try:
                summary = await _dispatch(limit)
            except Exception:
                logger.exception("notification dispatch pass failed")
                if once:
                    return 1
            else:
                if summary.total:
                    logger.info(
                        "notification dispatch pass complete",
                        extra={
                            "deliveries_sent": summary.deliveries_sent,
                            "deliveries_failed": summary.deliveries_failed,
                            "deliveries_suppressed": summary.deliveries_suppressed,
                            "test_notifications_sent": summary.test_notifications_sent,
                            "test_notifications_failed": summary.test_notifications_failed,
                        },
                    )
                if once:
                    failed = summary.deliveries_failed or summary.test_notifications_failed
                    return 1 if failed else 0

            try:
                await asyncio.wait_for(stop_requested.wait(), timeout=interval)
            except TimeoutError:
                continue
            break
    finally:
        await engine.dispose()

    return 0


async def _send_configured_test_message() -> int:
    chat_id = settings.telegram_chat_id.strip()
    if not chat_id:
        logger.error(
            "CHRONOARB_TELEGRAM_CHAT_ID is not configured; set it in .env to send a test message"
        )
        return 1
    if not settings.telegram_bot_token.get_secret_value().strip():
        logger.error("TELEGRAM_BOT_TOKEN is not configured; set it in .env to send a test message")
        return 1

    result = await TelegramService().send_test_alert(chat_id, rule_id="cli_test")
    if result.success:
        logger.info(
            "Telegram test message delivered",
            extra={"provider_message_id": result.provider_message_id},
        )
        return 0
    logger.error("Telegram test message failed: %s", result.error_message or "unknown error")
    return 1


def main() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
        force=True,
    )
    parser = argparse.ArgumentParser(description="Deliver pending ChronoArb alerts")
    parser.add_argument("--once", action="store_true", help="Run one pass and exit")
    parser.add_argument(
        "--test-message",
        action="store_true",
        help="Send one test message to CHRONOARB_TELEGRAM_CHAT_ID and exit",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=15.0,
        help="Seconds between passes when not using --once (default: 15)",
    )
    parser.add_argument("--limit", type=int, default=50, help="Maximum items per queue per pass")
    args = parser.parse_args()
    if not 1 <= args.limit <= 200:
        parser.error("--limit must be between 1 and 200")
    if args.interval < 1:
        parser.error("--interval must be at least 1 second")

    if args.test_message:
        raise SystemExit(asyncio.run(_send_configured_test_message()))

    exit_code = asyncio.run(_main(once=args.once, interval=args.interval, limit=args.limit))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
