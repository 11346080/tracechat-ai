# backend/database/redis_client.py

import redis.asyncio as redis
from config import settings
from redis.asyncio.connection import ConnectionPool
from typing import Optional

# 儲存連線池的全局變數
_redis_pool: Optional[ConnectionPool] = None

async def init_redis_pool():
    """
    初始化 Redis 連線池。
    """
    global _redis_pool
    if _redis_pool is None:
        try:
            print("INFO: Initializing Redis Connection Pool...")
            
            _redis_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                # 增加超時時間，尤其針對 Upstash 的 Serverless 特性
                socket_timeout=60, 
                socket_connect_timeout=5,
                max_connections=10 # 限制連線數量
            )
            print("INFO: Redis Connection Pool initialized successfully.")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to initialize Redis Connection Pool: {e}")
            raise

async def get_redis_client() -> redis.Redis:
    """
    獲取一個異步 Redis 客戶端實例。
    """
    # 🌟 關鍵修正：解決 NameError，確保在讀取/引用全局變數時作用域正確
    global _redis_pool 
    
    if _redis_pool is None:
        await init_redis_pool()
        
    # 從連線池中獲取客戶端
    # 這裡的 socket_timeout 設置與 ConnectionPool 保持一致
    return redis.Redis(
        connection_pool=_redis_pool,
        socket_timeout=60, 
        socket_connect_timeout=5
    )

# 由於 Redis-OM migrator 和 Models 需要同步連線
# 我們使用 config.settings 中已經初始化的同步 client
redis_om_conn = settings.redis_client

# 移除對頂層 `redis` 客戶端的錯誤依賴
__all__ = ["get_redis_client", "redis_om_conn"]