"""
Chat 相關的資料模型
"""
from redis_om import HashModel, Field
from database.redis_client import redis_om_conn

class ChatMessage(HashModel):
    """聊天訊息 ORM 模型"""
    session_id: str = Field(index=True)
    sender: str
    content: str = Field(index=True, full_text_search=True)
    ts: int

    class Meta:
        database = redis_om_conn
        model_key_prefix = "chat_msg"
        index_name = "chatmessage_idx"
