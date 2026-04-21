from clickhouse_driver import Client

from app.config import settings


_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DB,
        )
    return _client


def reset_client() -> None:
    global _client
    _client = None
