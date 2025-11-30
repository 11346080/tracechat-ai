"""
全文搜尋相關的服務 (不使用 RediSearch / Redis-OM，直接掃 chat_history)
"""
import json
from typing import List, Dict, Any
import redis.asyncio as redis

from database.redis_client import get_redis_client  # 若路由用 Depends，就從這裡拿 client


async def search_messages(query: str, redis_client: redis.Redis | None = None) -> List[str]:
    """
    在所有會話訊息中執行簡單全文搜尋，回傳包含關鍵字的 session_id 列表。
    不使用 ChatMessage.find / RediSearch，只讀 chat_history:*。
    """
    query = (query or "").strip()
    if not query:
        return []

    # 若路由沒傳 client 進來，就自己建一個（視你的專案結構決定）
    if redis_client is None:
        redis_client = await get_redis_client()  # 如果 get_redis_client 是 async 的

    print(f"🔍 正在執行全文搜索(簡單版): '{query}'")

    matched_sessions: set[str] = set()

    # 掃描所有 chat_history:* key
    async for key in redis_client.scan_iter("chat_history:*"):
        # key 形如 "chat_history:fresh1"
        _, session_id = key.split(":", 1)

        history = await redis_client.lrange(key, 0, -1)
        for msg in history:
            try:
                if isinstance(msg, bytes):
                    decoded = msg.decode()
                else:
                    decoded = msg

                if decoded == "__deleted__":
                    continue

                data = json.loads(decoded)
                content = str(data.get("content", ""))
                if query in content:
                    matched_sessions.add(session_id)
                    break  # 這個會話已經命中，直接檢查下一個 session
            except Exception as e:
                print(f"⚠️ 解析訊息失敗: {e}")
                continue

    result = sorted(matched_sessions)
    print(f"✅ 搜索完成，命中 {len(result)} 個會話: {result}")
    return result


async def get_hot_keywords(n: int = 5, redis_client: redis.Redis | None = None) -> Dict[str, Any]:
    """
    簡單版熱門關鍵詞：從 chat_history:* 統計出現次數最多的 content 片段。
    （無分詞，只是示範；之後如果要真的做熱門詞，可以改成對字詞切割）
    """
    if redis_client is None:
        redis_client = await get_redis_client()

    from collections import Counter

    counter: Counter[str] = Counter()

    async for key in redis_client.scan_iter("chat_history:*"):
        history = await redis_client.lrange(key, 0, -1)
        for msg in history:
            try:
                if isinstance(msg, bytes):
                    decoded = msg.decode()
                else:
                    decoded = msg

                if decoded == "__deleted__":
                    continue

                data = json.loads(decoded)
                content = str(data.get("content", "")).strip()
                if content:
                    counter[content] += 1
            except Exception:
                continue

    most_common = counter.most_common(n)
    keywords = [{"keyword": k, "count": v} for k, v in most_common]
    return {"keywords": keywords}
