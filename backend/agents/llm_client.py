"""
LLM 统一调用封装
支持：讯飞星火（主）+ DeepSeek/OpenAI（备），自动切换 + 超时重试 + 降级文案
"""
import os
import json
import logging
import httpx
from typing import AsyncIterator, Optional

import config

logger = logging.getLogger(__name__)


class LLMClient:
    """统一的 LLM 调用客户端 —— 超时/重试/降级由 config 驱动"""

    def __init__(
        self,
        primary: str = "spark",
        fallback: str = "deepseek",
    ):
        self.primary = primary
        self.fallback = fallback
        self.timeout = config.LLM_TIMEOUT
        self.max_retries = config.LLM_MAX_RETRIES

    async def chat_stream(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """流式对话，根据 LLM_PRIMARY 选择主模型，失败自动切换备选"""
        primary = os.getenv("LLM_PRIMARY", "spark")

        if primary == "deepseek":
            try:
                async for chunk in self._call_deepseek(system, user):
                    yield chunk
            except Exception as e:
                logger.warning(f"[LLMClient] DeepSeek 调用失败: {e}")
                yield f"[提示: DeepSeek 服务暂时不可用，请稍后重试]"
        else:
            # 默认：Spark 主，DeepSeek 备
            spark_failed = False
            for attempt in range(self.max_retries):
                try:
                    async for chunk in self._call_spark(system, user, model):
                        yield chunk
                    return
                except Exception as e:
                    spark_failed = True
                    logger.warning(f"[LLMClient] Spark 第{attempt + 1}次尝试失败: {e}")
                    if attempt < self.max_retries - 1:
                        import asyncio
                        yield f"[提示: 讯飞星火响应超时，正在重试（第{attempt + 1}/{self.max_retries}次）...]\n"
                        await asyncio.sleep(2 ** attempt)

            if spark_failed:
                logger.warning("[LLMClient] Spark 全部重试失败，切换至 DeepSeek 备用模型")
                yield "[提示: 讯飞星火服务暂时不可用，正在切换至备用模型...]\n"
                try:
                    async for chunk in self._call_deepseek(system, user):
                        yield chunk
                except Exception as e2:
                    logger.error(f"[LLMClient] 备用模型也失败: {e2}")
                    yield "[提示: AI 服务暂时不可用，当前将使用模板资源，建议稍后重新生成。]"

    async def _call_spark(
        self, system: str, user: str, model: Optional[str] = None
    ) -> AsyncIterator[str]:
        """调用讯飞星火 API（HTTP OpenAI 兼容，流式）"""
        api_password = os.getenv("SPARK_API_PASSWORD", "")
        if not api_password:
            yield "[提示: 讯飞星火 API 未配置，请检查 .env 文件]"
            return

        api_url = os.getenv(
            "SPARK_API_URL",
            "https://spark-api-open.xf-yun.com/v1/chat/completions",
        )
        model_name = model or os.getenv("SPARK_MODEL", "4.0Ultra")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
            yield "[提示: DeepSeek API Key 未配置，请检查 .env 文件]"
            return

        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
