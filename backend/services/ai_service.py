"""
AI 對話相關的業務邏輯（Azure OpenAI）
"""
import asyncio
from openai import AzureOpenAI
from config import settings

# 全域客戶端（延遲初始化，避免啟動時就爆錯）
_client: AzureOpenAI | None = None


def get_openai_client() -> AzureOpenAI:
    """
    取得 Azure OpenAI 客戶端實例。
    不傳任何 proxies 或額外奇怪參數，只用官方支援的欄位。
    """
    global _client
    if _client is not None:
        return _client

    # 這裡完全依照官方新 SDK 寫法
    _client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )
    print("✅ Azure OpenAI client initialized.")
    print(f"   Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    print(f"   Model: {settings.AZURE_OPENAI_MODEL}")
    return _client


async def get_ai_response(user_message: str) -> str:
    """
    呼叫 Azure OpenAI，取得一段回覆文字。
    """
    try:
        client = get_openai_client()

        # 使用 asyncio.to_thread 包一層，避免阻塞事件 loop
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model=settings.AZURE_OPENAI_MODEL,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.7,
            max_tokens=800,
        )

        content = completion.choices[0].message.content
        print(f"INFO: AI response generated, length={len(content)}")
        return content

    except Exception as e:
        error_msg = f"AI 回應失敗: {e}"
        print(f"ERROR: {error_msg}")
        # 回傳一個友善的錯誤訊息給前端
        return f"抱歉，AI 暫時無法回應您的問題。\n\n錯誤詳情：{e}"
