from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

TOKEN_ALGORITHM = "HS256"
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260_000
ACCESS_TOKEN_EXPIRE_SECONDS = 7200
REFRESH_TOKEN_EXPIRE_DAYS = 30


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def encrypt_secret(secret: str, key: str) -> str:
    raw = secret.encode("utf-8")
    key_stream = _secret_key_stream(key, len(raw))
    encrypted = bytes(byte ^ key_stream[index] for index, byte in enumerate(raw))
    return f"xor-v1:{_b64url_encode(encrypted)}"


def decrypt_secret(value: str, key: str) -> str:
    if not value.startswith("xor-v1:"):
        return value
    encrypted = _b64url_decode(value.removeprefix("xor-v1:"))
    key_stream = _secret_key_stream(key, len(encrypted))
    raw = bytes(byte ^ key_stream[index] for index, byte in enumerate(encrypted))
    return raw.decode("utf-8")


def _secret_key_stream(key: str, length: int) -> bytes:
    chunks: list[bytes] = []
    counter = 0
    while sum(len(chunk) for chunk in chunks) < length:
        counter_raw = counter.to_bytes(4, "big")
        chunks.append(hashlib.sha256(key.encode("utf-8") + counter_raw).digest())
        counter += 1
    return b"".join(chunks)[:length]


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False

    try:
        algorithm, iterations_raw, salt, expected = password_hash.split("$", 3)
        iterations = int(iterations_raw)
    except ValueError:
        return False

    if algorithm != PASSWORD_ALGORITHM:
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        iterations,
    ).hex()
    return hmac.compare_digest(actual, expected)


def create_token(
    payload: dict[str, Any],
    secret_key: str,
    *,
    expires_delta: timedelta,
) -> str:
    now = utc_now()
    token_payload = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": secrets.token_urlsafe(24),
    }
    header = {"alg": TOKEN_ALGORITHM, "typ": "JWT"}
    header_raw = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_raw = _b64url_encode(json.dumps(token_payload, separators=(",", ":")).encode("utf-8"))
    signed_part = f"{header_raw}.{payload_raw}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        signed_part.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signed_part}.{_b64url_encode(signature)}"


def decode_token(token: str, secret_key: str) -> dict[str, Any] | None:
    try:
        header_raw, payload_raw, signature_raw = token.split(".", 2)
        signed_part = f"{header_raw}.{payload_raw}"
        expected_signature = hmac.new(
            secret_key.encode("utf-8"),
            signed_part.encode("ascii"),
            hashlib.sha256,
        ).digest()
        actual_signature = _b64url_decode(signature_raw)
        if not hmac.compare_digest(actual_signature, expected_signature):
            return None

        header = json.loads(_b64url_decode(header_raw))
        if header.get("alg") != TOKEN_ALGORITHM:
            return None

        payload = json.loads(_b64url_decode(payload_raw))
    except (ValueError, json.JSONDecodeError):
        return None

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(utc_now().timestamp()):
        return None
    return payload
