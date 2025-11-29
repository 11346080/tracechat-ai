"""
WebSocket 相關的路由
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.message_service import save_message, get_message_history

from database.redis_client import redis
import json
import time

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket 聊天端點"""
    from services.ai_service import get_ai_response
    await websocket.accept()
    print(f"INFO: WebSocket connected for session: {session_id}")
    
    # 發送歷史訊息
    history = await get_message_history(session_id)
    for msg in history:
        await websocket.send_text(json.dumps(msg))
    
    try:
        while True:
            data_raw = await websocket.receive_text()
            data = json.loads(data_raw)
            
            # 儲存用戶訊息
            await save_message(session_id, data)
            await websocket.send_text(json.dumps(data))
            
            # Stream 記錄
            await redis.xadd("chat_stream", fields={
                "session_id": session_id,
                "sender": data["sender"],
                "content": data["content"],
                "ts": str(data["ts"]),
                "deleted": "false"
            })
            
            # 獲取 AI 回應
            if data.get("sender") == "me":
                ai_response_content = await get_ai_response(data["content"])
                
                ai_msg = {
                    "sender": "AI",
                    "content": ai_response_content,
                    "ts": int(time.time() * 1000)
                }
                
                await save_message(session_id, ai_msg)
                await websocket.send_text(json.dumps(ai_msg))
                
                # Stream 記錄
                await redis.xadd("chat_stream", fields={
                    "session_id": session_id,
                    "sender": "AI",
                    "content": ai_response_content,
                    "ts": str(ai_msg["ts"]),
                    "deleted": "false"
                })
    
    except WebSocketDisconnect:
        print(f"INFO: WebSocket disconnected for session: {session_id}")
    except Exception as e:
        print(f"ERROR: WebSocket error for session {session_id}: {e}")
