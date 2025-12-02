"""
會話管理的業務邏輯
"""
import time
import asyncio
import redis.asyncio as redis
from datetime import datetime
# === 關鍵修正：確保導入 Optional, Dict, Any, Awaitable ===
from typing import List, Dict, Any, Awaitable, Optional 

# 導入 Redis-OM 的同步連線
from database.redis_client import redis_om_conn 

# 導入 ChatMessage 模型 (假設已修復 ModuleNotFoundError)
from models.chat import ChatMessage
# 導入 ChatSession 模型 (假設已修復 ModuleNotFoundError)
from models.session import ChatSession 
# 假設 save_message 是一個異步函數
from services.message_service import save_message

# 將同步客戶端綁定給 Redis-OM 模型
ChatSession.Meta.database = redis_om_conn
from database.redis_client import redis_om_conn

async def get_all_sessions(redis_client: redis.Redis) -> List[Dict[str, Any]]:
    """
    暫時版本：不用 Redis-OM 查詢，只用原生 Redis 讀出 sessions。
    回傳簡單 dict list 給前端。
    """
    session_ids = await redis_client.smembers("active_sessions")
    print("DEBUG active_sessions:", session_ids)
    results: List[Dict[str, Any]] = []
    for sid in session_ids:
    # 掃描所有 chatsession:*，找出 session_id = sid 的那一筆
        for key in redis_om_conn.scan_iter(":chatsession:*"):
            data = redis_om_conn.hgetall(key)
            print("DEBUG chatsession key/data:", key, data)
            if not data:
                continue
            if data.get("session_id") == sid:
                results.append(
                    {
                        "session_id": data.get("session_id"),
                        "title": data.get("title", "新對話"),
                        "created_at": data.get("created_at"),
                        "message_count": int(data.get("message_count", 0)),
                    }
                )
                break

    # 依 created_at 排序（字串排序先不管時區，重點是前端有資料）
    results.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return results


# def _sort_sessions(sessions: List[ChatSession]) -> List[ChatSession]:
#     """同步地排序 sessions"""
#     sessions.sort(key=lambda s: s.created_at, reverse=True)
#     return sessions

# async def get_all_sessions(redis_client: redis.Redis) -> List[ChatSession]:
#     """獲取所有會話，並返回 ChatSession 對象列表"""
#     # 1. 從 Redis Set 獲取所有會話 ID (返回 str set，因為配置了 decode_responses=True)
#     sessions_keys = await redis_client.smembers("active_sessions")
    
#     # 2. 為每個 session ID 創建一個異步任務，以避免阻塞事件循環
#     tasks: List[Awaitable[Optional[ChatSession]]] = []
    
#     for session_id in sessions_keys:
#         # session_id 已經是 str，直接使用
#         tasks.append(asyncio.to_thread(_get_session_data, session_id))
        
#     # 3. 並發執行所有獲取任務
#     # 過濾掉失敗的 (None) 結果
#     raw_sessions = await asyncio.gather(*tasks)
#     sessions: List[ChatSession] = [s for s in raw_sessions if s is not None]
    
#     # 4. 排序 (將排序操作也放入線程中執行，確保主事件循環不阻塞)
#     sessions = await asyncio.to_thread(_sort_sessions, sessions)
    
#     return sessions

async def create_session(redis_client: redis.Redis, session_id: str):
    """創建新會話"""
    print(f"INFO: Creating new session: {session_id}")

    # 1. 將 session ID 加入活動會話 Set
    await redis_client.sadd("active_sessions", session_id)
    
    session_obj = ChatSession(
    session_id=session_id,
    created_at=datetime.utcnow(), # 不要用 int(time.time())
    )


    #由於 Redis-OM 的 save 是同步的，使用 asyncio.to_thread
    await asyncio.to_thread(session_obj.save)
    print(f"INFO: ChatSession object saved via Redis-OM (PK: {session_obj.pk}).")
    
    # 2. 準備 AI 歡迎訊息
    ai_welcome_message: Dict[str, Any] = {
        "session_id": session_id,
        "sender": "AI", 
        "content": "你好！我是 AI 助手，很高興為您服務。請問有什麼可以協助您的嗎？",
        "ts": int(time.time() * 1000) # 使用毫秒時間戳
    }
    
    # 3. 儲存訊息
    # 關鍵修正: 必須將 redis_client 傳遞給 save_message
    await save_message(redis_client, session_id, ai_welcome_message) 
    
    # 4. 記錄到 Stream
    await redis_client.xadd("chat_stream", fields={
        "session_id": ai_welcome_message["session_id"],
        "sender": ai_welcome_message["sender"],
        "content": ai_welcome_message["content"],
        "ts": str(ai_welcome_message["ts"]),
        "deleted": "false"
    })
    
    print(f"INFO: Session '{session_id}' created with welcome message.")

def _find_and_delete_pks(session_id: str):
    """同步地查找並刪除 ChatMessage，供 asyncio.to_thread 使用"""
    from redis_om import NotFoundError # 在這裡局部導入，避免循環依賴
    try:
        msgs = ChatMessage.find(ChatMessage.session_id == session_id).all()
        pk_list = [m.pk for m in msgs]
        for pk in pk_list:
            ChatMessage.delete(pk)
        return len(pk_list)
    except NotFoundError:
        return 0
    except Exception as e:
        print(f"ERROR during message cleanup for session {session_id}: {e}")
        return 0

async def delete_session(redis_client: redis.Redis, session_id: str) -> bool:
    """刪除會話及其所有訊息"""
    removed = await redis_client.srem("active_sessions", session_id)
    
    if not removed:
        print(f"WARNING: Session '{session_id}' not found.")
        return False
    
    # 將同步的刪除操作放入單獨的線程中運行
    deleted_count = await asyncio.to_thread(_find_and_delete_pks, session_id)
    
    # 清理非 Redis-OM 結構 (異步操作)
    await redis_client.delete(f"chat_history:{session_id}")
    await redis_client.delete(f"deleted_history:{session_id}")
    
    print(f"INFO: Session '{session_id}' deleted with {deleted_count} messages.")
    return True