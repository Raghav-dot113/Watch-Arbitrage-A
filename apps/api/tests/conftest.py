"""Shared test configuration.

Tests must not inherit the developer's local `.env` choices. In particular,
hackathon deployments set `CHRONOARB_AUTH_MODE=disabled`, while unit tests
exercise the development auth contract. Individual tests can still override
these values with `monkeypatch`.
"""

from __future__ import annotations

import pytest
from apps.api.settings import settings


@pytest.fixture(autouse=True)
def isolate_global_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "auth_mode", "dev")
