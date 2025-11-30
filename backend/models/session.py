from redis_om import HashModel, Field
from datetime import datetime
from typing import Optional

class ChatSession(HashModel):
    session_id: str = Field(index=True) # 新增這行，並設定 index=True 方便 find 查詢
    title: str = Field(index=True, default="新對話")
    created_at: datetime = Field(index=True, default=datetime.utcnow())
    user_id: Optional[str] = Field(index=True, default=None)
    message_count: int = Field(default=0)
    class Meta:
        model_key_prefix = "chatsession"
