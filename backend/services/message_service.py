"""
訊息相關的業務邏輯
"""
import json
import time
import asyncio
from database.redis_client import redis
from models.chat import ChatMessage

async def save_message(session_id: str, msg_data: dict):
    """儲存訊息到 Redis List 和 ORM"""
    await redis.rpush(f"chat_history:{session_id}", json.dumps(msg_data))
    
    cm = ChatMessage(
        session_id=session_id,
        sender=msg_data["sender"],
        content=msg_data["content"],
        ts=msg_data["ts"]
    )
    
    await asyncio.to_thread(cm.save)
    print(f"DEBUG: Message saved for session {session_id}")

async def get_message_history(session_id: str) -> list:
    """獲取會話的訊息歷史"""
    history = await redis.lrange(f"chat_history:{session_id}", 0, -1)
    messages = []
    
    for msg in history:
        try:
            decoded = msg.decode()
            if decoded != "__deleted__":
                messages.append(json.loads(decoded))
        except Exception as e:
            print(f"WARNING: Failed to decode message: {e}")
            continue
    
    return messages

async def delete_messages_batch(session_id: str, ts_list: list[int]) -> int:
    """批量刪除訊息"""
    now_ts = int(time.time())
    del_hist_key = f"deleted_history:{session_id}"
    msgs_raw = await redis.lrange(f"chat_history:{session_id}", 0, -1)
    to_delete_ts_str = set(map(str, ts_list))
    
    messages_to_keep = []
    deleted_msgs = []
    
    for msg_bytes in msgs_raw:
        try:
            decoded = msg_bytes.decode()
            if decoded == "__deleted__":
                continue
            data = json.loads(decoded)
            ts_val = str(data.get("ts"))
            
            if ts_val in to_delete_ts_str:
                if "session_id" not in data:
                    data["session_id"] = session_id
                
                data["deleted_at"] = now_ts
                deleted_msgs.append(data)
                print(f"🗑️ 標記刪除: ts={ts_val}, content={data.get('content', '')[:30]}...")
            else:
                messages_to_keep.append(msg_bytes)
        except Exception as e:
            print(f"⚠️ 處理訊息時出錯: {e}")
            continue
    
    # Redis List 更新
    async with redis.pipeline() as pipe:
        pipe.delete(f"chat_history:{session_id}")
        if messages_to_keep:
            pipe.rpush(f"chat_history:{session_id}", *messages_to_keep)
        if deleted_msgs:
            deleted_json_list = [json.dumps(dm) for dm in deleted_msgs]
            pipe.rpush(del_hist_key, *deleted_json_list)
        await pipe.execute()
    
    # ORM 刪除
    def delete_orm_messages():
        results = ChatMessage.find(ChatMessage.session_id == session_id).all()
        count = 0
        for r in results:
            if str(r.ts) in to_delete_ts_str:
                ChatMessage.delete(r.pk)
                count += 1
        return count
    
    deleted_orm_count = await asyncio.to_thread(delete_orm_messages)
    print(f"🗑️ ORM 刪除了 {deleted_orm_count} 條訊息")
    
    # Stream 記錄
    for ts_val in ts_list:
        await redis.xadd("chat_stream", fields={
            "session_id": session_id,
            "sender": "",
            "content": "",
            "ts": str(ts_val),
            "deleted": "true"
        })
    
    print(f"✅ 批量刪除完成: session={session_id}, 共刪除 {len(deleted_msgs)} 條訊息")
    return len(deleted_msgs)

