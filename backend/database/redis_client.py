"""
Redis 連線管理
"""
from redis_om import get_redis_connection
import redis.asyncio as aioredis
from config import settings

# ORM 專用 redis-om 連線
redis_om_conn = get_redis_connection(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT
)

# 異步 Redis 連線
redis = aioredis.from_url(settings.REDIS_URL)

async def close_redis():
    """關閉 Redis 連線"""
    await redis.close()
    print("INFO: Redis connection closed.")
