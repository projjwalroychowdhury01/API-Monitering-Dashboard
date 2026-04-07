# db/clickhouse_client.py
# Singleton ClickHouse client using clickhouse-driver.
# Host/port are read from config (env-var overridable).
# Retries up to MAX_RETRIES times with exponential back-off on failure.

import time

from clickhouse_driver import Client

from app.config import CLICKHOUSE_HOST, CLICKHOUSE_PORT

# ---------------------------------------------------------------------------
# Retry parameters
# ---------------------------------------------------------------------------

MAX_RETRIES: int = 3        # total attempts (1 initial + 2 retries)
RETRY_BASE_DELAY: float = 1.0  # seconds; doubles each attempt: 1 → 2 → 4

# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_client: Client | None = None


def get_client() -> Client:
    """
    Return the singleton ClickHouse client.

    On first call (or after a reset), establishes the connection with up to
    MAX_RETRIES attempts and exponential back-off between failures.

    Raises
    ------
    ConnectionError
        If all retry attempts are exhausted.
    """
    global _client
    if _client is not None:
        return _client

    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            candidate = Client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)
            candidate.execute("SELECT 1")  # connectivity probe
            _client = candidate
            return _client
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(delay)

    # All attempts exhausted — keep _client as None so next poll retries fresh.
    raise ConnectionError(
        f"[ClickHouse] Could not connect to {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT} "
        f"after {MAX_RETRIES} attempts — {last_exc}"
    ) from last_exc


def reset_client() -> None:
    """
    Discard the current singleton so the next get_client() call reconnects.
    Call this when a query raises an error that may indicate a broken connection.
    """
    global _client
    _client = None
