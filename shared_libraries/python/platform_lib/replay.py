from __future__ import annotations

import json
from typing import Any


SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "proxy-authorization",
}

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "session",
}


def sanitize_headers(headers: dict[str, Any] | None) -> dict[str, Any]:
    if not headers:
        return {}
    sanitized: dict[str, Any] = {}
    for key, value in headers.items():
        sanitized[key] = "[REDACTED]" if key.lower() in SENSITIVE_HEADERS else value
    return sanitized


def sanitize_payload(payload: Any, max_bytes: int = 16_384) -> Any:
    sanitized = _sanitize_value(payload)
    encoded = json.dumps(sanitized, default=str).encode("utf-8")
    if len(encoded) <= max_bytes:
        return sanitized

    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return {
        "truncated": True,
        "preview": truncated,
        "original_size_bytes": len(encoded),
    }


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            cleaned[key] = "[REDACTED]" if key.lower() in SENSITIVE_KEYS else _sanitize_value(item)
        return cleaned
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value
