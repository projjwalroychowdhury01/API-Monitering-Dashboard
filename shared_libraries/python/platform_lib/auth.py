from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}".encode("ascii"))


def create_access_token(payload: dict[str, Any], secret_key: str, expires_in_seconds: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    claims = payload.copy()
    now = int(time.time())
    claims.setdefault("iat", now)
    claims.setdefault("exp", now + expires_in_seconds)

    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise ValueError("Malformed bearer token.") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_signature = _b64url_decode(signature_segment)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise ValueError("Token signature is invalid.")

    claims = json.loads(_b64url_decode(payload_segment))
    if int(claims.get("exp", 0)) < int(time.time()):
        raise ValueError("Token has expired.")
    return claims


def generate_api_key(prefix: str = "rtio") -> tuple[str, str]:
    key_id = secrets.token_hex(8)
    secret = secrets.token_urlsafe(24)
    return key_id, f"{prefix}_{key_id}_{secret}"


def hash_api_key(raw_api_key: str) -> str:
    return hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
