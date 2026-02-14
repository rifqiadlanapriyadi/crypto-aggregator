"""Module containing everything required for the Redis cache."""

import redis

from api import config

REDIS_URL = f"redis://:{config.settings.redis_password}@redis:6379/0"

redis_client = redis.Redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)


def get_redis_client():
    """Get the Redis client."""
    return redis_client
