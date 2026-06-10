"""
LLM 统一调用封装
支持：讯飞星火（主）+ DeepSeek/OpenAI（备），自动切换
"""
import os
import json
import httpx
from typing import AsyncIterator, Optional


class LLMClient:
    """统一的 LLM 调用客户端"""

    def __init__(
        self,
        primary: str = "spark",
        fallback: str = "deepseek",
    ):
        self.primary = primary
        self.fallback = fallback

    async def chat_stream(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """流式对话，根据 LLM_PRIMARY 选择主模型，失败自动切换备选"""
        primary = os.getenv("LLM_PRIMARY", "spark")

        if primary == "deepseek":
            # 直接用 DeepSeek 作为主模型
            try:
                async for chunk in self._call_deepseek(system, user):
                    yield chunk
            except Exception as e:
                print(f"[LLMClient] DeepSeek failed: {e}")
                yield f"[错误: DeepSeek调用失败: {e}]"
        else:
            # 默认：Spark 主，DeepSeek 备
            try:
                async for chunk in self._call_spark(system, user, model):
                    yield chunk
            except Exception as e:
                print(f"[LLMClient] Spark failed: {e}, switching to fallback...")
                try:
                    async for chunk in self._call_deepseek(system, user):
                        yield chunk
                except Exception as e2:
                    print(f"[LLMClient] Fallback also failed: {e2}")
                    yield f"[错误: AI服务暂时不可用，请稍后重试]"

    async def _call_spark(
        self, system: str, user: str, model: Optional[str] = None
    ) -> AsyncIterator[str]:
        """调用讯飞星火 API（HTTP OpenAI 兼容，流式）"""
        api_password = os.getenv("SPARK_API_PASSWORD", "")
        if not api_password:
            yield "[错误: 未配置 SPARK_API_PASSWORD]"
            return

        api_url = os.getenv(
            "SPARK_API_URL",
            "https://spark-api-open.xf-yun.com/agent/v1/chat/completions",
        )
        model_name = model or os.getenv("SPARK_MODEL", "spark-2.0-flash")

        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream(
                "POST",
                api_url,
                headers={
                    "Authorization": f"Bearer {api_password}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            continue

    async def _call_deepseek(self, system: str, user: str) -> AsyncIterator[str]:
        """调用 DeepSeek API（OpenAI 兼容，流式）"""
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            yield "[错误: 未配置 DeepSeek API Key]"
            return

        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream(
                "POST",
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            continue
