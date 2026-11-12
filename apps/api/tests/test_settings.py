from __future__ import annotations

import logging
from pathlib import Path

import pytest
from apps.api.main import create_app
from apps.api.settings import PROJECT_ROOT, Settings, settings
from pydantic import SecretStr


def test_settings_env_file_uses_absolute_repository_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = Settings.model_config["env_file"]

    assert env_file == PROJECT_ROOT / ".env"
    assert isinstance(env_file, Path)
    assert env_file.is_absolute()


@pytest.mark.parametrize(
    "variable_name",
    ["CHRONOARB_CHANNEL3_API_KEY", "CHANNEL3_API_KEY"],
)
def test_settings_load_channel3_key_from_env_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    variable_name: str,
) -> None:
    monkeypatch.delenv("CHRONOARB_CHANNEL3_API_KEY", raising=False)
    monkeypatch.delenv("CHANNEL3_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(f"{variable_name}=test-channel3-key\n", encoding="utf-8")

    configured = Settings(_env_file=env_file)

    assert configured.channel3_api_key.get_secret_value() == "test-channel3-key"


@pytest.mark.parametrize(
    ("api_key", "configured"),
    [("", "false"), ("test-channel3-secret", "true")],
)
async def test_startup_logs_channel3_key_presence_without_secret(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    api_key: str,
    configured: str,
) -> None:
    monkeypatch.setattr(settings, "channel3_api_key", SecretStr(api_key))
    monkeypatch.setattr("apps.api.main.is_dev_sqlite_database", lambda: False)
    app = create_app()

    with caplog.at_level(logging.INFO, logger="chronoarb.api"):
        async with app.router.lifespan_context(app):
            pass

    assert f"channel3_api_key_configured={configured}" in caplog.text
    if api_key:
        assert api_key not in caplog.text
