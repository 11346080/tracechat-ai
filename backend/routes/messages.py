# backend/routes/messages.py

from fastapi import APIRouter, HTTPException, Depends
from models.schemas import BatchDeleteRequest, RestoreMessageRequest
from services.message_service import (
    save_message,
    delete_messages_batch,
    restore_message,
    get_deleted_history,
    get_message_history 
)
# 導入 get_redis_client 和異步 Redis 類型
from database.redis_client import get_redis_client
from redis.asyncio import Redis

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("")
async def add_message(
    data: dict,
    # 🌟 修正：使用 Depends 獲取異步 Redis 客戶端
    redis_client: Redis = Depends(get_redis_client) 
):
    """新增訊息"""
    # 關鍵修正：save_message 需要 redis_client 參數
    await save_message(redis_client, data["session_id"], data) 
    
    # 關鍵修正：使用 DI 獲取的 redis_client
    await redis_client.xadd("chat_stream", fields={
        "session_id": data["session_id"],
        "sender": data["sender"],
        "content": data["content"],
        "ts": str(data["ts"]),
        "deleted": "false"
    })
    
    return {"msg": "Message saved successfully"}

@router.post("/batch_delete")
async def batch_delete(
    req: BatchDeleteRequest,
    redis_client: Redis = Depends(get_redis_client)
):
    """批量刪除訊息"""
    # 關鍵修正：傳遞 redis_client 參數
    deleted_count = await delete_messages_batch(redis_client, req.session_id, req.ts_list)
    return {"msg": f"Deleted {deleted_count} messages"}

@router.post("/restore")
async def restore_message_endpoint(
    req: RestoreMessageRequest,
    redis_client: Redis = Depends(get_redis_client)
):
    """復原已刪除的訊息"""
    # 關鍵修正：傳遞 redis_client 參數
    success = await restore_message(redis_client, req.session_id, req.ts_to_restore, req.deleted_at)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or already restored")
    return {"msg": "Message restored successfully"}

@router.get("/deleted_history/{session_id}")
async def get_deleted_history_endpoint(
    session_id: str,
    redis_client: Redis = Depends(get_redis_client)
):
    """獲取刪除歷史紀錄"""
    try:
        # 關鍵修正：傳遞 redis_client 參數
        deleted_messages = await get_deleted_history(redis_client, session_id)
        print(f"📤 返回 {len(deleted_messages)} 條刪除紀錄給會話 {session_id}")
        return {"deleted_messages": deleted_messages}
    except Exception as e:
        print(f"❌ 獲取刪除歷史失敗: {e}")
        return {"deleted_messages": []}
    
@router.get("/{session_id}")
async def get_chat_history_endpoint(
    session_id: str,
    redis_client: Redis = Depends(get_redis_client)
):
    """
    獲取特定會話的聊天歷史紀錄。
    """
    try:
        # 呼叫 message_service.py 中已有的 get_message_history 函數
        messages = await get_message_history(redis_client, session_id)
        
        # 🌟 確保回傳格式為 {"messages": [...] }，這與前端預期一致
        print(f"📤 返回 {len(messages)} 條聊天歷史紀錄給會話 {session_id}")
        return {"messages": messages}
        
    except Exception as e:
        print(f"❌ 獲取聊天歷史失敗: {e}")
        # 發生錯誤時，返回空列表，避免前端崩潰
        return {"messages": []}