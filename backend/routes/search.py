"""
搜尋相關的 API 路由
"""
from fastapi import APIRouter
from services.search_service import search_messages, get_hot_keywords

router = APIRouter(tags=["Search"])

@router.get("/search_messages")
async def search_messages_endpoint(query: str):
    """全文搜尋訊息"""
    session_ids = await search_messages(query)
    return {"session_ids": session_ids}

@router.get("/hot_keywords")
async def get_hot_keywords_endpoint(n: int = 5):
    """獲取熱門關鍵詞"""
    keywords = await get_hot_keywords(n)
    return keywords
