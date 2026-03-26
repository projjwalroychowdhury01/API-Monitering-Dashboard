from clickhouse_driver import Client

_client = None

def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(host='localhost', port=9000)
    return _client
