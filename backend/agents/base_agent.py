"""
Agent 基类 —— 统一 LLM 调用、流式输出、重试、日志
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """所有 Agent 的基类"""

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.llm = llm_client

    @abstractmethod
    def get_system_prompt(self) -> str:
        """返回该 Agent 的系统提示词"""
        pass

    async def call_llm(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """统一的 LLM 流式调用 + 指数退避重试 + 日志"""
        system = system_prompt or self.get_system_prompt()

        for attempt in range(3):
            try:
                logger.info(f"[{self.__class__.__name__}] LLM call attempt {attempt + 1}")
                async for chunk in self.llm.chat_stream(
                    system=system,
                    user=user_prompt,
                ):
                    yield chunk
                return
            except Exception as e:
                logger.error(f"[{self.__class__.__name__}] Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    yield f"[提示: 内容生成失败（已重试3次），请稍后重新尝试。错误详情: {str(e)}]"
                else:
                    await asyncio.sleep(2 ** attempt)
