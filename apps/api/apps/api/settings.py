from __future__ import annotations

from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="CHRONOARB_",
        extra="ignore",
    )

    app_name: str = "ChronoArb"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    environment: Literal["local", "test", "staging", "production"] = "local"
    auth_mode: Literal["dev", "oidc"] = "dev"
    dev_jwt_secret: SecretStr = SecretStr("")
    jwt_issuer: str = "chronoarb-dev"
    jwt_audience: str = "chronoarb-api"
    cognito_jwks_url: str = ""
    cognito_issuer: str = ""
    cognito_audience: str = ""
    stripe_webhook_secret: str = ""
    auth_token_ttl_seconds: int = 900
    platform_ops_subjects: str = ""
    cors_origins: str = "http://localhost:3000"
    integration_encryption_key: SecretStr = SecretStr("")
    channel3_api_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices(
            "CHRONOARB_CHANNEL3_API_KEY",
            "CHANNEL3_API_KEY",
        ),
    )
    telegram_bot_token: SecretStr = SecretStr("")
    telegram_bot_username: str = ""
    paypal_client_id: str = ""
    paypal_client_secret: SecretStr = SecretStr("")
    paypal_webhook_id: str = ""
    paypal_plan_ids: dict[str, str] = Field(default_factory=dict)
    paypal_return_url: str = "http://localhost:3000/settings/organization?checkout=success"
    paypal_cancel_url: str = "http://localhost:3000/settings/organization?checkout=cancel"
    paypal_api_base_url: str = "https://api-m.sandbox.paypal.com"
    provider_request_timeout_seconds: float = 10

    # Default is SQLite (aiosqlite) for local development.
    # PostgreSQL async drivers (asyncpg, psycopg) have unresolved compatibility
    # issues with Python 3.14 as of 2026-08-03. Production must override via
    # CHRONOARB_DATABASE_URL=postgresql+asyncpg://... (CI runs Python 3.13).
    database_url: str = "sqlite+aiosqlite:///chronoarb.db"

    @field_validator("database_url")
    @classmethod
    def resolve_relative_sqlite_database_path(cls, value: str) -> str:
        url = make_url(value)
        database = url.database
        if (
            url.get_backend_name() != "sqlite"
            or not database
            or database == ":memory:"
            or database.startswith("file:")
        ):
            return value

        database_path = Path(database)
        if not database_path.is_absolute():
            database_path = PROJECT_ROOT / database_path
        return url.set(database=str(database_path.resolve())).render_as_string(hide_password=False)

    @field_validator("auth_token_ttl_seconds")
    @classmethod
    def validate_auth_token_ttl(cls, value: int) -> int:
        if not 1 <= value <= 900:
            raise ValueError("Authentication token lifetime must be between 1 and 900 seconds")
        return value

    @field_validator("jwt_issuer", "jwt_audience")
    @classmethod
    def validate_non_empty_auth_claim(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("JWT issuer and audience must not be empty")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",")]
        if not origins or any(not origin for origin in origins):
            raise ValueError("CORS origins must be a comma-separated list of explicit origins")
        normalized_origins: list[str] = []
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.hostname is None
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path not in {"", "/"}
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                raise ValueError(f"Invalid CORS origin: {origin!r}")
            try:
                _port = parsed.port
            except ValueError as exc:
                raise ValueError(f"Invalid CORS origin: {origin!r}") from exc
            normalized_origins.append(f"{parsed.scheme}://{parsed.netloc}")
        return ",".join(normalized_origins)

    @field_validator(
        "paypal_return_url",
        "paypal_cancel_url",
        "paypal_api_base_url",
    )
    @classmethod
    def validate_provider_urls(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.hostname is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise ValueError("Provider URLs must be absolute HTTP(S) URLs without fragments")
        return value

    @field_validator("paypal_api_base_url")
    @classmethod
    def validate_paypal_api_host(cls, value: str) -> str:
        parsed = urlsplit(value)
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("PayPal API URL must use an official PayPal API host") from exc
        if (
            parsed.hostname not in {"api-m.sandbox.paypal.com", "api-m.paypal.com"}
            or parsed.path not in {"", "/"}
            or parsed.query
            or port not in {None, 443}
        ):
            raise ValueError("PayPal API URL must use an official PayPal API host")
        return value

    @field_validator("provider_request_timeout_seconds")
    @classmethod
    def validate_provider_timeout(cls, value: float) -> float:
        if not 0.1 <= value <= 30:
            raise ValueError("Provider request timeout must be between 0.1 and 30 seconds")
        return value

    @model_validator(mode="after")
    def disallow_development_auth_outside_local_environments(self) -> Settings:
        if self.environment in {"staging", "production"} and self.auth_mode == "dev":
            raise ValueError("Development authentication is only allowed in local or test")
        if self.environment in {"staging", "production"}:
            provider_urls = (
                self.paypal_return_url,
                self.paypal_cancel_url,
                self.paypal_api_base_url,
            )
            if any(urlsplit(url).scheme != "https" for url in provider_urls):
                raise ValueError("Provider URLs must use HTTPS outside local and test")
            paypal_host = urlsplit(self.paypal_api_base_url).hostname
            allowed_hosts = {"api-m.sandbox.paypal.com", "api-m.paypal.com"}
            if paypal_host not in allowed_hosts:
                raise ValueError("PayPal API base URL must use an official PayPal API host")
            if self.environment == "production" and paypal_host != "api-m.paypal.com":
                raise ValueError("Production must use the live PayPal API host")
        return self

    @property
    def platform_ops_subject_allowlist(self) -> frozenset[str]:
        return frozenset(
            subject.strip() for subject in self.platform_ops_subjects.split(",") if subject.strip()
        )

    @property
    def cors_origin_allowlist(self) -> tuple[str, ...]:
        return tuple(self.cors_origins.split(","))


settings = Settings()
