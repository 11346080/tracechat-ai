"""
全跡AI對話室 - 主應用程式
"""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from redis_om import Migrator
import asyncio

# 先導入 config 和 database
from config import settings
from database.redis_client import close_redis

# Lifespan 管理
async def startup_logic():
    """啟動邏輯 - 初始化 RediSearch 索引"""
    print("=" * 60)
    print("🚀 全跡AI對話室 - 啟動中...")
    print("=" * 60)
    print("INFO: Attempting to ensure RediSearch index exists...")
    
    try:
        await asyncio.to_thread(Migrator().run)
        print("✅ RediSearch index confirmed or created successfully.")
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to run Redis-OM Migrator: {e}")
        print("   Please check if Redis Stack is running and accessible.")
    
    print("=" * 60)
    print("✅ Application startup complete.")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws/chat/{session_id}")
    print("📄 API Docs: http://localhost:8000/docs")
    print("=" * 60)

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """應用生命週期管理"""
    # 啟動
    await startup_logic()
    yield
    # 關閉
    await close_redis()
    print("=" * 60)
    print("🛑 Application shutdown complete.")
    print("=" * 60)

# 創建 FastAPI 應用
app = FastAPI(
    title="全跡AI對話室 API",
    description="基於 Redis Stack + FastAPI + Azure OpenAI 的智能對話系統",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 延遲導入 routes（避免循環導入）
from routes import sessions, messages, search, analytics, websocket

# 註冊路由
app.include_router(sessions.router)
app.include_router(messages.router)
app.include_router(search.router)
app.include_router(analytics.router)
app.include_router(websocket.router)

# Root 端點
@app.get("/", tags=["Root"])
async def root():
    """API 根路徑"""
    return {
        "message": "全跡AI對話室 API",
        "version": "1.0.0",
        "features": [
            "Multi-session chat management",
            "AI-powered conversations",
            "Full-text search",
            "Message history tracking",
            "Analytics & trends"
        ],
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "全跡AI對話室"}
