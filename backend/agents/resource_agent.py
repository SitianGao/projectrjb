"""
ResourceAgent —— 学习资源生成智能体

根据学习路径、学生画像和知识库，生成个性化多模态学习资源。

合同（对齐 docs/design.md §10.4.3）:
    主入口: generate_resources(topic, resource_types, difficulty, profile, knowledge_context)
    返回:   {"resources": [{"type", "title", "topic", "difficulty", "content"}, ...]}

v2 入口: generate_resources_v2(context, topic, resource_types, ...)
    返回:   ResourceGenerationOutput (Pydantic 校验后的结构化输出)
"""
import json
import logging
from typing import Optional, List, Dict

try:
    from config import RESOURCE_STRICT_MODE
except ModuleNotFoundError:
    from backend.config import RESOURCE_STRICT_MODE

from core.agent_context import AgentContext
from core.errors import ResourceSchemaInvalid
from core.knowledge_service import knowledge_service

from .base_agent import BaseAgent

from .schemas import (
    ResourceMeta,
    ResourceGenerationOutput,
    GenerationMeta,
    DocumentContent,
    SectionData,
    ExerciseContent,
    ExerciseQuestion,
    QuestionOption,
    MindmapContent,
    MindmapNode,
    PptContent,
    SlideData,
    SlideElement,
)

from .prompts.resource_prompts import RESOURCE_SYSTEM_PROMPT, TYPE_PROMPTS

logger = logging.getLogger(__name__)

# 星火 PPT API 大纲格式
SPARK_PPT_OUTLINE_SCHEMA = """
请按照以下 JSON 格式输出 PPT 大纲，用于调用星火 PPT API 生成专业课件：

```json
{
  "outline": [
    {
      "title": "章节标题",
      "subtitles": [
        {
          "title": "子标题",
          "content": "内容要点（简短描述，用于 PPT 排版）"
        }
      ]
    }
  ]
}
```

要求：
1. outline 数组最多 20 个一级章节（实际建议 8-12 个）
2. 每个章节最多 5 个子标题
3. 每个子标题的 content 控制在 50 字以内，用于 PPT 排版参考
4. 第一个章节通常是封面/标题页
5. 最后一个章节通常是小结/课后任务
6. 根据学生难度调整内容深度
"""


