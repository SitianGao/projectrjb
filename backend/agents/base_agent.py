"""
BaseAgent —— 所有 Agent 的抽象基类

职责：
- 保存 LLM 客户端引用
- 提供 call_llm() 统一入口（system prompt + user prompt）
- 子类只需实现 get_system_prompt() 即可接入 LLM

设计依据：docs/ai/agent-io.md
"""

import logging
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Agent 基类 —— 最小化设计。

    子类需要：
    1. 实现 get_system_prompt() 返回系统提示词
    2. 通过 self.call_llm(user_prompt) 调用 LLM
    3. 通过 self.llm_client 访问底层客户端（特殊场景）
    """

    def __init__(self, llm_client):
        """
        Args:
            llm_client: 实现了 chat_stream(system, user, model) 协议的 LLM 客户端
        """
        self.llm_client = llm_client
        self.name = self.__class__.__name__

    def get_system_prompt(self) -> str:
        """
        返回该 Agent 的系统提示词。

        子类必须覆盖此方法。
        """
        raise NotImplementedError(
            f"{self.name}: 子类必须实现 get_system_prompt()"
        )

    async def call_llm(
        self,
        user_prompt: str,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        LLM 调用的统一入口 —— 组合 system prompt + user prompt 后流式请求。

        Args:
            user_prompt: 用户提示词（已拼接好的完整 prompt）
            model: 模型名（可选，覆盖客户端默认值）

        Yields:
            str: LLM 逐 chunk 输出的文本
        """
        system = self.get_system_prompt()

        logger.debug(
            "%s: 调用 LLM (model=%s), system_prompt_len=%s, user_prompt_len=%s",
            self.name,
            model or getattr(self.llm_client, 'model', 'unknown'),
            len(system),
            len(user_prompt),
        )

        async for chunk in self.llm_client.chat_stream(
            system=system,
            user=user_prompt,
            model=model,
        ):
            yield chunk
