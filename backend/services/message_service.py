"""
訊息相關的業務邏輯
"""
import json
import time
import asyncio
from typing import List, Dict, Any
import redis.asyncio as redis  # 統一使用非同步 Redis 模組

# 導入 Redis-OM 的同步連線
from database.redis_client import redis_om_conn
from models.chat import ChatMessage  # 假設 ChatMessage 是 RediSearch ORM 模型

# 將同步客戶端綁定給 Redis-OM 模型 (這是 Redis-OM 要求的)
ChatMessage.Meta.database = redis_om_conn


async def save_message(redis_client: redis.Redis, session_id: str, msg_data: Dict[str, Any]):
    """
    儲存訊息到 Redis List 和 ORM。
    """
    print(f"INFO: Saving message to session '{session_id}'...")

    # 1. 儲存到 Redis List (用於快速查詢和歷史)
    await redis_client.rpush(f"chat_history:{session_id}", json.dumps(msg_data))

    # 2. 儲存到 RediSearch ORM (用於全文搜索和持久化)
    try:
        cm = ChatMessage(
            session_id=session_id,
            sender=msg_data["sender"],
            content=msg_data["content"],
            ts=msg_data["ts"],
        )
        await asyncio.to_thread(cm.save)
        print(f"INFO: Message saved via Redis-OM (PK: {cm.pk}).")
    except Exception as e:
        print(f"ERROR: Failed to save message via Redis-OM: {e}")
        # 不拋錯，讓服務繼續運行


async def get_message_history(redis_client: redis.Redis, session_id: str) -> List[Dict[str, Any]]:
    """
    獲取會話的訊息歷史。
    """
    history = await redis_client.lrange(f"chat_history:{session_id}", 0, -1)
    print(f"DEBUG history raw for {session_id}:", history)

    messages: List[Dict[str, Any]] = []

    for msg in history:
        try:
            if isinstance(msg, bytes):
                decoded = msg.decode()
            else:
                decoded = msg

            if decoded != "__deleted__":
                messages.append(json.loads(decoded))
        except Exception as e:
            print(f"WARNING: Failed to decode message in history for {session_id}: {e}")
            continue

    print(f"DEBUG parsed messages for {session_id}:", messages)
    return messages


async def delete_messages_batch(redis_client: redis.Redis, session_id: str, ts_list: List[int]) -> int:
    """
    批量刪除訊息，只使用 List 重建與刪除歷史，不再呼叫 ORM。
    """
    now_ts = int(time.time())
    del_hist_key = f"deleted_history:{session_id}"

    msgs_raw = await redis_client.lrange(f"chat_history:{session_id}", 0, -1)
    to_delete_ts_str = set(map(str, ts_list))

    messages_to_keep: List[str] = []
    deleted_msgs: List[Dict[str, Any]] = []

    for msg_raw in msgs_raw:
        try:
            if isinstance(msg_raw, bytes):
                decoded = msg_raw.decode()
            else:
                decoded = msg_raw

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
                messages_to_keep.append(decoded)
        except Exception as e:
            print(f"⚠️ 處理訊息時出錯: {e}")
            continue

    # 更新 Redis List + 刪除歷史
    async with redis_client.pipeline() as pipe:
        pipe.delete(f"chat_history:{session_id}")
        if messages_to_keep:
            pipe.rpush(f"chat_history:{session_id}", *messages_to_keep)
        if deleted_msgs:
            deleted_json_list = [json.dumps(dm) for dm in deleted_msgs]
            pipe.rpush(del_hist_key, *deleted_json_list)
        await pipe.execute()

    # Stream 記錄
    for ts_val in ts_list:
        await redis_client.xadd(
            "chat_stream",
            fields={
                "session_id": session_id,
                "sender": "",
                "content": "",
                "ts": str(ts_val),
                "deleted": "true",
            },
        )

    print(f"✅ 批量刪除完成: session={session_id}, 共刪除 {len(deleted_msgs)} 條訊息")
    return len(deleted_msgs)