class ResourceAgent(BaseAgent):
    """根据学习路径生成个性化学习资源"""

    def __init__(self, llm_client=None):
        super().__init__(llm_client)

    # 各资源类型的详细 Prompt 模板 (v1 —— 向后兼容)
    TYPE_PROMPTS = {
        "document": (
            "生成一份结构化 Markdown 讲解文档，要求：\n"
            "- 从生活/工程场景切入，引出核心概念\n"
            "- 给出清晰定义和关键公式（如有），配合文字解释\n"
            "- 提供 1-2 个具体示例或应用案例\n"
            "- 末尾列出 3-5 个关键要点和常见误区\n"
            "- 标注「建议核实」若涉及具体数值或年代"
        ),
        "mindmap": (
            "生成一个嵌套 Markdown 列表作为思维导图（前端用 markmap 渲染），要求：\n"
            "- 根节点为知识点名称\n"
            "- 第二层 3-5 个维度（如：概念定义、工作原理、应用场景、常见误区、相关技术）\n"
            "- 第三层每个维度展开 2-4 个子节点\n"
            "- 节点文字简短可控（8-15 字），可用 - 和缩进写出完整层级\n"
            "- 不使用序号，纯 Markdown 列表，缩进用 2 个空格"
        ),
        "exercise": (
            TYPE_PROMPTS["exercise"]
        ),
        "code": (
            TYPE_PROMPTS["code"]
        ),
        "reading": (
            "生成一份拓展阅读推荐材料，要求：\n"
            "- 推荐 3-5 份高质量文献/教程/视频，覆盖「入门 → 深入 → 前沿」三层\n"
            "- 每份材料附：标题、类型（论文/教材/博客/视频）、一句话推荐理由、适合什么阶段的读者\n"
            "- 提供一个「建议阅读顺序」和预估总时长\n"
            "- 若有开源代码或交互式 Demo，标注链接提示\n"
            "- 文末附「拓展思考题」2-3 道，引导读者主动探索"
        ),
        "ppt": (
            "生成一份 PPT 讲稿大纲（8-12 张 slide），要求：\n"
            "- Slide 1: 标题页（知识点名称 + 一句话价值主张）\n"
            "- Slide 2: 学习目标（3-4 条，以「学完本节你将能够…」开头）\n"
            "- Slide 3-4: 概念导入（场景/问题驱动，引出为什么需要这个知识）\n"
            "- Slide 5-7: 核心内容（每 slide 一个关键点，含定义/公式/图示说明）\n"
            "- Slide 8-9: 示例/案例（对比 before/after 或代码/结果）\n"
            "- Slide 10: 常见误区（3 个典型错误及正确理解）\n"
            "- Slide 11: 小结（回顾 3 个关键 takeaway）\n"
            "- Slide 12: 课后任务（练习题或拓展阅读推荐）\n"
            "- 每 slide 含 slide 标题 + 3-5 个 bullet points，标注「讲师备注」提示"
        ),
    }

    def get_system_prompt(self) -> str:
        return RESOURCE_SYSTEM_PROMPT

    def _build_generate_prompt(
        self,
        topic: str,
        resource_types: list,
        difficulty: str,
        profile_json: str,
        context_text: str,
        stage_info: Optional[dict] = None,
        path_goal: Optional[str] = None,
    ) -> str:
        """为 LLM 构建含类型详细要求的生成提示词（v2: 关卡对齐）"""
        lines = [
            f"知识点: {topic}",
            f"难度: {difficulty}",
            f"资源类型: {json.dumps(resource_types, ensure_ascii=False)}",
        ]

        # ── 关卡上下文（v2：关卡对齐） ──
        if stage_info and isinstance(stage_info, dict):
            lines.append("\n## 当前关卡信息（资源必须贴合此上下文）")
            stage_title = stage_info.get("title", "")
            if stage_title:
                lines.append(f"关卡名称: {stage_title}")
            objectives = stage_info.get("objectives", "")
            if objectives:
                lines.append(f"关卡目标: {objectives}")
            stage_topics = stage_info.get("topics") or []
            if stage_topics:
                lines.append(f"关卡知识点: {', '.join(stage_topics)}")
            tasks = stage_info.get("tasks") or []
            if tasks:
                lines.append("关卡任务清单:")
                for i, t in enumerate(tasks, 1):
                    task_desc = t.get("task", "") if isinstance(t, dict) else str(t)
                    resource_hint = t.get("resource_type", "") if isinstance(t, dict) else ""
                    extra = f"  → 推荐资源类型: {resource_hint}" if resource_hint else ""
                    lines.append(f"  {i}. {task_desc}{extra}")
            stage_index = stage_info.get("stage_index")
            if stage_index is not None:
                lines.append(f"这是学习路径的第 {stage_index} 个阶段。")
            previous_stage = stage_info.get("previous_stage_title", "")
            if previous_stage:
                lines.append(f"前置关卡: {previous_stage}（可在资源中简要回顾前置知识点）")
            next_stage = stage_info.get("next_stage_title", "")
            if next_stage:
                lines.append(f"下一关卡: {next_stage}（可在资源末尾预告，激发学习预期）")

        if path_goal:
            lines.append(f"\n学习路径总目标: {path_goal}")
            if stage_info and isinstance(stage_info, dict):
                lines.append("请将当前关卡放在整个学习路径中定位，让资源体现「这一步在通向什么目标」。")

        lines.append(f"\n学生画像:\n{profile_json}")
        if context_text:
            lines.append(f"知识库上下文:\n{context_text}")

        lines.append("\n## 各类型生成要求")
        for rtype in resource_types:
            detail = TYPE_PROMPTS.get(rtype) or self.TYPE_PROMPTS.get(
                rtype, f"请生成 {rtype} 类型的资源。"
            )
            lines.append(f"\n### {rtype}\n{detail}")

        # 关卡对齐的强调
        if stage_info and isinstance(stage_info, dict):
            lines.append(
                "\n## 关卡对齐检查清单\n"
                "生成每份资源时请检查：\n"
                "1. 标题是否反映了关卡目标（而非仅仅知识点名称）？\n"
                "2. 内容是否覆盖了关卡任务的具体要求？\n"
                "3. 练习题/代码是否直接服务于关卡中的 task？\n"
                "4. 难度是否匹配学生当前阶段（不超前、不滞后）？"
            )

        lines.append(
            "\n请严格输出 JSON："
            "{\"resources\":[{\"type\":\"exercise\",\"title\":\"...\","
            "\"topic\":\"...\",\"difficulty\":\"初级\",\"content\":{...}}]}。"
            "document、exercise、mindmap、ppt 的 content 必须是符合上方 Schema 的 JSON 对象，"
            "禁止把 Markdown 字符串放进 content。"
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 主入口（合同方法 —— v1 向后兼容）
    # ------------------------------------------------------------------
    async def generate_resources(
        self,
        topic: str,
        resource_types: Optional[List[str]] = None,
        difficulty: str = "中级",
        profile: Optional[dict] = None,
        knowledge_context: Optional[List[str]] = None,
        stage_info: Optional[dict] = None,
        path_goal: Optional[str] = None,
    ) -> Dict:
        """
        生成学习资源（v2: 关卡对齐）。

        Args:
            topic: 知识点主题
            resource_types: 要生成的资源类型列表，默认 ["document"]
            difficulty: 难度等级（初级/中级/高级）
            profile: 学生画像
            knowledge_context: RAG 检索到的知识库上下文
            stage_info: 当前关卡信息（v2 新增）:
                - title: 关卡名称
                - objectives: 关卡学习目标
                - topics: 关卡涵盖知识点列表
                - tasks: 关卡任务列表 [{task, resource_type, estimated_hours}, ...]
                - stage_index: 关卡序号（第几个阶段）
                - previous_stage_title: 前置关卡名（用于知识串联）
                - next_stage_title: 下一关卡名（用于学习预期引导）
            path_goal: 学习路径总目标（v2 新增）

        Returns:
            {"resources": [{"type", "title", "topic", "difficulty", "content"}, ...]}
        """
        # 构造 AgentContext（v2 过渡：为 orchestrator 提供统一上下文）
        course_id = "default_course"
        if stage_info and isinstance(stage_info, dict):
            course_id = stage_info.get("course_id", "default_course")
        context = AgentContext(
            user_id=profile.get("user_id", "default") if profile else "default",
            course_id=course_id,
        )

        resource_types = resource_types or ["document"]
        profile = profile or {}
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        context_text = "\n".join(knowledge_context or [])

        if self.llm:
            try:
                user_prompt = self._build_generate_prompt(
                    topic=topic,
                    resource_types=resource_types,
                    difficulty=difficulty,
                    profile_json=profile_json,
                    context_text=context_text,
                    stage_info=stage_info,
                    path_goal=path_goal,
                )
                chunks = []
                async for chunk in self.call_llm(user_prompt):
                    chunks.append(chunk)
                raw = "".join(chunks)
                result = self._parse_and_validate(raw, topic, resource_types, difficulty, profile)
                if result is not None:
                    result["generation_meta"] = {
                        "generation_source": "llm",
                        "fallback_used": False,
                        "fallback_type": None,
                    }
                    return result
            except Exception as exc:
                logger.warning("ResourceAgent LLM 调用失败，回退规则化: %s", exc)

        result = self._rule_based_resources(topic, resource_types, difficulty, profile, stage_info, knowledge_context=knowledge_context)
        result["generation_meta"] = {
            "generation_source": "llm_failed_rag_enriched" if knowledge_context else "outline",
            "fallback_used": True,
            "fallback_type": "knowledge_base_basic" if knowledge_context else "outline",
        }
        return result

    # ------------------------------------------------------------------
    # LLM 输出校验
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_and_validate(
        raw: str,
        topic: str,
        resource_types: List[str],
        difficulty: str,
        profile: dict,
    ) -> Optional[Dict]:
        """
        校验 LLM 输出。

        合法条件:
        1. 能够解析为合法 JSON
        2. 包含 "resources" 键
        3. "resources" 是 list

        Returns:
            合法的 dict，或 None（表示需要回退）
        """
        # 1. 解析 JSON
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            logger.warning("ResourceAgent: LLM 输出非合法 JSON，回退规则化")
            return None

        # 2. 检查 resources 键
        if "resources" not in data:
            logger.warning("ResourceAgent: LLM 输出缺少 resources 键，回退规则化")
            return None

        # 3. 检查 resources 是 list
        resources = data["resources"]
        if not isinstance(resources, list):
            logger.warning("ResourceAgent: resources 不是 list，回退规则化")
            return None

        # 4. 规范化每个资源项，确保 5 个必有字段
        normalized = []
        for i, item in enumerate(resources):
            if not isinstance(item, dict):
                continue
            resource_type = item.get("type") or item.get("resource_type") or (
                resource_types[0] if resource_types else "document"
            )
            content = item.get("content", "")
            if resource_type in {"document", "exercise", "mindmap", "ppt"}:
                if not isinstance(content, dict):
                    # LLM 常把 document 输出为 Markdown 字符串而非结构化对象
                    # 对于 document 类型：接收并包装为 dict，避免不必要的降级
                    if resource_type == "document" and isinstance(content, str) and len(content) > 100:
                        content = {"markdown_sections": content}
                    elif resource_type == "mindmap" and isinstance(content, str) and len(content) > 20:
                        content = {"markdown_tree": content}
                    elif resource_type == "ppt" and isinstance(content, str) and len(content) > 50:
                        content = {"markdown_slides": content}
                    else:
                        logger.warning("ResourceAgent: %s content 不是结构化对象，回退规则化", resource_type)
                        return None
                try:
                    validated = ResourceAgent._validate_by_type(resource_type, content)
                    content = validated.model_dump() if hasattr(validated, "model_dump") else content
                except ResourceSchemaInvalid as exc:
                    # 如果包装后的 dict 仍然校验失败，对于 document 做最终兜底
                    if resource_type == "document" and isinstance(content, dict) and "markdown_sections" in content:
                        logger.warning("ResourceAgent: document markdown 校验失败，使用原始字符串: %s", exc)
                        # 保持 markdown_sections，跳过 Pydantic 校验
                    else:
                        logger.warning("ResourceAgent: %s content 校验失败: %s", resource_type, exc)
                        return None
            normalized.append({
                "type": resource_type,
                "title": item.get("title", f"{topic} 学习资源"),
                "topic": item.get("topic", topic),
                "difficulty": item.get("difficulty", difficulty),
                "content": content,
            })

        if not normalized:
            logger.warning("ResourceAgent: resources 为空，回退规则化")
            return None

        return {"resources": normalized}

    # ------------------------------------------------------------------
    # 规则化兜底（无需 LLM）—— v1
    # ------------------------------------------------------------------
    def _rule_based_resources(
        self,
        topic: str,
        resource_types: List[str],
        difficulty: str,
        profile: dict,
        stage_info: Optional[dict] = None,
        knowledge_context: Optional[List[str]] = None,
    ) -> Dict:
        """开发期无 API Key 或 LLM 调用失败时使用的规则化资源生成（v2: 关卡感知）"""
        resources = []
        profile_inner = profile.get("profile", profile)
        cognitive = profile_inner.get("cognitive_style", "")
        has_rag = bool(knowledge_context)

        # 关卡感知的标题前缀
        stage_prefix = ""
        if stage_info and isinstance(stage_info, dict):
            stage_name = stage_info.get("title", "")
            if stage_name:
                stage_prefix = f"【{stage_name}】"

        for rtype in resource_types:
            title_map = {
                "document": f"{stage_prefix}{topic} 讲解文档",
                "mindmap": f"{stage_prefix}{topic} 思维导图",
                "exercise": f"{stage_prefix}{topic} 练习题",
                "code": f"{stage_prefix}{topic} 代码案例",
                "reading": f"{stage_prefix}{topic} 拓展阅读",
                "ppt": f"{stage_prefix}{topic} PPT 大纲",
            }

            content = self._build_content(rtype, topic, difficulty, cognitive, stage_info, has_rag=has_rag, has_llm=False)
            resources.append({
                "type": rtype,
                "title": title_map.get(rtype, f"{topic} 学习资源"),
                "topic": topic,
                "difficulty": difficulty,
                "content": content,
            })

        return {"resources": resources}

    @staticmethod
    def _build_stage_context_markdown(stage_info: Optional[dict]) -> str:
        """构建关卡背景 markdown 块（统一注入到各类型资源中）。"""
        if not stage_info or not isinstance(stage_info, dict):
            return ""

        stage_title = stage_info.get("title", "")
        if not stage_title:
            return ""

        lines = ["> 🎯 **当前关卡**：" + stage_title]

        objectives = stage_info.get("objectives", "")
        if objectives:
            lines.append("> **关卡目标**：" + str(objectives))

        stage_topics = stage_info.get("topics") or []
        if stage_topics:
            lines.append("> **涵盖知识点**：" + ", ".join(stage_topics))

        tasks = stage_info.get("tasks") or []
        if tasks:
            lines.append("> **关卡任务**：")
            for t in tasks:
                task_desc = t.get("task", "") if isinstance(t, dict) else str(t)
                lines.append(f">  - {task_desc}")

        stage_index = stage_info.get("stage_index")
        if stage_index is not None:
            lines.append(f"> 这是学习路径的第 **{stage_index}** 个阶段")

        lines.append("")  # 空行分隔
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 骨骼内容构建
    # ------------------------------------------------------------------
    def _build_content(
        self,
        rtype: str,
        topic: str,
        difficulty: str,
        cognitive: str,
        stage_info: Optional[dict] = None,
        has_rag: bool = False,
        has_llm: bool = False,
    ) -> str:
        """为每种资源类型生成基础内容（第6轮改造：去掉模板痕迹）。"""
        diff_labels = {"初级": "入门", "中级": "进阶", "高级": "深入"}
        level = diff_labels.get(difficulty, "入门")
        stage_context = self._build_stage_context_markdown(stage_info)

        # 降级提示
        if not has_llm and has_rag:
            degrade_note = "> AI 生成暂时不可用，已根据课程知识库为你准备基础版本。\n\n"
        elif not has_llm and not has_rag:
            degrade_note = "> 暂时无法生成完整内容，已为你创建学习提纲。请稍后重试。\n\n"
        else:
            degrade_note = ""

        if rtype == "document":
            # RAG 可用时：提供比纯提纲更丰富的内容骨架
            if has_rag:
                return (
                    f"# {topic}\n\n"
                    f"{degrade_note}"
                    f"{stage_context}"
                    f"## 情境导入\n\n"
                    f"在正式学习 {topic} 之前，先思考一个实际问题来建立感性认识。"
                    f"课程知识库已为你匹配了相关材料，建议先浏览下方「关键课程资料」中的章节。\n\n"
                    f"## 核心知识结构\n\n"
                    f"知识库中已检索到与 {topic} 相关的内容。请重点阅读：\n\n"
                    f"1. **概念与定义** — {topic} 的基本原理和数学表达\n"
                    f"2. **关键方法** — 解决相关问题的核心步骤\n"
                    f"3. **应用案例** — {topic} 在实际工程中的典型应用\n"
                    f"4. **定理前提与注意事项** — 如何识别 {topic} 的适用条件\n\n"
                    f"## 理解检测\n\n"
                    f"阅读完成后，尝试回答以下问题来检验理解：\n\n"
                    f"1. 什么是 {topic}？用自己的话给一个简短定义\n"
                    f"2. {topic} 需要哪些前置知识？\n"
                    f"3. 在什么场景下 {topic} 是首选的解决方案？\n\n"
                    f"## 关键课程资料\n\n"
                    f"知识库已根据当前任务自动匹配相关章节，请在左侧目录或上方资源区查看。\n\n"
                    f"## 简短总结\n\n"
                    f"{topic} 是{level}阶段学习的重要内容。当前基于课程知识库的检索结果为"
                    f"你准备了基础框架，配合阅读原始章节可以获得完整的理解。\n"
                )
            else:
                return (
                    f"# {topic}\n\n"
                    f"{degrade_note}"
                    f"{stage_context}"
                    f"## 本任务要解决什么\n\n"
                    f"掌握 {topic} 的核心概念和基本应用，为后续学习奠定基础。\n\n"
                    f"## 核心知识点\n\n"
                    f"- {topic} 的定义与基本原理\n"
                    f"- {topic} 的典型应用场景\n"
                    f"- {topic} 中的常见误区和注意事项\n\n"
                    f"## 推荐学习顺序\n\n"
                    f"1. 先阅读课程知识库中关于 {topic} 的章节\n"
                    f"2. 理解核心定义后，完成配套练习题\n"
                    f"3. 用自己的话复述关键概念，检查理解深度\n"
                    f"4. 尝试在实际问题中应用所学知识\n\n"
                    f"## 关键课程资料\n\n"
                    f"- 知识库中「{topic}」相关章节\n"
                    f"- 课程配套练习和示例代码\n\n"
                    f"## 简短总结\n\n"
                    f"{topic} 是{level}阶段的重要知识点。建议先掌握其核心定义和适用场景，"
                    f"再通过练习巩固理解。遇到困难时可以随时向 AI 导师提问。\n"
                )
        elif rtype == "mindmap":
            return (
                f"- {topic}\n"
                f"  - 概念定义\n"
                f"    - 核心术语\n"
                f"    - 基本原理\n"
                f"  - 应用场景\n"
                f"    - 典型用途\n"
                f"    - 实践案例\n"
                f"  - 常见问题\n"
                f"    - 易错点\n"
                f"    - 注意事项\n"
            )
        elif rtype == "exercise":
            return {
                "instructions": f"请完成以下关于「{topic}」的练习。",
                "questions": [
                    {
                        "id": "q1",
                        "type": "single_choice",
                        "stem": f"关于 {topic}，以下说法正确的是？",
                        "options": [
                            {"key": "A", "text": f"{topic} 是当前阶段需要掌握的核心知识"},
                            {"key": "B", "text": f"{topic} 与实际应用完全无关"},
                            {"key": "C", "text": f"学习 {topic} 不需要理解任何前置概念"},
                            {"key": "D", "text": "以上说法都正确"},
                        ],
                        "correct_answer": ["A"],
                        "explanation": f"{topic} 是当前学习任务的核心内容，需要结合定义、原理和应用理解。",
                        "difficulty": "easy" if difficulty == "初级" else "medium",
                        "knowledge_point_ids": [topic],
                    },
                    {
                        "id": "q2",
                        "type": "short_answer",
                        "stem": f"请用自己的话概括 {topic} 的核心思想，并给出一个应用场景。",
                        "options": [],
                        "correct_answer": [f"围绕 {topic} 的定义、核心机制和应用场景作答"],
                        "explanation": "回答应同时包含概念说明和具体应用，避免只背诵定义。",
                        "difficulty": "medium",
                        "knowledge_point_ids": [topic],
                    },
                ],
            }
        elif rtype == "code":
            func_name = topic.lower().replace(" ", "_").replace("-", "_")
            # 关卡感知：将关卡任务作为代码示例的场景说明
            task_scenario = ""
            if stage_info and isinstance(stage_info, dict):
                stage_tasks = stage_info.get("tasks") or []
                if stage_tasks:
                    task_scenario = "**关卡实战场景**：\n"
                    for t in stage_tasks:
                        td = t.get("task", "") if isinstance(t, dict) else str(t)
                        task_scenario += f"> 任务：{td}\n"
                    task_scenario += "\n"
            # 生成结构化代码实验内容（而非纯 Markdown 代码块）
            starter_code = (
                f'"""\n'
                f'{topic} — 参数实验（{level}）\n'
                f'通过调整参数观察 {topic} 的行为变化。\n'
                f'"""\n\n'
                f'import numpy as np\n\n'
                f'# ── 可调参数 ──\n'
                f'learning_rate = 0.01\n'
                f'n_iters = 500\n\n'
                f'# ── 步骤 1：生成数据 ──\n'
                f'np.random.seed(42)\n'
                f'n_samples = 100\n'
                f'X = np.random.randn(n_samples, 3)\n'
                f'y = X[:, 0] * 2.5 + X[:, 1] * (-1.3) + np.random.randn(n_samples) * 0.1\n\n'
                f'# ── 步骤 2：训练模型 ──\n'
                f'weights = np.zeros(3)\n'
                f'for i in range(n_iters):\n'
                f'    y_pred = X @ weights\n'
                f'    loss = np.mean((y_pred - y) ** 2)\n'
                f'    gradient = (2 / n_samples) * X.T @ (y_pred - y)\n'
                f'    weights -= learning_rate * gradient\n'
                f'    if i % 50 == 0:\n'
                f'        print(f"epoch {i}, loss = {{loss:.6f}}")\n\n'
                f'# ── 步骤 3：结果 ──\n'
                f'final_pred = X @ weights\n'
                f'final_loss = np.mean((final_pred - y) ** 2)\n'
                f'print(f"\\n最终 loss = {{final_loss:.6f}}")\n'
                f'print(f"学习到的权重: {{np.round(weights, 4)}}")\n'
            )

            return {
                "title": f"{topic} — 参数实验",
                "scenario": f"本实验通过调整学习率等参数，观察 {topic} 的训练过程和收敛行为。学生将对比不同参数下的损失曲线，理解参数对模型训练的影响。",
                "experiment_mode": "param_experiment",
                "difficulty": level,
                "estimated_minutes": 25,
                "learning_objectives": [
                    f"理解 {topic} 的核心原理",
                    "掌握学习率对训练收敛的影响",
                    "能够通过观察损失曲线判断训练状态",
                ],
                "knowledge_points": [topic],
                "prerequisite_knowledge": ["Python 基础", "NumPy 基础"],
                "steps": [
                    {
                        "step_id": "step-1",
                        "title": "运行基准实验",
                        "instruction": "使用默认参数运行代码，观察损失曲线的整体趋势。",
                        "code_snippet": "# 直接点击「运行实验」按钮",
                        "expected_result": "损失值随迭代次数增加而下降",
                    },
                    {
                        "step_id": "step-2",
                        "title": "调整学习率",
                        "instruction": "将学习率从 0.01 改为 0.1 和 1.0，分别运行，观察损失曲线变化。",
                        "code_snippet": "learning_rate = 0.1  # 试试 1.0",
                        "expected_result": "较大学习率可能导致损失震荡或发散",
                        "hint": "学习率过大会导致参数更新步长过大，可能跳过最优解",
                    },
                    {
                        "step_id": "step-3",
                        "title": "对比与总结",
                        "instruction": "对比不同学习率下的损失曲线，总结规律。",
                        "code_snippet": "",
                        "expected_result": "较小学习率收敛稳定但慢，较大学习率可能震荡",
                    },
                ],
                "starter_code": starter_code,
                "editable_parameters": [
                    {
                        "name": "learning_rate",
                        "label": "学习率",
                        "default_value": 0.01,
                        "allowed_values": [0.001, 0.01, 0.1, 0.5, 1.0],
                        "explanation": "控制每次参数更新的步长",
                    },
                    {
                        "name": "n_iters",
                        "label": "迭代次数",
                        "default_value": 500,
                        "allowed_values": [100, 500, 1000],
                        "explanation": "训练的总迭代轮数",
                    },
                ],
                "observation_questions": [
                    "学习率为 0.01 时，损失曲线的形状是什么样的？",
                    "学习率调大后，损失曲线发生了什么变化？",
                    "哪个学习率的收敛速度最快？哪个最稳定？",
                ],
                "common_errors": [
                    "学习率设置过大导致损失值变为 NaN",
                    "迭代次数不足导致模型未收敛",
                    "忘记设置随机种子导致结果不可复现",
                ],
                "expected_phenomena": [
                    "学习率 0.01：损失缓慢但稳定下降",
                    "学习率 0.1：损失快速下降",
                    "学习率 1.0：损失可能出现震荡或发散",
                ],
                "visualization_type": "loss_curve",
                "personalization_reason": f"学生对 {topic} 的掌握度较低，通过参数实验加深理解",
                "language": "python",
                "code": starter_code,
                "explanation": f"本实验演示 {topic} 的核心实现，通过调整学习率观察训练行为。",
            }
        elif rtype == "reading":
            return (
                f"# {topic} 拓展阅读\n\n"
                f"{stage_context}"
                f"## 推荐文献\n\n"
                f"1. **经典教材**: 相关章节 —— {topic}原理与推导\n"
                f"2. **综述文章**: {topic} 最新研究进展\n"
                f"3. **实践指南**: 如何在实际项目中应用{topic}\n\n"
                f"## 阅读要点\n\n"
                f"- 关注{level}篇的核心推导过程\n"
                f"- 对比不同方法的优缺点\n"
                f"- 思考如何与已学知识关联\n\n"
                f"> 建议核实: 具体文献请以课程指定教材为准。\n"
            )
        elif rtype == "ppt":
            # 关卡感知的 PPT：封面加入关卡关联信息
            stage_subtitle = ""
            if stage_info and isinstance(stage_info, dict):
                st = stage_info.get("title", "")
                if st:
                    stage_subtitle = f"  - 关联关卡：{st}\n"
            slides = [
                f"Slide 1: 封面 —— {topic}（{level}）\n"
                f"  - 副标题：从原理到实践的系统讲解\n"
                f"{stage_subtitle}"
                f"  - 讲师备注：本课件面向{level}阶段学习者，建议配合代码演示使用",
                f"Slide 2: 学习目标\n"
                f"  - 理解{topic}的基本概念和数学定义\n"
                f"  - 掌握{topic}的核心算法或推导过程\n"
                f"  - 能够在实际项目中应用{topic}解决相关问题\n"
                f"  - 了解{topic}的局限性和改进方向\n"
                f"  - 讲师备注：明确告知学员本节能达成的具体能力，建立学习预期",
                f"Slide 3: 问题引入 —— 为什么需要{topic}？\n"
                f"  - 现实痛点：描述一个没有{topic}时会遇到的困难\n"
                f"  - 传统方法的局限性\n"
                f"  - {topic}如何解决上述问题\n"
                f"  - 讲师备注：用一个贴近学员经验的具体场景引发共鸣，避免纯理论开场",
                f"Slide 4: 概念导入\n"
                f"  - 从生活/工程场景自然过渡到技术概念\n"
                f"  - 给出直觉层面的理解（先用白话讲，再引入术语）\n"
                f"  - 可视化建议：用对比示意图展示「有/无{topic}」的差异\n"
                f"  - 讲师备注：此 slide 的目标是让学员在听到公式之前先建立直觉",
                f"Slide 5: 核心定义与数学表达\n"
                f"  - 标准定义（引用教材或经典论文）\n"
                f"  - 数学公式及符号说明（逐项标注含义）\n"
                f"  - 关键假设与适用范围\n"
                f"  - 讲师备注：公式推导不宜过快，每步停顿 5-10 秒让学员消化",
                f"Slide 6: 算法流程 / 推导步骤\n"
                f"  - 步骤 1：输入/前置条件\n"
                f"  - 步骤 2：核心计算（画流程图辅助说明）\n"
                f"  - 步骤 3：输出/结果解释\n"
                f"  - 讲师备注：可用 Mermaid 流程图在讲解时同步展示，降低认知负荷",
                f"Slide 7: 代码实现\n"
                f"  - 关键代码片段（5-10 行核心逻辑）\n"
                f"  - 逐行注释说明 WHAT 和 WHY\n"
                f"  - 运行结果截图或预期输出\n"
                f"  - 讲师备注：建议现场运行代码或播放录屏，比静态展示效果更好",
                f"Slide 8: 实例演示\n"
                f"  - 具体案例：输入 → 处理 → 输出（完整走一遍）\n"
                f"  - 对比 before/after 效果\n"
                f"  - 如果可能，展示不同参数下的结果变化\n"
                f"  - 讲师备注：选择简单但足够体现核心思想的例子，避免过于复杂",
                f"Slide 9: 应用场景\n"
                f"  - 工业应用 1：具体场景 + 实施方案\n"
                f"  - 学术应用 2：研究方向 + 代表性成果\n"
                f"  - 跨界应用 3：在其他领域的创新用途\n"
                f"  - 讲师备注：鼓励学员分享自己遇到的相关场景，增强互动",
                f"Slide 10: 常见误区\n"
                f"  - 误区 1：错误理解及正确认识\n"
                f"  - 误区 2：典型调参错误及规避方法\n"
                f"  - 误区 3：适用范围混淆及判断标准\n"
                f"  - 讲师备注：误区来源于真实教学中学生的常见错误，比纯讲正确知识更有记忆点",
                f"Slide 11: 小结\n"
                f"  - 回顾 3 个核心 takeaway\n"
                f"  - 知识地图：{topic}在整个知识体系中的位置\n"
                f"  - 与前后知识点的关联：前置依赖 → {topic} → 后续延伸\n"
                f"  - 讲师备注：用一句话总结本节——学员离开时应该带走的最核心理解",
                f"Slide 12: 课后任务\n"
                f"  - 必做：2-3 道基础练习（巩固核心）\n"
                f"  - 选做：1 个实践项目（拓展应用）\n"
                f"  - 拓展阅读推荐：1-2 篇相关论文或教程\n"
                f"  - 讲师备注：明确告知下节课内容，让学员有连贯的学习预期",
            ]
            return "\n\n".join(slides)
        else:
            return f"# {topic} 学习资源\n\n（内容待生成）\n"

    # ==================================================================
    # v2 新增方法
    # ==================================================================

    # ── 类型专用 Pydantic 校验器 ──────────────────────────────────

    @staticmethod
    def _validate_document(content: dict) -> DocumentContent:
        """校验 document 类型资源的 content 是否符合 DocumentContent schema。"""
        try:
            return DocumentContent.model_validate(content)
        except Exception as e:
            raise ResourceSchemaInvalid("document", str(e))

    @staticmethod
    def _validate_exercise(content: dict) -> ExerciseContent:
        """校验 exercise 类型资源的 content 是否符合 ExerciseContent schema。"""
        try:
            return ExerciseContent.model_validate(content)
        except Exception as e:
            raise ResourceSchemaInvalid("exercise", str(e))

    @staticmethod
    def _validate_mindmap(content: dict) -> MindmapContent:
        """校验 mindmap 类型资源的 content 是否符合 MindmapContent schema。"""
        try:
            return MindmapContent.model_validate(content)
        except Exception as e:
            raise ResourceSchemaInvalid("mindmap", str(e))

    @staticmethod
    def _validate_ppt(content: dict) -> PptContent:
        """校验 ppt 类型资源的 content 是否符合 PptContent schema。"""
        try:
            return PptContent.model_validate(content)
        except Exception as e:
            raise ResourceSchemaInvalid("ppt", str(e))

    @staticmethod
    def _validate_code(content: dict):
        """校验 code 类型资源的 content 是否符合 CodeExperimentContent schema。"""
        from .schemas import CodeExperimentContent
        try:
            return CodeExperimentContent.model_validate(content)
        except Exception as e:
            raise ResourceSchemaInvalid("code", str(e))

    @staticmethod
    def _validate_by_type(resource_type: str, content: dict):
        """分发到对应类型的 Pydantic 校验器。

        Args:
            resource_type: 资源类型（document / exercise / mindmap / ppt）
            content: 待校验的 content dict

        Returns:
            校验后的 Pydantic 模型实例；对于无结构化 schema 的类型返回原始 dict

        Raises:
            ResourceSchemaInvalid: Schema 校验失败
        """
        validators = {
            "document": ResourceAgent._validate_document,
            "exercise": ResourceAgent._validate_exercise,
            "mindmap": ResourceAgent._validate_mindmap,
            "ppt": ResourceAgent._validate_ppt,
            "code": ResourceAgent._validate_code,
        }
        validator = validators.get(resource_type)
        if validator is None:
            # 无结构化 schema 的类型（code / reading / audio 等），原样返回
            return content
        return validator(content)

    # ── 标题规范化 ──────────────────────────────────────────────

    @staticmethod
    def _normalize_title(topic: str, resource_type: str) -> str:
        """根据知识点和资源类型生成规范化标题。

        Args:
            topic: 知识点名称
            resource_type: 资源类型

        Returns:
            规范化后的标题字符串
        """
        title_map = {
            "document": f"{topic}核心讲义",
            "exercise": f"{topic}专项练习",
            "mindmap": f"{topic}知识导图",
            "ppt": f"{topic}教学课件",
            "code": f"{topic}代码案例",
        }
        return title_map.get(resource_type, f"{topic}学习资源")

    # ── 重复检测（占位）─────────────────────────────────────────

    @staticmethod
    def _check_duplicate_version(topic: str, resource_type: str, course_id: str) -> int:
        """检测是否存在同 topic + resource_type + course_id 的资源，确定版本号。

        当前为占位实现，始终返回 1。
        实际 DB 检查在 service 层完成。

        Args:
            topic: 知识点名称
            resource_type: 资源类型
            course_id: 课程 ID

        Returns:
            版本号（新资源为 1，已存在则为 existing.version + 1）
        """
        # TODO: 接入 service 层的 DB 查询
        # existing = db.query(Resource).filter_by(
        #     topic=topic, resource_type=resource_type, course_id=course_id
        # ).first()
        # if existing:
        #     return existing.version + 1
        return 1

    # ── 规则化兜底（v2 返回 ResourceGenerationOutput）────────────

    def _rule_based_resources_v2(
        self,
        topic: str,
        resource_types: list[str],
        difficulty: str,
        profile: dict,
        context: AgentContext,
        stage_info: dict | None = None,
        knowledge_context: str = "",
    ) -> ResourceGenerationOutput:
        """开发期无 LLM 时的规则化资源生成（v2：返回 ResourceGenerationOutput）。"""
        resources = []
        profile_inner = profile.get("profile", profile)
        cognitive = profile_inner.get("cognitive_style", "")

        for rtype in resource_types:
            content_str = self._build_content(rtype, topic, difficulty, cognitive, stage_info)
            resource = ResourceMeta(
                resource_type=rtype,
                title=self._normalize_title(topic, rtype),
                summary=f"{topic} — {rtype} 学习资源（规则生成）",
                difficulty=difficulty,
                content={"raw": content_str},
                course_id=context.course_id,
                stage_id=context.stage_id or "",
                task_id=context.task_id or "",
                user_id=context.user_id,
                knowledge_point_ids=list(context.knowledge_point_ids),
            )
            resources.append(resource)

        return ResourceGenerationOutput(
            resources=resources,
            topic=topic,
            difficulty=difficulty,
            total=len(resources),
        )

    # ── v2 Prompt 构建 ──────────────────────────────────────────

    def _build_generate_prompt_v2(
        self,
        topic: str,
        resource_types: list[str],
        difficulty: str,
        profile_json: str,
        knowledge_context: str,
        context: AgentContext,
        stage_info: dict | None = None,
    ) -> str:
        """为 generate_resources_v2 构建提示词（使用导入的 TYPE_PROMPTS）。"""
        lines = [
            f"课程 ID: {context.course_id}",
            f"知识点: {topic}",
            f"难度: {difficulty}",
            f"目标资源类型: {json.dumps(resource_types, ensure_ascii=False)}",
        ]

        if stage_info and isinstance(stage_info, dict):
            stage_title = stage_info.get("title", "")
            if stage_title:
                lines.append(f"当前关卡: {stage_title}")
            objectives = stage_info.get("objectives", "")
            if objectives:
                lines.append(f"关卡目标: {objectives}")

        lines.append(f"\n学生画像:\n{profile_json}")

        if knowledge_context:
            lines.append(f"\n{knowledge_context}")

        lines.append("\n## 各类型生成要求")
        for rtype in resource_types:
            # 优先使用导入的 TYPE_PROMPTS（v2 结构化 schema），回退到类级 TYPE_PROMPTS（v1）
            detail = TYPE_PROMPTS.get(rtype) or self.TYPE_PROMPTS.get(rtype, f"请生成 {rtype} 类型的资源。")
            lines.append(f"\n### {rtype}\n{detail}")

        lines.append(
            "\n请严格输出符合 ResourceGenerationOutput Schema 的 JSON 对象。"
        )
        return "\n".join(lines)

    # ── v2 主入口 ───────────────────────────────────────────────

    async def generate_resources_v2(
        self,
        *,
        context: AgentContext,
        topic: str,
        resource_types: list[str] | None = None,
        difficulty: str = "中级",
        profile: dict | None = None,
        stage_info: dict | None = None,
        knowledge_context: str | None = None,
    ) -> ResourceGenerationOutput:
        """生成学习资源（v2：Pydantic 结构化输出 + 类型校验）。

        Args:
            context: 统一 Agent 上下文（包含 course_id, user_id, stage_id, task_id）
            topic: 知识点主题
            resource_types: 要生成的资源类型列表，默认 ["document"]
            difficulty: 难度等级（初级/中级/高级）
            profile: 学生画像
            stage_info: 当前关卡信息（可选）
            knowledge_context: RAG 检索上下文（外部传入，避免重复检索）

        Returns:
            ResourceGenerationOutput: Pydantic 校验后的结构化资源列表
        """
        resource_types = resource_types or ["document"]
        profile = profile or {}
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)

        # 1. 检索知识库上下文（仅在外部未传入时）
        if knowledge_context is None:
            try:
                knowledge_context = knowledge_service.search_context(context.course_id, topic)
            except Exception as exc:
                logger.warning("ResourceAgent: 知识库检索失败，继续生成: %s", exc)
                knowledge_context = "（资料库中未找到可靠依据）"

        # 2. LLM 路径
        fallback_reason_code = None
        fallback_reason_detail = None
        if self.llm:
            try:
                user_prompt = self._build_generate_prompt_v2(
                    topic=topic,
                    resource_types=resource_types,
                    difficulty=difficulty,
                    profile_json=profile_json,
                    knowledge_context=knowledge_context,
                    context=context,
                    stage_info=stage_info,
                )
                result = await self.call_llm_json(
                    context=context,
                    user_prompt=user_prompt,
                    response_model=ResourceGenerationOutput,
                )
            except Exception as exc:
                fallback_reason_code = _classify_error_code(exc)
                fallback_reason_detail = str(exc)
                if RESOURCE_STRICT_MODE:
                    raise RuntimeError(
                        f"严格模式：ResourceAgent 生成失败，拒绝规则模板降级：{exc}"
                    ) from exc
                logger.warning("ResourceAgent v2 LLM 调用失败，回退规则化: %s", exc)
                result = self._rule_based_resources_v2(
                    topic=topic,
                    resource_types=resource_types,
                    difficulty=difficulty,
                    profile=profile,
                    context=context,
                    stage_info=stage_info,
                    knowledge_context=knowledge_context,
                )
        else:
            # 3. 规则化兜底
            fallback_reason_code = "LLM_NOT_CONFIGURED"
            fallback_reason_detail = "LLM client is None"
            if RESOURCE_STRICT_MODE:
                raise RuntimeError("严格模式：ResourceAgent 未配置 LLM，拒绝规则模板降级")
            logger.info("ResourceAgent v2: 无 LLM，使用规则化资源生成")
            result = self._rule_based_resources_v2(
                topic=topic,
                resource_types=resource_types,
                difficulty=difficulty,
                profile=profile,
                context=context,
                stage_info=stage_info,
                knowledge_context=knowledge_context,
            )

        # 4. 后处理：校验 + 规范化 + 上下文注入
        valid_resources = []
        logger.info("ResourceAgent v2: LLM 输出 %d 个资源，开始校验", len(result.resources))
        for i, resource in enumerate(result.resources):
            try:
                # 类型化 Schema 校验
                validated_content = self._validate_by_type(resource.resource_type, resource.content)
                if hasattr(validated_content, "model_dump"):
                    resource.content = validated_content.model_dump()

                # 标题规范化
                resource.title = self._normalize_title(topic, resource.resource_type)

                # 注入上下文字段
                resource.course_id = context.course_id
                resource.stage_id = context.stage_id or ""
                resource.task_id = context.task_id or ""
                resource.user_id = context.user_id
                if not resource.knowledge_point_ids:
                    resource.knowledge_point_ids = list(context.knowledge_point_ids)

                # 重复检测（占位）
                resource.version = self._check_duplicate_version(
                    topic=topic,
                    resource_type=resource.resource_type,
                    course_id=context.course_id,
                )

                valid_resources.append(resource)
                logger.info("ResourceAgent v2: 资源[%d] 校验通过 type=%s title=%s", i, resource.resource_type, resource.title)
            except ResourceSchemaInvalid as e:
                logger.warning(
                    "ResourceAgent v2: 资源[%d] 校验失败 type=%s title=%s: %s",
                    i, resource.resource_type, resource.title, e,
                )
                continue
            except Exception as e:
                logger.warning(
                    "ResourceAgent v2: 资源[%d] 处理异常 type=%s: %s",
                    i, resource.resource_type, e,
                )
                continue

        if not valid_resources and result.resources:
            logger.error(
                "ResourceAgent v2: 所有 %d 个资源均校验失败，LLM 输出内容可能不符合 Schema",
                len(result.resources),
            )
            # 降级：使用规则化资源
            logger.info("ResourceAgent v2: 降级使用规则化资源")
            result = self._rule_based_resources_v2(
                topic=topic,
                resource_types=resource_types,
                difficulty=difficulty,
                profile=profile,
                context=context,
                stage_info=stage_info,
                knowledge_context=knowledge_context or "",
            )

        result.resources = valid_resources
        result.total = len(valid_resources)
        result.topic = topic
        result.difficulty = difficulty

        # 设置 generation_meta
        from datetime import datetime
        usage = self.llm.last_usage if self.llm else None
        result.generation_meta = GenerationMeta(
            agent_name=self.agent_name,
            provider=usage.provider if usage else ("spark" if fallback_reason_code is None else "fallback"),
            model=usage.model if usage else "unknown",
            run_id="",
            request_id="",
            duration_ms=usage.duration_ms if usage else 0,
            fallback_used=fallback_reason_code is not None,
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

        return result

    async def generate_spark_ppt_outline(
        self,
        *,
        context: AgentContext,
        topic: str,
        difficulty: str = "中级",
        profile: dict | None = None,
        stage_info: dict | None = None,
        knowledge_context: str | None = None,
    ) -> list[dict]:
        """生成星火 PPT API 兼容的大纲格式。

        Args:
            context: 统一 Agent 上下文
            topic: 知识点主题
            difficulty: 难度等级
            profile: 学生画像
            stage_info: 关卡信息
            knowledge_context: 知识库上下文

        Returns:
            星火 API 格式的大纲列表
        """
        profile = profile or {}
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)

        # 构建提示词
        lines = [
            f"知识点: {topic}",
            f"难度: {difficulty}",
            f"学生画像:\n{profile_json}",
        ]

        if stage_info and isinstance(stage_info, dict):
            stage_title = stage_info.get("title", "")
            if stage_title:
                lines.append(f"当前关卡: {stage_title}")
            objectives = stage_info.get("objectives", "")
            if objectives:
                lines.append(f"关卡目标: {objectives}")

        if knowledge_context:
            lines.append(f"\n知识库上下文:\n{knowledge_context}")

        lines.append(SPARK_PPT_OUTLINE_SCHEMA)
        lines.append(
            "\n请严格输出 JSON 格式，不要包含任何其他文字。"
        )

        user_prompt = "\n".join(lines)

        # 调用 LLM 生成大纲
        if self.llm:
            try:
                chunks = []
                async for chunk in self.call_llm(user_prompt):
                    chunks.append(chunk)
                raw = "".join(chunks)

                # 解析 JSON
                data = self._parse_outline_json(raw)
                if data and "outline" in data:
                    outline = data["outline"]
                    if isinstance(outline, list) and len(outline) > 0:
                        logger.info("LLM 生成 PPT 大纲成功: %d 个章节", len(outline))
                        return outline

                logger.warning("LLM 输出的大纲格式不正确，使用规则化大纲")
            except Exception as exc:
                logger.warning("LLM 生成 PPT 大纲失败: %s，使用规则化大纲", exc)

        # 规则化兜底
        return self._generate_rule_based_outline(topic, difficulty, stage_info)

    @staticmethod
    def _parse_outline_json(raw: str) -> dict | None:
        """解析 LLM 输出的 JSON 大纲"""
        text = raw.strip()

        # 移除代码块标记
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            if text.startswith("json"):
                text = text[4:].strip()

        # 提取 JSON 对象
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end >= start:
            text = text[start:end + 1]

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, TypeError):
            pass

        return None

    def _generate_rule_based_outline(
        self,
        topic: str,
        difficulty: str,
        stage_info: dict | None = None,
    ) -> list[dict]:
        """规则化生成 PPT 大纲（LLM 不可用时的兜底方案）"""
        diff_labels = {"初级": "入门", "中级": "进阶", "高级": "深入"}
        level = diff_labels.get(difficulty, "入门")

        # 关卡信息
        stage_title = ""
        if stage_info and isinstance(stage_info, dict):
            stage_title = stage_info.get("title", "")

        outline = [
            {
                "title": topic,
                "subtitles": [
                    {"title": "学习目标", "content": f"掌握{topic}的核心概念和基本应用"},
                    {"title": "难度等级", "content": f"本课件面向{level}阶段学习者"},
                ]
            },
            {
                "title": f"为什么需要{topic}",
                "subtitles": [
                    {"title": "现实痛点", "content": f"描述没有{topic}时会遇到的困难"},
                    {"title": "解决方案", "content": f"{topic}如何解决上述问题"},
                ]
            },
            {
                "title": f"{topic}的核心概念",
                "subtitles": [
                    {"title": "基本定义", "content": f"{topic}的标准定义和关键术语"},
                    {"title": "数学表达", "content": f"{topic}的数学公式和符号说明"},
                ]
            },
            {
                "title": f"{topic}的工作原理",
                "subtitles": [
                    {"title": "算法流程", "content": f"{topic}的核心算法步骤"},
                    {"title": "推导过程", "content": f"{topic}的关键推导"},
                ]
            },
            {
                "title": f"{topic}的代码实现",
                "subtitles": [
                    {"title": "Python 示例", "content": f"{topic}的完整代码实现"},
                    {"title": "关键代码解读", "content": "逐行解释核心逻辑"},
                ]
            },
            {
                "title": f"{topic}实例演示",
                "subtitles": [
                    {"title": "案例分析", "content": f"{topic}的实际应用案例"},
                    {"title": "效果对比", "content": "Before/After 效果对比"},
                ]
            },
            {
                "title": f"{topic}常见误区",
                "subtitles": [
                    {"title": "典型错误", "content": f"学习{topic}时的常见错误"},
                    {"title": "正确理解", "content": f"正确理解{topic}的关键点"},
                ]
            },
            {
                "title": f"{topic}小结",
                "subtitles": [
                    {"title": "核心要点", "content": f"回顾{topic}的3个关键 takeaway"},
                    {"title": "知识地图", "content": f"{topic}在整个知识体系中的位置"},
                    {"title": "课后任务", "content": "完成配套练习题，巩固所学知识"},
                ]
            },
        ]

        # 根据难度调整章节数量
        if difficulty == "初级":
            outline = outline[:6]
        elif difficulty == "高级":
            # 高级增加前沿发展章节
            outline.insert(-1, {
                "title": f"{topic}前沿发展",
                "subtitles": [
                    {"title": "最新研究", "content": f"{topic}领域的最新研究进展"},
                    {"title": "未来方向", "content": f"{topic}的未来发展趋势"},
                ]
            })

        return outline

    async def prepare_stage_resources(
        self,
        *,
        context: AgentContext,
        stage: dict,
        resource_blueprint: list[dict] | None = None,
    ) -> list[dict]:
        """根据已保存阶段生成可追踪的资源任务描述，不在前端伪造进度。"""
        blueprint = resource_blueprint or stage.get("resource_blueprint") or []
        if not blueprint:
            blueprint = [
                {
                    "resource_type": task.get("task_type") or task.get("type"),
                    "topic": task.get("title") or stage.get("title"),
                    "task_id": task.get("task_id"),
                }
                for task in stage.get("tasks") or []
                if (task.get("task_type") or task.get("type")) in {
                    "document",
                    "mindmap",
                    "exercise",
                    "code",
                    "ppt",
                    "interactive_classroom",
                }
            ]
        return [
            {
                "job_id": f"resource_job_{context.course_id}_{index}",
                "course_id": context.course_id,
                "stage_id": context.stage_id or stage.get("stage_id"),
                "task_id": item.get("task_id"),
                "resource_type": item.get("resource_type") or item.get("type") or "document",
                "topic": item.get("topic") or stage.get("title") or "",
                "status": "created",
            }
            for index, item in enumerate(blueprint, 1)
            if isinstance(item, dict)
        ]


