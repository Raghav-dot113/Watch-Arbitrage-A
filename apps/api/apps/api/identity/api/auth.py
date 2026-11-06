from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import unquote

import httpx
from apps.api.settings import settings
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class UnauthorizedError(Exception):
    pass


_bearer = HTTPBearer(auto_error=False)
_bearer_dependency = Depends(_bearer)


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def verify_dev_token(token: str) -> str:
    if settings.auth_mode not in {"local", "test"}:
        raise UnauthorizedError
    if len(settings.dev_jwt_secret) < 32:
        raise UnauthorizedError

    parts = token.split(".")
    if len(parts) != 3:
        raise UnauthorizedError

    header_segment, payload_segment, signature_segment = parts
    try:
        header: dict[str, Any] = json.loads(_base64url_decode(header_segment))
        payload: dict[str, Any] = json.loads(_base64url_decode(payload_segment))
        signature = _base64url_decode(signature_segment)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise UnauthorizedError from None

    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise UnauthorizedError

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected = hmac.new(
        settings.dev_jwt_secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(signature, expected):
        raise UnauthorizedError

    expires_at = payload.get("exp")
    subject = payload.get("sub")
    if not isinstance(expires_at, int) or expires_at <= int(time.time()):
        raise UnauthorizedError
    if not isinstance(subject, str) or not subject:
        raise UnauthorizedError
    return subject


_jwks_cache: dict[str, Any] = {}


def _rsa_verify(message: bytes, signature: bytes, jwk: dict[str, Any]) -> bool:
    if jwk.get("kty") != "RSA" or jwk.get("alg") != "RS256":
        return False
    try:
        modulus = int.from_bytes(_base64url_decode(str(jwk["n"])), "big")
        exponent = int.from_bytes(_base64url_decode(str(jwk["e"])), "big")
        k = (modulus.bit_length() + 7) // 8
        if len(signature) != k:
            return False
        encoded = pow(int.from_bytes(signature, "big"), exponent, modulus).to_bytes(k, "big")
    except (KeyError, ValueError, TypeError):
        return False

    digest_info = (
        bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(message).digest()
    )
    expected = b"\x00\x01" + b"\xff" * (k - len(digest_info) - 3) + b"\x00" + digest_info
    return hmac.compare_digest(encoded, expected)


async def verify_production_token(token: str) -> str:
    if settings.auth_mode != "production":
        raise UnauthorizedError
    if (
        not settings.cognito_jwks_url
        or not settings.cognito_issuer
        or not settings.cognito_audience
    ):
        raise UnauthorizedError

    parts = token.split(".")
    if len(parts) != 3:
        raise UnauthorizedError
    header_segment, payload_segment, signature_segment = parts
    try:
        header = json.loads(_base64url_decode(header_segment))
        payload = json.loads(_base64url_decode(payload_segment))
        signature = _base64url_decode(signature_segment)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise UnauthorizedError from None

    if header.get("alg") != "RS256" or header.get("typ") != "JWT":
        raise UnauthorizedError
    kid = header.get("kid")
    if not isinstance(kid, str) or not kid:
        raise UnauthorizedError

    now = int(time.time())
    expires_at = payload.get("exp")
    issued_at = payload.get("iat")
    if not isinstance(expires_at, int) or expires_at <= now:
        raise UnauthorizedError
    if not isinstance(issued_at, int) or issued_at > now + 300:
        raise UnauthorizedError
    if payload.get("iss") != settings.cognito_issuer:
        raise UnauthorizedError
    audience = payload.get("aud") or payload.get("client_id")
    if audience != settings.cognito_audience:
        raise UnauthorizedError
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise UnauthorizedError

    cached_at = _jwks_cache.get("_cached_at", 0)
    keys = _jwks_cache.get("keys")
    if not isinstance(keys, list) or now - int(cached_at) >= settings.jwks_cache_seconds:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(settings.cognito_jwks_url)
                response.raise_for_status()
                document = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            raise UnauthorizedError from None
        keys = document.get("keys") if isinstance(document, dict) else None
        if not isinstance(keys, list):
            raise UnauthorizedError
        _jwks_cache["_cached_at"] = now
        _jwks_cache["keys"] = keys

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    for key in keys:
        if (
            isinstance(key, dict)
            and key.get("kid") == unquote(kid)
            and _rsa_verify(signing_input, signature, key)
        ):
            return subject
    raise UnauthorizedError


async def get_current_subject(
    credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError
    if settings.auth_mode == "production":
        return await verify_production_token(credentials.credentials)
    return verify_dev_token(credentials.credentials)
