import time
from typing import Dict, Tuple

from app.config import settings


_last_alerted: Dict[Tuple[str, str], float] = {}


def is_suppressed(source_key: str, alert_type: str) -> bool:
    key = (source_key, alert_type)
    last_ts = _last_alerted.get(key)
    if last_ts is None:
        return False
    return (time.monotonic() - last_ts) < settings.ALERT_COOLDOWN


def record_alert(source_key: str, alert_type: str) -> None:
    _last_alerted[(source_key, alert_type)] = time.monotonic()


def reset() -> None:
    _last_alerted.clear()