# ── Helpers (module-level) ──────────────────────────────────

def _classify_error_code(exc: Exception) -> str:
    """Classify an exception into a fallback_reason_code."""
    msg = str(exc).lower()
    if isinstance(exc, RuntimeError):
        if "未配置" in str(exc) or "缺少" in str(exc) or "api key" in msg or "api_key" in msg:
            return "LLM_NOT_CONFIGURED"
        if "认证" in str(exc) or "auth" in msg or "unauthorized" in msg or "401" in msg:
            return "LLM_AUTH_FAILED"
    if isinstance(exc, (TimeoutError,)) or "timeout" in msg or "timed out" in msg:
        return "LLM_TIMEOUT"
    exc_name = type(exc).__name__
    if "HTTPError" in exc_name or "ConnectError" in exc_name or "provider" in msg:
        return "LLM_PROVIDER_ERROR"
    if "empty" in msg or "空" in str(exc):
        return "LLM_OUTPUT_EMPTY"
    if isinstance(exc, (json.JSONDecodeError,)) or "json" in msg or "parse" in msg:
        return "LLM_OUTPUT_INVALID_JSON"
    if "schema" in msg or "pydantic" in msg or "validation" in msg:
        return "RESOURCE_SCHEMA_INVALID"
    if "rag" in msg or "retrieval" in msg or "知识库" in str(exc):
        return "RAG_RETRIEVAL_FAILED"
    if "safety" in msg or "安全" in str(exc):
        return "SAFETY_CHECK_FAILED"
    return "UNKNOWN_GENERATION_ERROR"


def resource_output_to_service_dict(output: ResourceGenerationOutput) -> dict:
    """Convert v2 Pydantic output to the dict format ResourceService expects."""
    resources = []
    for r in output.resources:
        content = r.content
        if hasattr(content, "model_dump"):
            content = content.model_dump()
        resources.append({
            "type": r.resource_type,
            "title": r.title,
            "topic": r.topic,
            "difficulty": r.difficulty,
            "content": content,
            "summary": r.summary or "",
            "estimated_minutes": r.estimated_minutes or 20,
        })
    meta = {}
    if output.generation_meta:
        gm = output.generation_meta
        meta = {
            "agent_name": gm.agent_name or "ResourceAgent",
            "provider": gm.provider,
            "model": gm.model,
            "run_id": gm.run_id,
            "request_id": gm.request_id,
            "duration_ms": gm.duration_ms,
            "fallback_used": gm.fallback_used,
            "generated_at": gm.generated_at,
        }
    return {
        "resources": resources,
        "generation_meta": meta,
    }
