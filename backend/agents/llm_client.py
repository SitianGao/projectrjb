"""
LLM 客户端抽象层 —— 统一 DeepSeek/OpenAI 兼容接口

设计原则：
- 统一 chat_stream 异步流式接口，所有 Agent 通过此接口调用 LLM
- 支持多提供商：DeepSeek（主力）、OpenAI（备选）
- 内置重试 + 超时控制
- 兼容测试 Mock（只需实现 chat_stream 协议）

依赖：pip install httpx
"""

import asyncio
import logging
from typing import AsyncIterator, Optional

import httpx

from config import (
    DEEPSEEK_API_KEY,
    OPENAI_API_KEY,
    LLM_TIMEOUT,
    LLM_MAX_RETRIES,
)

logger = logging.getLogger(__name__)

# ---- 提供商端点 ----
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
OPENAI_BASE_URL = "https://api.openai.com/v1"

# 默认模型
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class LLMClient:
    """
    统一 LLM 客户端 —— 实现 chat_stream 协议。

    用法：
        client = LLMClient()            # 自动选择可用提供商
        async for chunk in client.chat_stream(system="你是...", user="你好"):
            print(chunk)
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Args:
            provider: "deepseek" / "openai"，不传则自动检测
            model: 模型名，不传则使用提供商默认值
            timeout: 单次请求超时秒数
            max_retries: 最大重试次数
        """
        self.timeout = timeout or LLM_TIMEOUT
        self.max_retries = max_retries or LLM_MAX_RETRIES

        # 自动选择提供商
        if provider:
            self.provider = provider
        elif DEEPSEEK_API_KEY:
            self.provider = "deepseek"
        elif OPENAI_API_KEY:
            self.provider = "openai"
        else:
            self.provider = "none"

        # 设置端点和密钥
        if self.provider == "deepseek":
            self.base_url = DEEPSEEK_BASE_URL
            self.api_key = DEEPSEEK_API_KEY
            self.model = model or DEFAULT_DEEPSEEK_MODEL
        elif self.provider == "openai":
            self.base_url = OPENAI_BASE_URL
            self.api_key = OPENAI_API_KEY
            self.model = model or DEFAULT_OPENAI_MODEL
        else:
            self.base_url = ""
            self.api_key = ""
            self.model = model or DEFAULT_DEEPSEEK_MODEL
            logger.warning(
                "未配置任何 LLM API Key（DEEPSEEK_API_KEY / OPENAI_API_KEY），"
                "LLM 调用将失败。测试环境请使用 Mock。"
            )

    async def chat_stream(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        流式对话接口 —— 所有 Agent 调用的统一入口。

        Args:
            system: 系统提示词
            user: 用户消息
            model: 模型名（覆盖实例默认值）

        Yields:
            str: LLM 输出的文本块（delta content）
        """
        if self.provider == "none":
            raise RuntimeError(
                "LLM 未配置。请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 环境变量，"
                "或在测试中使用 Mock LLM。"
            )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        effective_model = model or self.model
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async for chunk in self._stream_request(messages, effective_model):
                    yield chunk
                return  # 成功，退出重试循环
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
                last_error = e
                logger.warning(
                    "LLM 调用超时/连接错误 (attempt %s/%s, model=%s): %s",
                    attempt, self.max_retries, effective_model, e,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2 ** attempt, 8))  # 指数退避，上限 8s
            except httpx.HTTPStatusError as e:
                # 4xx 不重试（客户端错误），5xx 重试
                last_error = e
                status = e.response.status_code
                logger.warning(
                    "LLM 返回 HTTP %s (attempt %s/%s): %s",
                    status, attempt, self.max_retries, e,
                )
                if status >= 500 and attempt < self.max_retries:
                    await asyncio.sleep(min(2 ** attempt, 8))
                else:
                    break

        raise RuntimeError(
            f"LLM 调用失败（已重试 {self.max_retries} 次）: {last_error}"
        )

    async def _stream_request(
        self,
        messages: list,
        model: str,
    ) -> AsyncIterator[str]:
        """
        发送 streaming 请求到 OpenAI 兼容 API。

        使用 httpx 异步客户端 + stream 模式逐行解析 SSE。
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    # SSE 格式: "data: {...json...}"
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[len("data: "):]

                    # 流结束标记
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        import json
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        # 跳过无法解析的行
                        continue


# ---- 工厂函数 ----

def create_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMClient:
    """
    创建 LLM 客户端实例。

    Args:
        provider: "deepseek" / "openai"，不传则自动检测
        model: 模型名

    Returns:
        LLMClient 实例
    """
    client = LLMClient(provider=provider, model=model)
    logger.info(
        "LLM 客户端初始化完成: provider=%s, model=%s, timeout=%ss, max_retries=%s",
        client.provider, client.model, client.timeout, client.max_retries,
    )
    return client