async def restore_message(session_id: str, ts_to_restore: int, deleted_at: int) -> bool:
    """復原已刪除的訊息（按時間順序插入）"""
    del_hist_key = f"deleted_history:{session_id}"
    deleted_messages_raw = await redis.lrange(del_hist_key, 0, -1)
    
    message_to_restore = None
    remaining_deleted = []
    
    print(f"🔍 正在搜尋要復原的訊息: session={session_id}, ts={ts_to_restore}")
    
    for msg_bytes in deleted_messages_raw:
        try:
            data = json.loads(msg_bytes.decode())
            
            if int(data.get("ts")) == int(ts_to_restore) and int(data.get("deleted_at")) == int(deleted_at):
                message_to_restore = data
                print(f"✅ 找到要復原的訊息")
            else:
                remaining_deleted.append(msg_bytes)
                
        except Exception as e:
            print(f"⚠️ 無法解析訊息: {e}")
            continue
    
    if not message_to_restore:
        print(f"❌ 找不到要復原的訊息")
        return False
    
    # 移除 deleted_at 欄位
    del message_to_restore["deleted_at"]
    
    # 確保 session_id 存在
    if "session_id" not in message_to_restore:
        message_to_restore["session_id"] = session_id
    
    try:
        # 讀取現有訊息，按時間順序重新排列
        existing_messages_raw = await redis.lrange(f"chat_history:{session_id}", 0, -1)
        all_messages = []
        
        # 解析現有訊息
        for msg_bytes in existing_messages_raw:
            try:
                decoded = msg_bytes.decode()
                if decoded != "__deleted__":
                    all_messages.append(json.loads(decoded))
            except Exception as e:
                print(f"⚠️ 解析現有訊息失敗: {e}")
                continue
        
        # 加入要復原的訊息
        all_messages.append(message_to_restore)
        
        # 按時間戳排序（從舊到新）
        all_messages.sort(key=lambda x: x.get("ts", 0))
        
        print(f"📝 重新排序訊息: 共 {len(all_messages)} 條")
        
        # 更新 Redis（完全重建列表）
        async with redis.pipeline() as pipe:
            # 刪除舊的刪除歷史和聊天歷史
            pipe.delete(del_hist_key)
            pipe.delete(f"chat_history:{session_id}")
            
            # 重建刪除歷史（移除已復原的訊息）
            if remaining_deleted:
                pipe.rpush(del_hist_key, *remaining_deleted)
            
            # 重建聊天歷史（按時間順序）
            sorted_messages_json = [json.dumps(msg) for msg in all_messages]
            pipe.rpush(f"chat_history:{session_id}", *sorted_messages_json)
            
            await pipe.execute()
        
        print(f"✅ Redis 更新完成（訊息已按時間排序）")
        
        # 復原到 ORM
        cm = ChatMessage(
            session_id=message_to_restore["session_id"],
            sender=message_to_restore["sender"],
            content=message_to_restore["content"],
            ts=message_to_restore["ts"]
        )
        await asyncio.to_thread(cm.save)
        
        # Stream 記錄
        await redis.xadd("chat_stream", fields={
            "session_id": session_id,
            "sender": message_to_restore["sender"],
            "content": message_to_restore["content"],
            "ts": str(message_to_restore["ts"]),
            "deleted": "false"
        })
        
        print(f"✅ 訊息復原完成（已按時間順序插入）")
        return True
        
    except Exception as e:
        print(f"❌ 復原訊息時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

async def get_deleted_history(session_id: str) -> list:
    """獲取刪除紀錄"""
    from config import settings
    
    del_hist_key = f"deleted_history:{session_id}"
    deleted_messages_raw = await redis.lrange(del_hist_key, 0, -1)
    
    current_time = int(time.time())
    valid_messages = []
    expired_indices = []
    
    print(f"🔍 正在檢查會話 {session_id} 的刪除紀錄...")
    print(f"   原始紀錄數: {len(deleted_messages_raw)}")
    
    for idx, msg_bytes in enumerate(deleted_messages_raw):
        try:
            data = json.loads(msg_bytes.decode())
            deleted_at = data.get("deleted_at", 0)
            
            # 檢查是否過期（預設 30 天）
            if current_time - deleted_at > settings.DELETE_RECORD_RETENTION_SECONDS:
                expired_indices.append(idx)
                print(f"   ⚠️ 紀錄 {idx} 已過期")
            else:
                valid_messages.append(data)
        except Exception as e:
            print(f"   ⚠️ 無法解析紀錄 {idx}: {e}")
            continue
    
    # 清理過期紀錄
    if expired_indices:
        async with redis.pipeline() as pipe:
            pipe.delete(del_hist_key)
            if valid_messages:
                valid_json_list = [json.dumps(vm) for vm in valid_messages]
                pipe.rpush(del_hist_key, *valid_json_list)
            await pipe.execute()
        print(f"   🧹 清理了 {len(expired_indices)} 條過期紀錄")
    
    print(f"✅ 返回 {len(valid_messages)} 條有效刪除紀錄")
    return valid_messages

