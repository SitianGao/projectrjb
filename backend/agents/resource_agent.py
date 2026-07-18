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
            "生成 Markdown 格式练习题，要求：\n"
            "- 3-5 道题，覆盖概念理解、公式应用、场景判断\n"
            "- 使用 Markdown 标题（### 题目 N）、列表、加粗等排版\n"
            "- 每题包含：题目描述、选项（A/B/C/D）、正确答案、详细解析\n"
            "- 初级难度以单选和判断为主，中高级加入简答和代码补全\n"
            "- 正确答案需逻辑正确并用 **加粗** 标注，干扰项需有迷惑性\n"
            "- 用 --- 分隔各题"
        ),
        "code": (
            "生成完整可运行的 Python 代码示例，用 Markdown 代码块（```python...```）包裹，要求：\n"
            "- 包含必要的 import 和 main 入口\n"
            "- 关键步骤用中文注释解释 WHY 而不仅仅是 WHAT\n"
            "- 如有多个实现方式，提供对比并标注适用场景\n"
            "- 代码风格遵循 PEP 8\n"
            "- 代码块前后可加简短说明文字"
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
            detail = self.TYPE_PROMPTS.get(rtype, f"请生成 {rtype} 类型的资源。")
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
            "\n请严格输出 JSON: {\"resources\": [{type, title, topic, difficulty, content}, ...]}"
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
                    return result
            except Exception as exc:
                logger.warning("ResourceAgent LLM 调用失败，回退规则化: %s", exc)

        return self._rule_based_resources(topic, resource_types, difficulty, profile, stage_info)

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
            normalized.append({
                "type": item.get("type", resource_types[0] if resource_types else "document"),
                "title": item.get("title", f"{topic} 学习资源"),
                "topic": item.get("topic", topic),
                "difficulty": item.get("difficulty", difficulty),
                "content": item.get("content", ""),
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
    ) -> Dict:
        """开发期无 API Key 时使用的规则化资源生成（v2: 关卡感知）"""
        resources = []
        profile_inner = profile.get("profile", profile)
        cognitive = profile_inner.get("cognitive_style", "")

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

            content = self._build_content(rtype, topic, difficulty, cognitive, stage_info)
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
    ) -> str:
        """为每种资源类型生成骨架内容（v2: 关卡感知）"""
        diff_labels = {"初级": "入门", "中级": "进阶", "高级": "深入"}
        level = diff_labels.get(difficulty, "入门")

        # 构建关卡背景块（统一注入到各资源类型开头）
        stage_context = self._build_stage_context_markdown(stage_info)

        if rtype == "document":
            cognitive_hint = (
                "建议从生活场景或工程问题切入，用白话讲清楚「为什么需要这个概念」"
                if "图解" in cognitive else
                "建议从数学定义出发，先给出公式再逐项解释物理含义"
            )
            return (
                f"# {topic} 讲解文档（{level}）\n\n"
                f"{stage_context}"
                f"## 1. 概念导入\n\n"
                f"{topic} 是{level}阶段的核心知识点。{cognitive_hint}。\n\n"
                f"## 2. 概念定义\n\n"
                f"{topic} 指……（请结合教材中的标准定义理解）。\n"
                f"其核心思想是建立一个从输入到输出的映射关系，通过数据驱动的方式学习规律。\n\n"
                f"## 3. 核心原理\n\n"
                f"### 3.1 基本思路\n"
                f"从给定数据出发，通过优化目标函数来确定模型参数。\n\n"
                f"### 3.2 关键步骤\n"
                f"1. 数据准备：收集、清洗并划分训练集与测试集\n"
                f"2. 模型选择：根据问题类型选择合适的模型结构\n"
                f"3. 训练优化：使用优化算法最小化损失函数\n"
                f"4. 评估验证：在测试集上评估模型性能\n\n"
                f"## 4. 示例说明\n\n"
                f"以实际场景为例：假设我们要预测房价，可以将面积、地段、房龄作为输入特征，\n"
                f"房价作为输出。通过{topic}构建从特征到价格的映射，实现对新房源的价格预估。\n\n"
                f"## 5. 关键要点\n\n"
                f"- 核心理解：掌握算法的基本思想和适用场景\n"
                f"- 常见误区：不要忽略数据预处理步骤，垃圾进则垃圾出\n"
                f"- 实践建议：先跑通简单示例，再逐步增加数据量和特征维度\n\n"
                f"## 6. 参考来源\n\n"
                f"> **建议核实**: 本内容基于通用知识体系生成，具体公式推导、超参数选择请以课程指定教材为准。\n"
                f"> 标注「建议核实」的内容建议对照教材确认后使用。\n"
            )
        elif rtype == "mindmap":
            # 关卡感知的思维导图：当有 stage_info 时，围绕关卡知识点展开
            stage_topics_bullets = ""
            if stage_info and isinstance(stage_info, dict):
                stage_topics_list = stage_info.get("topics") or []
                if stage_topics_list:
                    stage_topics_bullets = "  - 关卡知识点\n" + "".join(
                        f"    - {t}\n" for t in stage_topics_list
                    )
            return (
                f"{stage_context}"
                f"- {topic}\n"
                f"{stage_topics_bullets}"
                f"  - 概念定义\n"
                f"    - 核心术语\n"
                f"    - 公式表达\n"
                f"  - 工作原理\n"
                f"    - 输入\n"
                f"    - 处理过程\n"
                f"    - 输出\n"
                f"  - 应用场景\n"
                f"    - 场景A\n"
                f"    - 场景B\n"
                f"  - 常见问题\n"
                f"    - 误区1\n"
                f"    - 误区2\n"
            )
        elif rtype == "exercise":
            # 关卡感知的练习题：将关卡任务转化为具体题目
            tasks_questions = ""
            if stage_info and isinstance(stage_info, dict):
                stage_tasks = stage_info.get("tasks") or []
                if stage_tasks:
                    tasks_questions = "### 关卡任务练习\n\n"
                    for i, t in enumerate(stage_tasks, 1):
                        task_desc = t.get("task", "") if isinstance(t, dict) else str(t)
                        resource_hint = t.get("resource_type", "") if isinstance(t, dict) else ""
                        hint_note = f"（推荐资源类型: {resource_hint}）" if resource_hint else ""
                        tasks_questions += (
                            f"**关卡任务 {i}**：{task_desc} {hint_note}\n\n"
                            f"> **📝 练习要求**：请根据上述任务描述完成练习。\n\n"
                        )
                    tasks_questions += "---\n\n"
            return (
                f"# {topic} 练习题（{level}）\n\n"
                f"{stage_context}"
                f"{tasks_questions}"
                f"### 题目 1（单选）\n\n"
                f"关于 {topic}，以下说法正确的是？\n\n"
                f"A. {topic} 是 AI 领域的基础概念之一\n\n"
                f"B. {topic} 完全不实用\n\n"
                f"C. 学习 {topic} 不需要任何前置知识\n\n"
                f"D. 以上都不对\n\n"
                f"> **✅ 正确答案：A**\n>\n"
                f"> **📖 解析：** {topic} 是重要基础概念，学习前建议具备相关前置知识。B 过于绝对，C 不符合实际。\n\n"
                f"---\n\n"
                f"### 题目 2（简答）\n\n"
                f"请简述 {topic} 的核心思想。\n\n"
                f"> **📝 参考答案：** （围绕核心概念展开，重点考察对核心原理的理解深度）\n\n"
                f"---\n\n"
                f"### 题目 3（应用）\n\n"
                f"{topic} 在实际项目中如何应用？请举例说明。\n\n"
                f"> **📝 参考答案：** （结合实际场景作答，考察理论联系实际的能力）\n"
            )
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
            return (
                f"# {topic} — 代码示例（{level}）\n\n"
                f"{stage_context}"
                f"{task_scenario}"
                f"本代码演示 {topic} 的典型实现方式，包含数据准备、模型构建、训练和评估四个阶段。\n\n"
                f"```python\n"
                f'"""\n'
                f'{topic} — 代码示例（{level}）\n'
                f'本代码演示 {topic} 的典型实现方式，包含数据准备、模型构建、训练和评估四个阶段。\n'
                f'"""\n\n'
                f'import numpy as np\n\n'
                f'\n'
                f'# ============================================================================\n'
                f'# 步骤 1：生成示例数据\n'
                f'# ============================================================================\n'
                f'np.random.seed(42)\n'
                f'n_samples = 100\n'
                f'n_features = 5\n'
                f'X = np.random.randn(n_samples, n_features)  # 特征矩阵\n'
                f'y = X[:, 0] * 2.5 + X[:, 1] * (-1.3) + np.random.randn(n_samples) * 0.1  # 目标变量\n'
                f'print(f"数据形状: X={{X.shape}}, y={{y.shape}}")\n'
                f'\n'
                f'\n'
                f'# ============================================================================\n'
                f'# 步骤 2：实现 {topic} 核心算法\n'
                f'# ============================================================================\n'
                f'def {func_name}(X, y, learning_rate=0.01, n_iters=1000):\n'
                f'    """{topic} 的核心实现\n'
                f'    \n'
                f'    参数:\n'
                f'        X: 特征矩阵 (n_samples, n_features)\n'
                f'        y: 目标变量 (n_samples,)\n'
                f'        learning_rate: 学习率，控制每步更新幅度\n'
                f'        n_iters: 最大迭代次数\n'
                f'    返回:\n'
                f'        weights: 模型权重 (n_features,)\n'
                f'    """\n'
                f'    n_samples, n_features = X.shape\n'
                f'    weights = np.zeros(n_features)  # 初始化权重为零\n'
                f'    \n'
                f'    for i in range(n_iters):\n'
                f'        # 正向计算：预测值\n'
                f'        y_pred = X @ weights  # 矩阵乘法 (n_samples, n_features) @ (n_features,) = (n_samples,)\n'
                f'        \n'
                f'        # 计算损失：均方误差 (MSE)\n'
                f'        loss = np.mean((y_pred - y) ** 2)\n'
                f'        \n'
                f'        # 反向计算：梯度\n'
                f'        gradient = (2 / n_samples) * X.T @ (y_pred - y)\n'
                f'        \n'
                f'        # 参数更新：沿负梯度方向\n'
                f'        weights -= learning_rate * gradient\n'
                f'        \n'
                f'        # 每 200 轮打印一次训练进度\n'
                f'        if i % 200 == 0:\n'
                f'            print(f"迭代 {{i:4d}}: loss={{loss:.6f}}")\n'
                f'    \n'
                f'    return weights\n'
                f'\n'
                f'\n'
                f'# ============================================================================\n'
                f'# 步骤 3：训练与评估\n'
                f'# ============================================================================\n'
                f'if __name__ == "__main__":\n'
                f'    print(f"开始演示: {topic}（{level}级别）")\n'
                f'    \n'
                f'    # 训练模型\n'
                f'    learned_weights = {func_name}(X, y, learning_rate=0.01, n_iters=1000)\n'
                f'    \n'
                f'    # 评估模型\n'
                f'    y_final_pred = X @ learned_weights\n'
                f'    final_mse = np.mean((y_final_pred - y) ** 2)\n'
                f'    print(f"\\n训练完成！最终 MSE: {{final_mse:.6f}}")\n'
                f'    print(f"学习到的权重: {{np.round(learned_weights, 4)}}")\n'
                f'```\n'
            )
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
    ) -> ResourceGenerationOutput:
        """生成学习资源（v2：Pydantic 结构化输出 + 类型校验）。

        Args:
            context: 统一 Agent 上下文（包含 course_id, user_id, stage_id, task_id）
            topic: 知识点主题
            resource_types: 要生成的资源类型列表，默认 ["document"]
            difficulty: 难度等级（初级/中级/高级）
            profile: 学生画像
            stage_info: 当前关卡信息（可选）

        Returns:
            ResourceGenerationOutput: Pydantic 校验后的结构化资源列表
        """
        resource_types = resource_types or ["document"]
        profile = profile or {}
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)

        # 1. 检索知识库上下文
        try:
            knowledge_context = knowledge_service.search_context(context.course_id, topic)
        except Exception as exc:
            logger.warning("ResourceAgent: 知识库检索失败，继续生成: %s", exc)
            knowledge_context = "（资料库中未找到可靠依据）"

        # 2. LLM 路径
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
        for resource in result.resources:
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
            except ResourceSchemaInvalid as e:
                logger.warning(
                    "ResourceAgent v2: 资源校验失败 type=%s title=%s: %s",
                    resource.resource_type, resource.title, e,
                )
                continue

        result.resources = valid_resources
        result.total = len(valid_resources)
        result.topic = topic
        result.difficulty = difficulty

        return result
