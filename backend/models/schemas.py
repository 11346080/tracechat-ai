"""
API 請求/回應的 Pydantic 模型
"""
from pydantic import BaseModel,  Field

class BatchDeleteRequest(BaseModel):
    """批量刪除請求模型"""
    session_id: str
    ts_list: list[int]

class RestoreMessageRequest(BaseModel):
    """訊息復原請求模型"""
    session_id: str = Field(..., description="會話 ID")
    ts_to_restore: int = Field(..., description="要復原的訊息時間戳（毫秒）")
    deleted_at: int = Field(..., description="刪除時間戳（秒）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "測試",
                "ts_to_restore": 1764060332607,
                "deleted_at": 1764064879
            }
        }

class MessageData(BaseModel):
    """訊息資料模型"""
    session_id: str
    sender: str
    content: str
    ts: int
