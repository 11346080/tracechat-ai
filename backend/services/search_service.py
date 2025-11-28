"""
搜尋相關的業務邏輯
"""
import asyncio
from models.chat import ChatMessage

async def search_messages(query: str) -> list[str]:
    """全文搜尋訊息，返回相關會話 ID"""
    def do_search():
        results = ChatMessage.find(ChatMessage.content % f"*{query}*").all()
        session_ids = list(set(r.session_id for r in results))
        return session_ids
    
    session_ids = await asyncio.to_thread(do_search)
    print(f"INFO: Search query '{query}' found {len(session_ids)} sessions.")
    return session_ids

async def get_hot_keywords(n: int = 5) -> list[dict]:
    """獲取熱門關鍵詞（簡化版本 - 可擴展使用 Redis aggregation）"""
    # 這裡可以實作更複雜的聚合邏輯
    # 暫時返回空列表或示範資料
    return [
        {"word": "Python", "count": 42},
        {"word": "Redis", "count": 38},
        {"word": "FastAPI", "count": 31},
        {"word": "AI", "count": 27},
        {"word": "對話", "count": 25}
    ][:n]
