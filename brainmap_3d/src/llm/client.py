import os
from typing import AsyncIterator, Optional, List, Dict, Any
import httpx
from openai import AsyncOpenAI

from src.core.config import settings


class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY or os.environ.get("DASHSCOPE_API_KEY", "dummy-key"),
            base_url=settings.DASHSCOPE_BASE_URL,
            http_client=httpx.AsyncClient(timeout=120.0),
        )
        self.default_model = settings.LLM_MODEL
        self.default_max_tokens = settings.LLM_MAX_TOKENS
        self.default_temperature = settings.LLM_TEMPERATURE

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        """非流式聊天"""
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens or self.default_max_tokens,
            stream=False,
        )
        return response.choices[0].message.content or ""

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """流式聊天"""
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens or self.default_max_tokens,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed_text(self, text: str, model: Optional[str] = None) -> List[float]:
        """获取文本嵌入向量（用于语义搜索）"""
        response = await self.client.embeddings.create(
            model=model or "text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
