# routes/search.py
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from database.redis_client import get_redis_client
from services.search_service import search_messages

router = APIRouter(prefix="/search_messages", tags=["Search"])


@router.get("")
async def search_messages_endpoint(
    query: str,
    redis_client: Redis = Depends(get_redis_client),
):
    session_ids = await search_messages(query, redis_client)
    return {"session_ids": session_ids}
