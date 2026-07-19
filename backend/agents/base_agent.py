"""
Agent 基类 —— 统一 LLM 调用、JSON 解析、Pydantic 校验、重试、日志。

所有业务 Agent 继承此类，通过 call_llm_json() 获取结构化输出。
"""

from __future__ import annotations

import json
import re
import time
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional

from pydantic import BaseModel

import config
from core.agent_context import AgentContext
from core.errors import AgentOutputInvalid

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """所有 Agent 的基类。

    子类必须实现:
    - get_system_prompt() → str
    - agent_name 属性（或使用类名）
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.llm = llm_client

    @property
    def agent_name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def get_system_prompt(self) -> str:
        """返回该 Agent 的系统提示词。"""
        ...

    # ── 流式调用（向后兼容）─────────────────────────────────

    async def call_llm(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict[str, str]] = None,
        response_schema: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """流式 LLM 调用 + 指数退避重试。"""
        system = system_prompt or self.get_system_prompt()

        if not self.llm:
            raise RuntimeError("LLM client is not configured")

        attempts = 1 if config.LLM_STRICT_MODE else 3
        last_error = None
        for attempt in range(attempts):
            try:
                logger.info("[%s] LLM call attempt %d", self.agent_name, attempt + 1)
                kwargs: dict = {"system": system, "user": user_prompt}
                if response_format is not None:
                    kwargs["response_format"] = response_format
                if response_schema is not None:
                    kwargs["response_schema"] = response_schema
                async for chunk in self.llm.chat_stream(**kwargs):
                    yield chunk
                return
            except Exception as e:
                last_error = e
                logger.error("[%s] Attempt %d failed: %s", self.agent_name, attempt + 1, e)
                if attempt == attempts - 1:
                    # 最终失败必须 raise，禁止 yield 中文提示
                    raise RuntimeError(
                        f"[{self.agent_name}] LLM 调用失败（已重试{attempts}次）"
                    ) from last_error
                else:
                    await __import__("asyncio").sleep(2 ** attempt)

    # ── 结构化 JSON 调用（核心方法）─────────────────────────

    async def call_llm_json(
        self,
        *,
        context: AgentContext,
        system_prompt: str = "",
        user_prompt: str,
        response_model: type[BaseModel],
        temperature: float = 0.1,
    ) -> BaseModel:
        """调用 LLM 并返回 Pydantic 校验后的结构化输出。

        流程:
        1. 非流式调用 LLM
        2. 提取 JSON
        3. Pydantic 校验
        4. 首次失败 → 自动修复一次
        5. 再次失败 → 抛出 AgentOutputInvalid

        Args:
            context: 统一 Agent 上下文
            system_prompt: 系统提示词（空则使用 get_system_prompt()）
            user_prompt: 用户提示词
            response_model: Pydantic 模型类（用于校验）
            temperature: LLM 温度

        Returns:
            通过 Pydantic 校验的模型实例

        Raises:
            AgentOutputInvalid: 输出无法解析或校验失败
        """
        request_id = str(uuid.uuid4())[:8]
        system = system_prompt or self.get_system_prompt()
        start = time.monotonic()

        logger.info(
            "[%s] call_llm_json start request_id=%s user_id=%s course_id=%s stage_id=%s task_id=%s",
            self.agent_name, request_id,
            context.user_id, context.course_id,
            context.stage_id or "-", context.task_id or "-",
        )

        if not self.llm:
            raise RuntimeError(f"{self.agent_name}: LLM client is not configured")

        # 第一次尝试
        raw = ""
        success = False
        try:
            model_name = response_model.__name__
            schema_hint = json.dumps(response_model.model_json_schema(), ensure_ascii=False)

            full_user_prompt = (
                f"{user_prompt}\n\n"
                f"## 输出要求\n"
                f"你必须只输出一个 JSON 对象，符合以下 Schema：\n"
                f"```json\n{schema_hint}\n```\n"
                f"不要输出 Markdown 代码块。不要输出解释文字。只输出 JSON。"
            )

            raw = await self.llm.chat(
                system=system,
                user=full_user_prompt,
                temperature=temperature,
            )
            parsed = self._extract_json(raw)
            result = response_model.model_validate(parsed)
            success = True
            self._log_completion(context, request_id, start, True)
            return result

        except Exception as first_error:
            logger.warning(
                "[%s] 首次校验失败 request_id=%s: %s",
                self.agent_name, request_id, first_error,
            )

            # 自动修复一次
            try:
                # 提取错误位置附近的上下文
                error_context = raw[:2000]
                error_str = str(first_error)
                char_match = re.search(r"char (\d+)", error_str)
                if char_match:
                    pos = int(char_match.group(1))
                    start = max(0, pos - 200)
                    end = min(len(raw), pos + 200)
                    error_context = f"...\n{raw[start:end]}\n...(错误在 char {pos} 附近)"

                repair_prompt = (
                    f"你上一次的输出无法通过 JSON 解析。\n\n"
                    f"错误信息: {error_str}\n\n"
                    f"错误位置附近的内容:\n```\n{error_context}\n```\n\n"
                    f"请修正 JSON 格式错误（如缺少逗号、引号不匹配等），确保输出合法 JSON。只输出修正后的完整 JSON 对象。"
                )
                raw2 = await self.llm.chat(
                    system=system,
                    user=repair_prompt,
                    temperature=0.0,
                )
                parsed2 = self._extract_json(raw2)
                result = response_model.model_validate(parsed2)
                success = True
                logger.info("[%s] 自动修复成功 request_id=%s", self.agent_name, request_id)
                self._log_completion(context, request_id, start, True)
                return result

            except Exception as second_error:
                self._log_completion(context, request_id, start, False, str(second_error))
                raise AgentOutputInvalid(
                    agent_name=self.agent_name,
                    reason=f"首次: {first_error}; 修复后: {second_error}",
                ) from second_error

    # ── JSON 提取 ────────────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> Any:
        """从 LLM 输出中提取 JSON 对象。

        处理: Markdown 代码块、前后文字、尾部逗号、缺少逗号。
        """
        if not text or not text.strip():
            raise ValueError("LLM 输出为空")

        text = text.strip()

        # 去除 ```json ... ``` 包裹
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            text = m.group(1).strip()

        # 找到第一个 { 或 [
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start >= 0 and end >= start:
                text = text[start:end + 1]
                break

        # 尝试解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 修复尾部逗号
            cleaned = re.sub(r",\s*([}\]])", r"\1", text)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # 修复缺少逗号: }" 或 ]" 或 }{ 或 ]{ 前缺少逗号
                cleaned = re.sub(r'(["\d\w\]}])\s*(["{\[])', r'\1,\2', cleaned)
                # 修复行尾缺少逗号: 值后面直接换行
                cleaned = re.sub(r'(["\d\w\]}\)])\s*\n\s*(["{\[])', r'\1,\n\2', cleaned)
                return json.loads(cleaned)

    # ── 日志 ─────────────────────────────────────────────────

    def _log_completion(
        self,
        context: AgentContext,
        request_id: str,
        start: float,
        success: bool,
        error_code: str = "",
    ) -> None:
        duration_ms = int((time.monotonic() - start) * 1000)
        usage = self.llm.last_usage if self.llm else None

        log_data = {
            "request_id": request_id,
            "session_id": context.session_id or "-",
            "agent_name": self.agent_name,
            "user_id": context.user_id,
            "course_id": context.course_id,
            "stage_id": context.stage_id or "-",
            "task_id": context.task_id or "-",
            "model": usage.model if usage else "-",
            "duration_ms": duration_ms,
            "success": success,
            "error_code": error_code,
        }
        level = logging.INFO if success else logging.ERROR
        logger.log(level, "[%s] completed %s", self.agent_name, json.dumps(log_data, ensure_ascii=False))
