"""
分析/統計相關的 API 路由
"""
from fastapi import APIRouter, HTTPException
from database.redis_client import redis_om_conn
import asyncio
from models.chat import ChatMessage

router = APIRouter(prefix="/aggregation", tags=["Analytics"])

@router.get("/hourly_trend/{session_id}")
async def get_hourly_trend(session_id: str):
    """獲取會話的小時活躍趨勢"""
    
    def query_hourly_trend():
        try:
            # 使用 RediSearch 聚合
            from redis.commands.search.aggregation import AggregateRequest
            from redis.commands.search.reducers import count
            
            # 檢查索引是否存在
            try:
                info = redis_om_conn.ft("chatmessage_idx").info()
                print(f"✅ Index exists: {info.get('index_name')}")
            except Exception as e:
                print(f"❌ Index not found: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail="RediSearch index not found. Please ensure Redis Stack is running and index is created."
                )
            
            # 構建聚合查詢
            query = f"@session_id:{{{session_id}}}"
            
            # 使用 APPLY 計算小時時間槽
            req = (
                AggregateRequest(query)
                .apply(hour="floor(@ts/3600000)*3600000")
                .group_by("@hour", count().alias("count"))
                .sort_by("@hour", asc=True)
            )
            
            print(f"📊 Executing aggregation query for session: {session_id}")
            result = redis_om_conn.ft("chatmessage_idx").aggregate(req)
            
            hourly_trend = []
            for row in result.rows:
                try:
                    # row 格式: ['hour', ts_value, 'count', count_value]
                    ts_ms = int(row[1])
                    cnt = int(row[3])
                    
                    from datetime import datetime
                    dt = datetime.fromtimestamp(ts_ms / 1000)
                    time_slot = dt.strftime("%Y-%m-%d %H:00:00")
                    
                    hourly_trend.append({
                        "time_slot": time_slot,
                        "count": cnt
                    })
                except (ValueError, IndexError) as e:
                    print(f"⚠️ Warning: Failed to parse row {row}: {e}")
                    continue
            
            print(f"✅ Found {len(hourly_trend)} hourly data points")
            return hourly_trend
            
        except Exception as e:
            print(f"❌ Aggregation query failed: {e}")
            print(f"   Session: {session_id}")
            import traceback
            traceback.print_exc()
            
            # 如果聚合失敗，使用備用方案
            return fallback_hourly_trend(session_id)
    
    try:
        hourly_trend = await asyncio.to_thread(query_hourly_trend)
        
        if not hourly_trend:
            print(f"⚠️ No data found for session: {session_id}")
            return {
                "hourly_trend": [],
                "message": "No data available for this session"
            }
        
        return {"hourly_trend": hourly_trend}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to get hourly trend: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get hourly trend: {str(e)}"
        )


def fallback_hourly_trend(session_id: str) -> list:
    """
    備用方案：直接從 ORM 查詢並手動聚合
    當 RediSearch 聚合失敗時使用
    """
    try:
        print(f"🔄 Using fallback method for session: {session_id}")
        
        # 查詢該會話的所有訊息
        messages = ChatMessage.find(ChatMessage.session_id == session_id).all()
        
        if not messages:
            return []
        
        # 手動按小時聚合
        from collections import defaultdict
        from datetime import datetime
        
        hourly_counts = defaultdict(int)
        
        for msg in messages:
            ts_ms = msg.ts
            dt = datetime.fromtimestamp(ts_ms / 1000)
            # 取整到小時
            hour_key = dt.strftime("%Y-%m-%d %H:00:00")
            hourly_counts[hour_key] += 1
        
        # 轉換為列表並排序
        hourly_trend = [
            {"time_slot": time_slot, "count": count}
            for time_slot, count in sorted(hourly_counts.items())
        ]
        
        print(f"✅ Fallback method found {len(hourly_trend)} hourly data points")
        return hourly_trend
        
    except Exception as e:
        print(f"❌ Fallback method also failed: {e}")
        return []
