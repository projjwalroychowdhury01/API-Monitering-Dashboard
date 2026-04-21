import json

from app.db.redis_client import get_redis


def get(key: str):
    client = get_redis()
    value = client.get(key)
    if value is None:
        return None
    return json.loads(value)


def set(key: str, value, ttl: int = 30):
    client = get_redis()
    client.set(key, json.dumps(value, default=str), ex=ttl)
