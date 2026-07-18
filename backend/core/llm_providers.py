"""
统一 LLM Provider 抽象层。

所有 Agent 通过 LLMClient 调用 Provider，不直接依赖具体 SDK。
切换模型只需修改环境变量，无需改动 Agent 代码。
"""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

import httpx

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Provider 基类
# ═══════════════════════════════════════════════════════════════

class BaseProvider(ABC):
    """所有 LLM Provider 的抽象基类。"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 标识：deepseek | xfyun | openai"""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """当前使用的模型名称"""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Provider 是否可用（已配置密钥且 enabled）"""
        ...

    @abstractmethod
    async def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> str:
        """非流式对话"""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        system: str,
        user: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """流式对话"""
        ...

    @abstractmethod
    async def chat_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.1,
    ) -> Any:
        """非流式对话 → JSON 解析"""
        ...


# ═══════════════════════════════════════════════════════════════
# DeepSeek Provider
# ═══════════════════════════════════════════════════════════════

class DeepSeekProvider(BaseProvider):
    """DeepSeek API Provider。

    环境变量：
        DEEPSEEK_API_KEY     — API 密钥
        DEEPSEEK_API_URL     — API 地址（默认 https://api.deepseek.com）
        DEEPSEEK_MODEL       — 模型名称（默认 deepseek-chat）
        DEEPSEEK_ENABLED     — 是否启用（默认 true）
    """

    def __init__(self, timeout_seconds: int = 60):
        self._api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self._api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")
        self._model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self._enabled = os.getenv("DEEPSEEK_ENABLED", "true").lower() not in {
            "0", "false", "no", "off",
        }
        self._timeout = httpx.Timeout(
            timeout_seconds,
            connect=min(timeout_seconds, 10),
            read=timeout_seconds,
            write=min(timeout_seconds, 10),
            pool=min(timeout_seconds, 5),
        )

    @property
    def provider_name(self) -> str:
        return "deepseek"

    @property
    def model_name(self) -> str:
        return self._model

    def is_available(self) -> bool:
        return self._enabled and bool(self._api_key.strip())

    async def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        chunks: list[str] = []
        async for chunk in self.chat_stream(system=system, user=user):
            chunks.append(chunk)
        return "".join(chunks)

    async def chat_stream(self, system: str, user: str, **kwargs: Any) -> AsyncIterator[str]:
        if not self.is_available():
            yield "[提示: DeepSeek API 未配置，请检查 .env 文件]"
            return

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
        }

        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST",
                f"{self._api_url.rstrip('/')}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
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
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    async def chat_json(self, system: str, user: str, temperature: float = 0.1) -> Any:
        if not self.is_available():
            raise RuntimeError("DeepSeek API 未配置")

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._api_url.rstrip('/')}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            # Extract JSON from potential markdown wrapping
            text = content.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
                if text.lower().startswith("json"):
                    text = text[4:].strip()
            start = text.find("{")
            end = text.rfind("}")
            if start == -1:
                start = text.find("[")
                end = text.rfind("]")
            if start >= 0 and end >= start:
                text = text[start:end + 1]
            return json.loads(text)


# ═══════════════════════════════════════════════════════════════
# 讯飞星火 Provider（完整保留，当前不启用）
# ═══════════════════════════════════════════════════════════════

class XfyunSparkProvider(BaseProvider):
    """讯飞星火 Spark API Provider。

    环境变量：
        SPARK_API_PASSWORD  — API 密钥（Bearer token）
        SPARK_API_URL       — API 地址
        SPARK_MODEL         — 模型名称（默认 4.0Ultra）
        SPARK_ENABLED       — 是否启用（默认 false）
    """

    def __init__(self, timeout_seconds: int = 60):
        self._api_password = os.getenv("SPARK_API_PASSWORD", "")
        self._api_url = os.getenv(
            "SPARK_API_URL",
            "https://spark-api-open.xf-yun.com/v1/chat/completions",
        )
        self._model = os.getenv("SPARK_MODEL", "4.0Ultra")
        self._enabled = os.getenv("SPARK_ENABLED", "false").lower() in {
            "1", "true", "yes", "on",
        }
        self._timeout = httpx.Timeout(
            timeout_seconds,
            connect=min(timeout_seconds, 10),
            read=timeout_seconds,
            write=min(timeout_seconds, 10),
            pool=min(timeout_seconds, 5),
        )

    @property
    def provider_name(self) -> str:
        return "xfyun"

    @property
    def model_name(self) -> str:
        return self._model

    def is_available(self) -> bool:
        return self._enabled and bool(self._api_password.strip())

    async def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        chunks: list[str] = []
        async for chunk in self.chat_stream(system=system, user=user):
            chunks.append(chunk)
        return "".join(chunks)

    async def chat_stream(self, system: str, user: str, **kwargs: Any) -> AsyncIterator[str]:
        if not self.is_available():
            yield ""
            return

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST",
                self._api_url,
                headers={
                    "Authorization": f"Bearer {self._api_password}",
                    "Content-Type": "application/json",
                },
                json=payload,
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
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    async def chat_json(self, system: str, user: str, temperature: float = 0.1) -> Any:
        if not self.is_available():
            raise RuntimeError("讯飞星火 API 未配置")

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._api_url,
                headers={
                    "Authorization": f"Bearer {self._api_password}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response.raise_for_status()
            result = response.json()
            if result.get("code", 0) != 0:
                raise RuntimeError(
                    f"讯飞星火错误 {result.get('code')}: {result.get('message', '')}"
                )
            content = result["choices"][0]["message"]["content"]
            text = content.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                lines = lines[1:] if lines[0].startswith("```") else lines
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
                if text.lower().startswith("json"):
                    text = text[4:].strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start:end + 1]
            return json.loads(text)
