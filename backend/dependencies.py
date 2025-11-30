import redis.asyncio as redis
# 假設 get_redis_client() 函數在 database/redis_client.py 中定義，
# 它返回一個異步 Redis 客戶端實例。
from database.redis_client import get_redis_client

async def get_async_redis_client() -> redis.Redis:
    """
    FastAPI 依賴函數：
    獲取異步 Redis 客戶端實例，用於注入到路由函數中。
    """
    # 這裡調用實際建立連線或從連線池獲取連線的函數
    return await get_redis_client()