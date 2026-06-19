"""
ResourceAgent —— 学习资源生成智能体

根据学习路径、学生画像和知识库，生成个性化多模态学习资源。

合同（对齐 docs/design.md §10.4.3）:
    主入口: generate_resources(topic, resource_types, difficulty, profile, knowledge_context)
    返回:   {"resources": [{"type", "title", "topic", "difficulty", "content"}, ...]}
"""
import json
import logging
from typing import Optional, List, Dict

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResourceAgent(BaseAgent):
    """根据学习路径生成个性化学习资源"""

    def __init__(self, llm_client=None):
        super().__init__(llm_client)

    # 各资源类型的详细 Prompt 模板
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
            "生成 JSON 格式练习题，要求：\n"
            "- 3-5 道题，覆盖概念理解、公式应用、场景判断\n"
            "- 每道题含 question/options/answer/explanation\n"
            "- 初级难度以单选和判断为主，中高级加入简答和代码补全\n"
            "- 正确答案需逻辑正确，干扰项需有迷惑性"
        ),
        "code": (
            "生成完整可运行的 Python 代码示例，要求：\n"
            "- 包含必要的 import 和 main 入口\n"
            "- 关键步骤用中文注释解释 WHY 而不仅仅是 WHAT\n"
            "- 如有多个实现方式，提供对比并标注适用场景\n"
            "- 代码风格遵循 PEP 8"
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
        return (
            "你是学习资源生成智能体。\n"
            "根据知识点主题、学生画像和资源类型要求，生成个性化、多模态的学习资源。\n\n"
            "## 资源类型\n"
            "- document: 结构化 Markdown 讲解文档，含标题、定义、原理、示例。\n"
            "- mindmap: 嵌套 Markdown 列表（用 - 和缩进表示层级），前端用 markmap 渲染。\n"
            "- exercise: JSON 格式练习题，每道题含 question / options / answer / explanation。\n"
            "- code: 完整可运行的 Python 代码 + 详细注释。\n"
            "- reading: 拓展阅读材料，含分级推荐文献、阅读顺序、拓展思考题。\n"
            "- ppt: 12-slide 讲稿大纲，每 slide 含标题、bullets、讲师备注。\n\n"
            "## 个性化要求\n"
            "- 初级: 多解释、多示例、避免术语堆砌。\n"
            "- 中级: 适当的公式和原理，配合实战练习。\n"
            "- 高级: 深入理论推导、性能优化、前沿扩展。\n"
            "- 视觉型学习者 (cognitive_style=图解/案例): 多给图示思路和案例。\n\n"
            "## 防幻觉约束\n"
            "1. 公式、定理务必核实，不编造——不确定的标注『建议核实』。\n"
            "2. 代码确保语法正确、逻辑合理、可直接运行。\n"
            "3. 练习题必须有正确答案——干扰项要有迷惑性但必须是错的，不能给模糊或双关的选项。\n"
            "4. 超出知识范围请诚实告知，不编造内容。\n"
            "5. 附带 sources 字段标注知识来源；无可靠来源时标注『建议核实』。\n"
            "6. 不生成违规、敏感或不安全的内容。\n\n"
            "## 输出格式\n"
            "严格输出 JSON: {\"resources\": [{type, title, topic, difficulty, content}, ...]}\n"
            "content 字段为 Markdown 字符串（exercise 类型为 JSON 字符串）。"
        )

    def _build_generate_prompt(
        self,
        topic: str,
        resource_types: list,
        difficulty: str,
        profile_json: str,
        context_text: str,
    ) -> str:
        """为 LLM 构建含类型详细要求的生成提示词"""
        lines = [
            f"知识点: {topic}",
            f"难度: {difficulty}",
            f"资源类型: {json.dumps(resource_types, ensure_ascii=False)}",
            f"学生画像:\n{profile_json}",
        ]
        if context_text:
            lines.append(f"知识库上下文:\n{context_text}")

        lines.append("\n## 各类型生成要求")
        for rtype in resource_types:
            detail = self.TYPE_PROMPTS.get(rtype, f"请生成 {rtype} 类型的资源。")
            lines.append(f"\n### {rtype}\n{detail}")

        lines.append(
            "\n请严格输出 JSON: {\"resources\": [{type, title, topic, difficulty, content}, ...]}"
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 主入口（合同方法）
    # ------------------------------------------------------------------
    async def generate_resources(
        self,
        topic: str,
        resource_types: Optional[List[str]] = None,
        difficulty: str = "中级",
        profile: Optional[dict] = None,
        knowledge_context: Optional[List[str]] = None,
    ) -> Dict:
        """
        生成学习资源。

        Args:
            topic: 知识点主题
            resource_types: 要生成的资源类型列表，默认 ["document"]
            difficulty: 难度等级（初级/中级/高级）
            profile: 学生画像
            knowledge_context: RAG 检索到的知识库上下文

        Returns:
            {"resources": [{"type", "title", "topic", "difficulty", "content"}, ...]}
        """
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

        return self._rule_based_resources(topic, resource_types, difficulty, profile)

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
    # 规则化兜底（无需 LLM）
    # ------------------------------------------------------------------
    def _rule_based_resources(
        self,
        topic: str,
        resource_types: List[str],
        difficulty: str,
        profile: dict,
    ) -> Dict:
        """开发期无 API Key 时使用的规则化资源生成"""
        resources = []
        profile_inner = profile.get("profile", profile)
        cognitive = profile_inner.get("cognitive_style", "")

        for rtype in resource_types:
            title_map = {
                "document": f"{topic} 讲解文档",
                "mindmap": f"{topic} 思维导图",
                "exercise": f"{topic} 练习题",
                "code": f"{topic} 代码案例",
                "reading": f"{topic} 拓展阅读",
                "ppt": f"{topic} PPT 大纲",
            }

            content = self._build_content(rtype, topic, difficulty, cognitive)
            resources.append({
                "type": rtype,
                "title": title_map.get(rtype, f"{topic} 学习资源"),
                "topic": topic,
                "difficulty": difficulty,
                "content": content,
            })

        return {"resources": resources}

    def _build_content(
        self, rtype: str, topic: str, difficulty: str, cognitive: str
    ) -> str:
        """为每种资源类型生成骨架内容"""
        diff_labels = {"初级": "入门", "中级": "进阶", "高级": "深入"}
        level = diff_labels.get(difficulty, "入门")

        if rtype == "document":
            return (
                f"# {topic} 讲解文档（{level}）\n\n"
                f"## 1. 概念定义\n\n"
                f"{topic} 是……（建议用一两句话概括核心概念）\n\n"
                f"## 2. 核心原理\n\n"
                f"（此处展开原理说明，配合{'生活类比' if '图解' in cognitive else '公式推导'}）\n\n"
                f"## 3. 示例说明\n\n"
                f"（给出 1-2 个具体示例帮助理解）\n\n"
                f"## 4. 关键要点\n\n"
                f"- 要点1\n- 要点2\n- 要点3\n\n"
                f"## 5. 参考来源\n\n"
                f"> 建议核实: 本内容基于通用知识生成，具体公式请查阅教材。\n"
            )
        elif rtype == "mindmap":
            return (
                f"- {topic}\n"
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
            questions = [
                {
                    "question": f"关于{topic}，以下说法正确的是？（单选）",
                    "options": {
                        "A": f"{topic}是AI领域的基础概念之一",
                        "B": f"{topic}完全不实用",
                        "C": f"学习{topic}不需要任何前置知识",
                        "D": "以上都不对",
                    },
                    "answer": "A",
                    "explanation": f"{topic}是重要基础概念，学习前建议具备相关前置知识。",
                },
                {
                    "question": f"请简述{topic}的核心思想。（简答）",
                    "options": {},
                    "answer": "（开放式答案，围绕核心概念展开）",
                    "explanation": "重点考察对核心原理的理解深度。",
                },
                {
                    "question": f"{topic}在实际项目中如何应用？请举例说明。（简答）",
                    "options": {},
                    "answer": "（结合实际场景作答）",
                    "explanation": "考察理论联系实际的能力。",
                },
            ]
            return json.dumps(questions, ensure_ascii=False, indent=2)
        elif rtype == "code":
            return (
                f'"""\n'
                f'{topic} — 代码示例（{level}）\n'
                f'本代码演示 {topic} 的核心实现思路\n'
                f'"""\n\n'
                f'import numpy as np\n\n'
                f'# TODO: 实现 {topic} 的核心逻辑\n'
                f'def demo_{topic.lower().replace(" ", "_")}():\n'
                f'    """{topic} 示例函数"""\n'
                f'    print("开始演示 {topic}")\n'
                f'    # 1. 数据准备\n'
                f'    # 2. 核心计算\n'
                f'    # 3. 结果输出\n'
                f'    return None\n\n'
                f'if __name__ == "__main__":\n'
                f'    demo_{topic.lower().replace(" ", "_")}()\n'
            )
        elif rtype == "reading":
            return (
                f"# {topic} 拓展阅读\n\n"
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
            slides = []
            slides.append(f"Slide 1: 封面 — {topic}（{level}）")
            slides.append(f"Slide 2: 学习目标 — 学完本节你将掌握…")
            slides.append(f"Slide 3: 概念导入 — 从生活中的例子引出{topic}")
            slides.append(f"Slide 4: 核心定义 — {topic}的数学定义与公式")
            slides.append(f"Slide 5: 工作原理 — 图解/流程图展示核心机制")
            slides.append(f"Slide 6: 代码示例 — 关键代码片段演示")
            slides.append(f"Slide 7: 常见误区 — 3 个典型易错点")
            slides.append(f"Slide 8: 小结与练习 — 回顾要点 + 课后练习")
            return "\n".join(slides)
        else:
            return f"# {topic} 学习资源\n\n（内容待生成）\n"
