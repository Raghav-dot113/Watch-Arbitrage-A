"""CLI entry point for running the ChronoArb seed.

Usage:
    python -m apps.api.seed
    python -m apps.api.seed --reset
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from apps.api.seed.runner import reset_and_seed, seed_database

logger = logging.getLogger("chronoarb.seed")


async def _main(reset: bool) -> None:
    if reset:
        logger.info("Resetting and seeding database...")
        counts = await reset_and_seed()
    else:
        logger.info("Seeding database (idempotent)...")
        counts = await seed_database()

    total = sum(counts.values())
    parts = [f"{k}={v}" for k, v in counts.items()]
    logger.info("Seed complete: %s (%d total records)", " ".join(parts), total)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Seed ChronoArb demo/development data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all seed-relevant tables and re-seed from scratch (destructive)",
    )
    args = parser.parse_args()
    asyncio.run(_main(reset=args.reset))


if __name__ == "__main__":
    main()
