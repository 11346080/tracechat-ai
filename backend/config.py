# backend/config.py
import os
from dotenv import load_dotenv
from redis import Redis # 專門用於 Migrator 的同步客戶端

load_dotenv()

class Settings:
    # Redis 配置
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "rediss://default:AYVPAAIncDJhYjFkMGQ2OTkzN2Y0ODM5YmQ4Y2MwZDcxYzAyNzUzMnAyMzQxMjc@darling-mole-34127.upstash.io:6379" 
    )
    
    # 這裡不再預先實例化異步客戶端
    
    # Azure OpenAI 配置
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource-name.openai.azure.com/")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "YOUR_API_KEY_HERE")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")
    AZURE_OPENAI_MODEL: str = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    
    # 業務邏輯配置
    DELETE_RECORD_RETENTION_DAYS: int = 30
    DELETE_RECORD_RETENTION_SECONDS: int = DELETE_RECORD_RETENTION_DAYS * 24 * 60 * 60
    
    # CORS 配置
    CORS_ORIGINS: list = ["*"]

settings = Settings()

# 關鍵修正：在 settings 初始化後，使用同步 Redis 客戶端進行綁定 (供 Redis-OM Migrator 使用)
try:
    # 這裡使用同步的 `redis` 庫
    settings.redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    print("INFO: Synchronous Redis client for Migrator initialized successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize SYNCHRONOUS Redis Client for Migrator: {e}")
    raise