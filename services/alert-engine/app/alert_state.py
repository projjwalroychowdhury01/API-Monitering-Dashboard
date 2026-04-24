# alert_state.py
# In-memory per-endpoint alert deduplication.
# Prevents the same alert type from firing every poll cycle during sustained issues.
#
# Thread-safety: not required — the engine runs in a single-threaded loop.

import time
from typing import Dict, Tuple

from app.config import ALERT_COOLDOWN

# ---------------------------------------------------------------------------
# State — module-level singleton dict
# ---------------------------------------------------------------------------

# Maps (endpoint_id, alert_type) → UNIX timestamp of last fired alert.
_last_alerted: Dict[Tuple[str, str], float] = {}


def is_suppressed(endpoint_id: str, alert_type: str) -> bool:
    """
    Return True if this (endpoint_id, alert_type) combination fired an alert
    within the last ALERT_COOLDOWN seconds and should be suppressed.
    """
    key = (endpoint_id, alert_type)
    last_ts = _last_alerted.get(key)
    if last_ts is None:
        return False
    return (time.monotonic() - last_ts) < ALERT_COOLDOWN


def record_alert(endpoint_id: str, alert_type: str) -> None:
    """
    Record that an alert of this type fired right now for the given endpoint.
    Call this *after* the alert has been dispatched.
    """
    _last_alerted[(endpoint_id, alert_type)] = time.monotonic()


def reset() -> None:
    """
    Clear all recorded alert state.
    Intended for use in tests only.
    """
    _last_alerted.clear()
