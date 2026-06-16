"""
ResourceAgent —— 学习资源生成智能体

根据学习路径、学生画像和知识库，生成个性化多模态学习资源。

输出结构（对齐 docs/design.md §10.4.3）:
    resources: list[dict]
        type: str        — document | mindmap | exercise | code | reading | ppt
        title: str       — 资源标题
        topic: str       — 知识点主题
        difficulty: str  — 初级 | 中级 | 高级
        content: str     — Markdown / JSON / 代码内容
"""
import json
from typing import Optional, List, Dict

from .base_agent import BaseAgent


class ResourceAgent(BaseAgent):
    """根据学习路径生成个性化学习资源"""

    def __init__(self, llm_client=None):
        super().__init__(llm_client)

    def get_system_prompt(self) -> str:
        return (
            "你是学习资源生成智能体。\n"
            "根据知识点主题、学生画像和资源类型要求，生成个性化、多模态的学习资源。\n\n"
            "## 资源类型\n"
            "- document: 结构化 Markdown 讲解文档，含标题、定义、原理、示例。\n"
            "- mindmap: 嵌套 Markdown 列表（用 - 和缩进表示层级），前端用 markmap 渲染。\n"
            "- exercise: JSON 格式练习题，每道题含 question / options / answer / explanation。\n"
            "- code: 完整可运行的 Python 代码 + 详细注释。\n"
            "- reading: 拓展阅读材料，含要点摘要和推荐理由。\n"
            "- ppt: PPT 大纲，按 slide 组织，每 slide 含 title + bullets。\n\n"
            "## 个性化要求\n"
            "- 初级: 多解释、多示例、避免术语堆砌。\n"
            "- 中级: 适当的公式和原理，配合实战练习。\n"
            "- 高级: 深入理论推导、性能优化、前沿扩展。\n"
            "- 视觉型学习者 (cognitive_style=图解/案例): 多给图示思路和案例。\n\n"
            "## 防幻觉约束\n"
            "- 公式、定理务必核实，不编造。\n"
            "- 代码确保语法正确、逻辑合理。\n"
            "- 不确定内容标注『建议核实』。\n"
            "- 附带 sources 字段标注知识来源。\n\n"
            "## 输出格式\n"
            "严格输出 JSON: {\"resources\": [{type, title, topic, difficulty, content}, ...]}"
        )

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    async def generate_resources(
        self,
        topic: str,
        resource_types: Optional[List[str]] = None,
        difficulty: str = "中级",
        profile: Optional[dict] = None,
        knowledge_context: Optional[List[str]] = None,
    ) -> str:
        """
        生成学习资源 JSON。

        Args:
            topic: 知识点主题
            resource_types: 要生成的资源类型列表
            difficulty: 难度等级（初级/中级/高级）
            profile: 学生画像
            knowledge_context: RAG 检索到的知识库上下文
        Returns:
            JSON 字符串，含 resources 数组
        """
        resource_types = resource_types or ["document"]
        profile_json = json.dumps(profile or {}, ensure_ascii=False, indent=2)
        context_text = "\n".join(knowledge_context or [])
        user_prompt = (
            f"知识点: {topic}\n"
            f"难度: {difficulty}\n"
            f"资源类型: {json.dumps(resource_types, ensure_ascii=False)}\n"
            f"学生画像:\n{profile_json}\n\n"
            + (f"知识库上下文:\n{context_text}\n\n" if context_text else "")
            + "请生成对应类型的个性化学习资源。"
        )

        if self.llm:
            try:
                chunks = []
                async for chunk in self.call_llm(user_prompt):
                    chunks.append(chunk)
                return "".join(chunks)
            except Exception:
                pass

        return self._rule_based_resources(topic, resource_types, difficulty, profile or {})

    # ------------------------------------------------------------------
    # 规则化兜底（无需 LLM）
    # ------------------------------------------------------------------
    def _rule_based_resources(
        self,
        topic: str,
        resource_types: List[str],
        difficulty: str,
        profile: dict,
    ) -> str:
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

        return json.dumps({"resources": resources}, ensure_ascii=False, indent=2)

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
