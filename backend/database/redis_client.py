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
            
            # 使用 ConnectionPool 而非直接 Redis.from_url，可以更好地控制連線行為
            _redis_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                # 增加超時時間，尤其針對 Upstash 的 Serverless 特性
                socket_timeout=60, 
                socket_connect_timeout=5,
                max_connections=10 # 限制連線數量，避免超出 Upstash 免費層限制
            )
            print("INFO: Redis Connection Pool initialized successfully.")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to initialize Redis Connection Pool: {e}")
            raise

async def get_redis_client() -> redis.Redis:
    """
    獲取一個異步 Redis 客戶端實例。
    """
    if _redis_pool is None:
        await init_redis_pool()
        
    # 從連線池中獲取客戶端
    # 這裡的 socket_timeout 設置與 ConnectionPool 保持一致
    return redis.Redis(
        connection_pool=_redis_pool,
        socket_timeout=10, 
        socket_connect_timeout=5
    )

# 為了確保 Redis-OM migrator 可以運行，我們提供一個同步的 Redis 連線，
# 讓 migrator 在應用程式啟動時使用。
# 這裡使用 config.settings 中已經初始化的同步 client
redis_om_migrator_client = settings.redis_client