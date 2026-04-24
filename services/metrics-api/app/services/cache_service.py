import json
from app.db.redis_client import get_redis

def get(key: str):
    client = get_redis()
    val = client.get(key)
    if val is not None:
        return json.loads(val)
    return None

def set(key: str, value, ttl: int = 60):
    client = get_redis()
    client.set(key, json.dumps(value), ex=ttl)
