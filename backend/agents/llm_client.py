"""
LLM 统一调用封装
支持：讯飞星火（主）+ DeepSeek/OpenAI（备），自动切换 + 超时重试 + 降级文案

只负责模型调用，不包含任何业务逻辑。
所有敏感配置从环境变量读取，不硬编码。
"""

from __future__ import annotations

import json
import logging
import os
import time
import asyncio
from typing import Any, AsyncIterator, Optional

import httpx

import config

logger = logging.getLogger(__name__)


class UsageStats:
    """单次 LLM 调用的使用统计。"""

    def __init__(self):
        self.model: str = ""
        self.provider: str = ""
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0
        self.duration_ms: int = 0


class LLMClient:
    """统一的 LLM 调用客户端。

    职责只限于模型调用:
    - chat: 非流式对话（收集全部 chunk）
    - chat_json: 非流式对话 + JSON 解析
    - chat_stream: 流式对话
    - 超时/重试/降级
    - 用量统计
    """

    def __init__(
        self,
        primary: str = "",
        fallback: str = "deepseek",
    ):
        self.primary = primary or os.getenv("LLM_PRIMARY", "deepseek")
        self.fallback = fallback
        self.timeout_seconds = max(1, int(config.LLM_TIMEOUT))
        self.max_retries = (
            1 if config.LLM_STRICT_MODE else max(1, int(config.LLM_MAX_RETRIES))
        )
        self.retry_base_delay = 0.5
        self._last_usage: Optional[UsageStats] = None

    @property
    def last_usage(self) -> Optional[UsageStats]:
        return self._last_usage

    # ── 非流式 chat ──────────────────────────────────────────

    async def chat(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """非流式对话——收集所有 chunk 后返回完整文本。"""
        chunks: list[str] = []
        async for chunk in self.chat_stream(system=system, user=user, model=model):
            chunks.append(chunk)
        return "".join(chunks)

    async def chat_json(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Any:
        """非流式对话——返回解析后的 JSON（dict 或 list）。

        Raises:
            ValueError: LLM 返回内容不是合法 JSON
        """
        raw = await self.chat(system=system, user=user, model=model, temperature=temperature)
        return self._parse_json(raw)

    # ── 流式 chat_stream ─────────────────────────────────────

    async def chat_stream(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        response_format: Optional[dict[str, str]] = None,
        response_schema: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """流式对话——根据 LLM_PRIMARY 选择主模型，失败自动切换备选。"""
        start = time.monotonic()
        provider = self.primary

        try:
            if self.primary == "deepseek":
                async for chunk in self._call_deepseek(system, user):
                    yield chunk
                provider = "deepseek"
            else:
                spark_failed = False
                for attempt in range(self.max_retries):
                    try:
                        stream = self._call_spark(
                            system, user, model,
                            response_format=response_format,
                            response_schema=response_schema,
                        )
                        async for chunk in stream:
                            yield chunk
                        self._record_usage(start, model or os.getenv("SPARK_MODEL", "4.0Ultra"), "spark")
                        return
                    except Exception as e:
                        spark_failed = True
                        logger.warning("[LLMClient] Spark attempt %d/%d failed: %s", attempt + 1, self.max_retries, e)
                        if attempt < self.max_retries - 1:
                            yield f"[提示: 讯飞星火响应超时，正在重试（第{attempt + 1}/{self.max_retries}次）...]\n"
                            await asyncio.sleep(self.retry_base_delay * (2 ** attempt))

                if spark_failed:
                    if config.LLM_STRICT_MODE:
                        raise RuntimeError("严格模式：讯飞星火调用失败，拒绝切换备用模型")
                    logger.warning("[LLMClient] Spark 全部重试失败，切换至 DeepSeek")
                    yield "[提示: 讯飞星火服务暂时不可用，正在切换至备用模型...]\n"
                    try:
                        async for chunk in self._call_deepseek(system, user):
                            yield chunk
                        provider = "deepseek"
                    except Exception as e2:
                        logger.error("[LLMClient] 备用模型也失败: %s", e2)
                        yield "[提示: AI 服务暂时不可用，当前将使用模板资源，建议稍后重新生成。]"
        finally:
            elapsed = int((time.monotonic() - start) * 1000)
            usage = self._last_usage or UsageStats()
            usage.provider = usage.provider or provider
            usage.duration_ms = elapsed
            self._last_usage = usage

    # ── Spark ─────────────────────────────────────────────────

    async def _call_spark(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        response_format: Optional[dict[str, str]] = None,
        response_schema: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        api_password = os.getenv("SPARK_API_PASSWORD", "")
        if not api_password:
            raise RuntimeError("讯飞星火 API 未配置，请检查 SPARK_API_PASSWORD")

        api_url = os.getenv("SPARK_API_URL", "https://spark-api-open.xf-yun.com/v1/chat/completions")
        model_name = model or os.getenv("SPARK_MODEL", "4.0Ultra")

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": response_format is None and response_schema is None,
        }

        if response_schema is not None:
            function_name = "return_resources"
            payload.update({
                "temperature": 0.1,
                "top_k": 1,
                "tools": [{
                    "type": "function",
                    "function": {
                        "name": function_name,
                        "description": "按学习资源合同返回生成结果",
                        "parameters": response_schema,
                    },
                }],
                "tool_choice": {"type": "function", "function": {"name": function_name}},
                "tool_calls_switch": True,
            })
        elif response_format is not None:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=self._timeout()) as client:
            if response_format is not None or response_schema is not None:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {api_password}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                if result.get("code", 0) != 0:
                    raise RuntimeError(f"讯飞星火返回错误 {result.get('code')}: {result.get('message', '')}")

                try:
                    message = result["choices"][0]["message"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise RuntimeError("讯飞星火结构化响应缺少 choices.message") from exc

                if response_schema is not None:
                    tool_calls = message.get("tool_calls") or []
                    arguments = None
                    if tool_calls:
                        try:
                            arguments = tool_calls[0]["function"]["arguments"]
                        except (KeyError, IndexError, TypeError):
                            arguments = None
                    if arguments is None:
                        function_call = message.get("function_call") or {}
                        arguments = function_call.get("arguments")

                    if arguments is not None:
                        content = (
                            json.dumps(arguments, ensure_ascii=False)
                            if isinstance(arguments, dict) else arguments
                        )
                    else:
                        content = message.get("content")
                else:
                    content = message.get("content")

                if not isinstance(content, str) or not content.strip():
                    raise RuntimeError("讯飞星火结构化模式返回了空内容")
                yield content
                return

            async with client.stream(
                "POST", api_url,
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
                response.raise_for_status()
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

    # ── DeepSeek ──────────────────────────────────────────────

    async def _call_deepseek(self, system: str, user: str) -> AsyncIterator[str]:
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            yield "[提示: DeepSeek API Key 未配置，请检查 .env 文件]"
            return

        async with httpx.AsyncClient(timeout=self._timeout()) as client:
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
                response.raise_for_status()
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

    # ── 内部方法 ──────────────────────────────────────────────

    def _timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            self.timeout_seconds,
            connect=min(self.timeout_seconds, 5),
            read=self.timeout_seconds,
            write=min(self.timeout_seconds, 10),
            pool=min(self.timeout_seconds, 5),
        )

    def _record_usage(self, start: float, model: str, provider: str) -> None:
        self._last_usage = UsageStats()
        self._last_usage.model = model
        self._last_usage.provider = provider
        self._last_usage.duration_ms = int((time.monotonic() - start) * 1000)

    @staticmethod
    def _parse_json(raw: str) -> Any:
        """从 LLM 响应中提取 JSON。"""
        text = raw.strip()
        # 去 Markdown 代码块
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
        # 找最外层 JSON
        start = text.find("{")
        end = text.rfind("}")
        if start == -1:
            start = text.find("[")
            end = text.rfind("]")
        if start >= 0 and end >= start:
            text = text[start:end + 1]
        return json.loads(text)
