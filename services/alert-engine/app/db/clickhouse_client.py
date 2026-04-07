# db/clickhouse_client.py
# Singleton ClickHouse client using clickhouse-driver.
# Connects to localhost:9000 with no authentication.

from clickhouse_driver import Client

_client = None  # module-level singleton


def get_client() -> Client:
    """
    Return the singleton ClickHouse client.
    Creates the client on first call; reuses it on subsequent calls.
    Raises ConnectionError if the connection cannot be established.
    """
    global _client
    if _client is None:
        try:
            _client = Client(host="localhost", port=9000)
            # Verify connectivity immediately so failures surface early.
            _client.execute("SELECT 1")
        except Exception as exc:
            _client = None  # reset so next call retries
            raise ConnectionError(
                f"[ClickHouse] Failed to connect to localhost:9000 — {exc}"
            ) from exc
    return _client
