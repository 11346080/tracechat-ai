"""
配置檔案 - 集中管理所有配置參數
"""
import os
from dotenv import load_dotenv
from redis import Redis

load_dotenv()

class Settings:
    # Redis 配置
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6380" 
    )
    redis_client = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        # 設置套接字讀/寫超時為 60 秒
        socket_timeout=60, 
        socket_connect_timeout=5 
    )

    
    
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
