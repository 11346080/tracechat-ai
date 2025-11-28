"""
會話相關的 API 路由
"""
from fastapi import APIRouter, HTTPException
from services.session_service import get_all_sessions, create_session, delete_session

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("")
async def list_sessions():
    """獲取所有會話列表"""
    sessions = await get_all_sessions()
    return {"sessions": sessions}

@router.post("/{session_id}")
async def add_session(session_id: str):
    """創建新會話"""
    await create_session(session_id)
    return {"msg": "Session created successfully"}

@router.delete("/{session_id}")
async def remove_session(session_id: str):
    """刪除會話"""
    success = await delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"msg": "Session deleted successfully"}
