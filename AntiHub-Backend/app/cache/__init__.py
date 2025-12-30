"""
缓存模块
提供 Redis 客户端和缓存相关功能
"""
from app.cache.redis_client import (
    RedisClient,
    get_redis_client,
    init_redis,
    close_redis,
)

__all__ = [
    "RedisClient",
    "get_redis_client",
    "init_redis",
    "close_redis",
]