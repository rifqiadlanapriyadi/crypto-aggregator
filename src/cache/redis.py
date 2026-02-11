"""Module containing everything required for the Redis cache."""

import redis

from api import config

REDIS_URL = config.settings.redis_url

redis_client = redis.Redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)


def get_redis_client():
    """Get the Redis client."""
    return redis_client
