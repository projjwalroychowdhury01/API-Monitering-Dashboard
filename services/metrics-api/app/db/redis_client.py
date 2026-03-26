import redis

_redis_client = None
def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
    return _redis_client