"""
會話相關的 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, status
from redis.asyncio import Redis
from typing import List

# 假設這些模型和服務已存在
from models.session import ChatSession 
from services.session_service import get_all_sessions, create_session, delete_session
# 統一使用 get_redis_client 作為異步 Redis 客戶端的依賴
from database.redis_client import get_redis_client 

# 註冊路由並設定前綴
router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get(
    "/", # 修正: 使用 "/" 搭配前綴 /sessions 得到 /sessions
    # response_model=List[ChatSession], 
    summary="獲取所有活動會話"
)
async def list_sessions(
    # 統一使用 get_redis_client
    redis_client: Redis = Depends(get_redis_client)
):
    """
    獲取所有活動會話列表，用於側邊欄顯示。
    """
    sessions = await get_all_sessions(redis_client) 
    return sessions

@router.post(
    "/{session_id}", # 修正: 移除重複的 /sessions，路徑為 /sessions/{session_id}
    status_code=status.HTTP_201_CREATED, # 添加狀態碼
    summary="創建新的會話"
)
async def add_session(
    session_id: str,
    # 統一使用 get_redis_client
    redis_client: Redis = Depends(get_redis_client) 
):
    """
    使用指定的 ID 建立新的聊天會話，並發送一個 AI 歡迎訊息。
    """
    await create_session(redis_client, session_id)
    return {"message": f"Session {session_id} created successfully"}

@router.delete(
    "/{session_id}",
    summary="刪除指定會話"
)
async def remove_session(
    session_id: str,
    # 統一使用 get_redis_client
    redis_client: Redis = Depends(get_redis_client)
):
    """
    刪除會話及其所有訊息。
    """
    success = await delete_session(redis_client, session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Session ID '{session_id}' not found."
        )
    return {"message": f"Session {session_id} deleted successfully."}