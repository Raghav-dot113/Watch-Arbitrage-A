from __future__ import annotations

import base64
import hashlib
import os

from apps.api.settings import settings
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_ASSOCIATED_DATA = b"chronoarb-provider-secret-v1"


class IntegrationEncryptionUnavailableError(Exception):
    pass


class IntegrationCiphertextError(Exception):
    pass


def digest_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def encrypt_provider_secret(value: str) -> str:
    key_text = settings.integration_encryption_key.get_secret_value()
    if not key_text:
        raise IntegrationEncryptionUnavailableError
    try:
        key = base64.urlsafe_b64decode(key_text.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise IntegrationEncryptionUnavailableError from error
    if len(key) != 32:
        raise IntegrationEncryptionUnavailableError
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, value.encode("utf-8"), _ASSOCIATED_DATA)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_provider_secret(value: str) -> str:
    key_text = settings.integration_encryption_key.get_secret_value()
    if not key_text:
        raise IntegrationEncryptionUnavailableError
    try:
        key = base64.urlsafe_b64decode(key_text.encode("ascii"))
        raw = base64.urlsafe_b64decode(value.encode("ascii"))
        if len(key) != 32 or len(raw) < 13:
            raise IntegrationEncryptionUnavailableError
        return AESGCM(key).decrypt(raw[:12], raw[12:], _ASSOCIATED_DATA).decode("utf-8")
    except InvalidTag as error:
        raise IntegrationCiphertextError from error
    except (ValueError, UnicodeEncodeError) as error:
        raise IntegrationCiphertextError from error