async def restore_message(redis_client: redis.Redis, session_id: str, ts_to_restore: int, deleted_at: int) -> bool:
    """
    復原已刪除的訊息（按時間順序插入）。
    """
    del_hist_key = f"deleted_history:{session_id}"
    deleted_messages_raw = await redis_client.lrange(del_hist_key, 0, -1)

    message_to_restore = None
    remaining_deleted: List[str] = []

    print(f"🔍 正在搜尋要復原的訊息: session={session_id}, ts={ts_to_restore}")

    for msg_raw in deleted_messages_raw:
        try:
            if isinstance(msg_raw, bytes):
                decoded = msg_raw.decode()
            else:
                decoded = msg_raw

            data = json.loads(decoded)

            if int(data.get("ts")) == int(ts_to_restore) and int(data.get("deleted_at")) == int(deleted_at):
                message_to_restore = data
                print("✅ 找到要復原的訊息")
            else:
                remaining_deleted.append(decoded)
        except Exception as e:
            print(f"⚠️ 無法解析訊息: {e}")
            continue

    if not message_to_restore:
        print("❌ 找不到要復原的訊息")
        return False

    # 移除 deleted_at 欄位
    message_to_restore.pop("deleted_at", None)

    # 確保 session_id 存在
    if "session_id" not in message_to_restore:
        message_to_restore["session_id"] = session_id

    try:
        existing_messages_raw = await redis_client.lrange(f"chat_history:{session_id}", 0, -1)
        all_messages: List[Dict[str, Any]] = []

        for msg_raw in existing_messages_raw:
            try:
                if isinstance(msg_raw, bytes):
                    decoded = msg_raw.decode()
                else:
                    decoded = msg_raw

                if decoded != "__deleted__":
                    all_messages.append(json.loads(decoded))
            except Exception as e:
                print(f"⚠️ 解析現有訊息失敗: {e}")
                continue

        all_messages.append(message_to_restore)
        all_messages.sort(key=lambda x: x.get("ts", 0))

        print(f"📝 重新排序訊息: 共 {len(all_messages)} 條")

        async with redis_client.pipeline() as pipe:
            pipe.delete(del_hist_key)
            pipe.delete(f"chat_history:{session_id}")

            if remaining_deleted:
                pipe.rpush(del_hist_key, *remaining_deleted)

            sorted_messages_json = [json.dumps(msg) for msg in all_messages]
            pipe.rpush(f"chat_history:{session_id}", *sorted_messages_json)

            await pipe.execute()

        print("✅ Redis 更新完成（訊息已按時間排序）")

        cm = ChatMessage(
            session_id=message_to_restore["session_id"],
            sender=message_to_restore["sender"],
            content=message_to_restore["content"],
            ts=message_to_restore["ts"],
        )
        await asyncio.to_thread(cm.save)

        await redis_client.xadd(
            "chat_stream",
            fields={
                "session_id": session_id,
                "sender": message_to_restore["sender"],
                "content": message_to_restore["content"],
                "ts": str(message_to_restore["ts"]),
                "deleted": "false",
            },
        )

        print("✅ 訊息復原完成（已按時間順序插入）")
        return True

    except Exception as e:
        print(f"❌ 復原訊息時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


async def get_deleted_history(redis_client: redis.Redis, session_id: str) -> list:
    """
    獲取刪除紀錄並清理過期紀錄。
    """
    from config import settings

    del_hist_key = f"deleted_history:{session_id}"
    deleted_messages_raw = await redis_client.lrange(del_hist_key, 0, -1)

    current_time = int(time.time())
    valid_messages: List[Dict[str, Any]] = []
    expired_indices: List[int] = []

    print(f"🔍 正在檢查會話 {session_id} 的刪除紀錄...")
    print(f"   原始紀錄數: {len(deleted_messages_raw)}")

    for idx, msg_raw in enumerate(deleted_messages_raw):
        try:
            if isinstance(msg_raw, bytes):
                decoded = msg_raw.decode()
            else:
                decoded = msg_raw

            data = json.loads(decoded)
            deleted_at = data.get("deleted_at", 0)

            if current_time - deleted_at > settings.DELETE_RECORD_RETENTION_SECONDS:
                expired_indices.append(idx)
                print(f"   ⚠️ 紀錄 {idx} 已過期")
            else:
                valid_messages.append(data)
        except Exception as e:
            print(f"   ⚠️ 無法解析紀錄 {idx}: {e}")
            continue

    if expired_indices:
        async with redis_client.pipeline() as pipe:
            pipe.delete(del_hist_key)
            if valid_messages:
                valid_json_list = [json.dumps(vm) for vm in valid_messages]
                pipe.rpush(del_hist_key, *valid_json_list)
            await pipe.execute()
        print(f"   🧹 清理了 {len(expired_indices)} 條過期紀錄")

    print(f"✅ 返回 {len(valid_messages)} 條有效刪除紀錄")
    return valid_messages
