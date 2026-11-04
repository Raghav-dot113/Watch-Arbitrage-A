from __future__ import annotations

from typing import Literal
from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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
    auth_token_ttl_seconds: int = 900
    platform_ops_subjects: str = ""
    cors_origins: str = "http://localhost:3000"

    # Default is SQLite (aiosqlite) for local development.
    # PostgreSQL async drivers (asyncpg, psycopg) have unresolved compatibility
    # issues with Python 3.14 as of 2026-08-03. Production must override via
    # CHRONOARB_DATABASE_URL=postgresql+asyncpg://... (CI runs Python 3.13).
    database_url: str = "sqlite+aiosqlite:///chronoarb.db"

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

    @model_validator(mode="after")
    def disallow_development_auth_outside_local_environments(self) -> Settings:
        if self.environment in {"staging", "production"} and self.auth_mode == "dev":
            raise ValueError("Development authentication is only allowed in local or test")
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
