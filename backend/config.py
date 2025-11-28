"""
配置檔案 - 集中管理所有配置參數
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6380"))
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}"
    
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
