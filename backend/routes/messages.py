"""
訊息相關的 API 路由
"""
from fastapi import APIRouter, HTTPException
from models.schemas import BatchDeleteRequest, RestoreMessageRequest
from services.message_service import (
    save_message,
    delete_messages_batch,
    restore_message,
    get_deleted_history
)
from database.redis_client import redis

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("")
async def add_message(data: dict):
    """新增訊息"""
    await save_message(data["session_id"], data)
    
    await redis.xadd("chat_stream", fields={
        "session_id": data["session_id"],
        "sender": data["sender"],
        "content": data["content"],
        "ts": str(data["ts"]),
        "deleted": "false"
    })
    
    return {"msg": "Message saved successfully"}

@router.post("/batch_delete")
async def batch_delete(req: BatchDeleteRequest):
    """批量刪除訊息"""
    deleted_count = await delete_messages_batch(req.session_id, req.ts_list)
    return {"msg": f"Deleted {deleted_count} messages"}

@router.post("/restore")
async def restore_message_endpoint(req: RestoreMessageRequest):
    """復原已刪除的訊息"""
    success = await restore_message(req.session_id, req.ts_to_restore, req.deleted_at)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or already restored")
    return {"msg": "Message restored successfully"}

@router.get("/deleted_history/{session_id}")
async def get_deleted_history_endpoint(session_id: str):
    """獲取刪除歷史紀錄"""
    try:
        deleted_messages = await get_deleted_history(session_id)
        print(f"📤 返回 {len(deleted_messages)} 條刪除紀錄給會話 {session_id}")
        return {"deleted_messages": deleted_messages}
    except Exception as e:
        print(f"❌ 獲取刪除歷史失敗: {e}")
        return {"deleted_messages": []}

