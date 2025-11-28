"""
會話管理的業務邏輯
"""
import time
import asyncio
from database.redis_client import redis
from models.chat import ChatMessage
from services.message_service import save_message

async def get_all_sessions() -> list[str]:
    """獲取所有會話"""
    sessions = await redis.smembers("active_sessions")
    return sorted([s.decode() for s in sessions])

async def create_session(session_id: str):
    """創建新會話"""
    await redis.sadd("active_sessions", session_id)
    
    # 發送歡迎訊息
    ai_welcome_message = {
        "session_id": session_id,
        "sender": "AI",
        "content": "你好！我是 AI 助手，很高興為您服務。請問有什麼可以協助您的嗎？",
        "ts": int(time.time() * 1000)
    }
    
    await save_message(session_id, ai_welcome_message)
    
    await redis.xadd("chat_stream", fields={
        "session_id": session_id,
        "sender": ai_welcome_message["sender"],
        "content": ai_welcome_message["content"],
        "ts": str(ai_welcome_message["ts"]),
        "deleted": "false"
    })
    
    print(f"INFO: Session '{session_id}' created with welcome message.")

async def delete_session(session_id: str) -> bool:
    """刪除會話及其所有訊息"""
    removed = await redis.srem("active_sessions", session_id)
    
    if not removed:
        print(f"WARNING: Session '{session_id}' not found.")
        return False
    
    # 查詢並刪除所有訊息
    def find_and_delete_pks():
        msgs = ChatMessage.find(ChatMessage.session_id == session_id).all()
        pk_list = [m.pk for m in msgs]
        for pk in pk_list:
            ChatMessage.delete(pk)
        return len(pk_list)
    
    deleted_count = await asyncio.to_thread(find_and_delete_pks)
    
    # 刪除 Redis 紀錄
    await redis.delete(f"chat_history:{session_id}")
    await redis.delete(f"deleted_history:{session_id}")
    
    print(f"INFO: Session '{session_id}' deleted with {deleted_count} messages.")
    return True
