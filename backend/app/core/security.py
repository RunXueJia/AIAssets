#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:35
# @File     : security.py
# @Desc     : Password hashing and JWT-compatible token helpers.

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings
from app.core.exceptions import AppError


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt_text, digest_text = password_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    salt = _b64url_decode(salt_text)
    expected = _b64url_decode(digest_text)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(digest, expected)


def create_access_token(subject: str, permissions: list[str], expires_delta: int | None = None) -> str:
    expire_seconds = expires_delta or settings.access_token_expire_seconds
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": subject, "permissions": permissions, "exp": int(expires_at.timestamp())}
    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")),
            _b64url_encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")),
        ]
    )
    signature = hmac.new(settings.secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_text, payload_text, signature_text = token.split(".", 2)
    except ValueError as exc:
        raise AppError(40100, "未登录或 Token 过期", 401) from exc

    signing_input = f"{header_text}.{payload_text}"
    expected = hmac.new(settings.secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    try:
        signature = _b64url_decode(signature_text)
    except ValueError as exc:
        raise AppError(40100, "未登录或 Token 过期", 401) from exc
    if not hmac.compare_digest(expected, signature):
        raise AppError(40100, "未登录或 Token 过期", 401)

    payload = json.loads(_b64url_decode(payload_text).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise AppError(40100, "未登录或 Token 过期", 401)
    return payload
