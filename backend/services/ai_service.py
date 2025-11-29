"""
AI 對話相關的業務邏輯（Azure OpenAI）
"""
import asyncio
import os

import httpx
from openai import AzureOpenAI

from config import settings  # 從環境變數讀取設定


# 全域客戶端
_client: AzureOpenAI | None = None


def get_openai_client() -> AzureOpenAI:
    """
    取得 Azure OpenAI 客戶端實例。

    流程：
    1. 若已初始化則直接返回。
    2. 清除 HTTP_PROXY / HTTPS_PROXY，避免代理造成問題。
    3. 建立不帶代理的 httpx 客戶端。
    4. 使用 settings 中的環境變數建立 AzureOpenAI 客戶端。
    """
    global _client
    if _client is not None:
        return _client

    # 清除可能殘留的代理設定
    if "HTTP_PROXY" in os.environ:
        print("DEBUG: Removing HTTP_PROXY from os.environ.")
        del os.environ["HTTP_PROXY"]
    if "HTTPS_PROXY" in os.environ:
        print("DEBUG: Removing HTTPS_PROXY from os.environ.")
        del os.environ["HTTPS_PROXY"]

    # 不使用代理的 httpx 客戶端
    safe_http_client = httpx.Client(proxies=None)

    print("DEBUG: Attempting to initialize AzureOpenAI client.")

    try:
        new_client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            http_client=safe_http_client,
        )
    except Exception as e:
        print(f"❌ FATAL ERROR during AzureOpenAI client initialization: {e}")
        raise

    _client = new_client

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

        if client is None:
            raise RuntimeError("Azure OpenAI client failed to initialize (returned None).")

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
        return "抱歉，AI 暫時無法回應您的問題，請稍後再試。"


    except Exception as e:
        error_msg = f"AI 回應失敗: {e}"
        print(f"ERROR: {error_msg}")
        return "抱歉，AI 暫時無法回應您的問題，請稍後再試。"
