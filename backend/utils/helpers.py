"""
輔助工具函數
"""
from datetime import datetime

def format_timestamp(ts_ms: int) -> str:
    """將 timestamp (毫秒) 轉換為可讀格式"""
    dt = datetime.fromtimestamp(ts_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def validate_session_id(session_id: str) -> bool:
    """驗證會話 ID 格式"""
    if not session_id or len(session_id) > 100:
        return False
    # 可以加入更多驗證規則
    return True
