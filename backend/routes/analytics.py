"""
分析/統計相關的 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends
from redis.asyncio import Redis
from typing import Dict, List
from datetime import datetime, timezone, timedelta

from database.redis_client import get_redis_client

router = APIRouter(prefix="/aggregation", tags=["Analytics"])
TZ = timezone(timedelta(hours=8))  # 台灣時間


@router.get("/hourly_trend/{session_id}")
async def get_hourly_trend(
    session_id: str,
    redis_client: Redis = Depends(get_redis_client),
):
    """
    獲取會話的小時活躍趨勢（不使用 RediSearch / Redis-OM，只讀 chat_stream）。
    只統計未標記刪除的使用者訊息（sender=me, deleted != "true"），
    且同一個 ts 只算一次。
    """
    try:
        entries = await redis_client.xrange("chat_stream", "-", "+")
        print("DEBUG chat_stream entries for", session_id, ":", entries)

        hourly_counts: Dict[str, int] = {}
        seen_ts: set[int] = set()  # 避免同一則訊息被算多次

        for entry_id, fields in entries:
            if fields.get("session_id") != session_id:
                continue

            if fields.get("deleted") == "true":
                continue

            sender = fields.get("sender", "")
            if sender.lower() != "me":
                continue

            content = fields.get("content", "")
            if not content.strip():
                continue  # 空內容不算

            ts_str = fields.get("ts")
            if not ts_str:
                continue

            try:
                ts_ms = int(ts_str)
            except ValueError:
                continue

            # 同一個 ts 只算一次（避免刪除/復原後多次 xadd）
            if ts_ms in seen_ts:
                continue
            seen_ts.add(ts_ms)

            try:
                dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=TZ)
                time_slot = dt.strftime("%Y-%m-%d %H:00")
                hourly_counts[time_slot] = hourly_counts.get(time_slot, 0) + 1
            except Exception:
                continue

        hourly_trend: List[Dict[str, int]] = [
            {"time_slot": k, "count": v}
            for k, v in sorted(hourly_counts.items())
        ]

        if not hourly_trend:
            return {
                "hourly_trend": [],
                "message": "No data available for this session",
            }

        return {"hourly_trend": hourly_trend}

    except Exception as e:
        print(f"❌ Failed to get hourly trend for {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get hourly trend: {str(e)}",
        )
