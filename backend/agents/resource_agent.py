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
        return (
            "你是学习资源生成智能体。\n"
            "根据知识点主题、学生画像和资源类型要求，生成个性化、多模态的学习资源。\n\n"
            "## 资源类型\n"
            "- document: 结构化 Markdown 讲解文档，含标题、定义、原理、示例。\n"
            "- mindmap: 嵌套 Markdown 列表（用 - 和缩进表示层级），前端用 markmap 渲染。\n"
            "- exercise: Markdown 格式练习题，用标题、列表、加粗等排版，每题含题目、选项、答案和解析。\n"
            "- code: 完整可运行的 Python 代码，用 Markdown 代码块（```python）包裹。\n"
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
            "content 字段为 Markdown 字符串（exercise 和 code 类型也使用 Markdown 格式排版）。"
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
            cognitive_hint = (
                "建议从生活场景或工程问题切入，用白话讲清楚「为什么需要这个概念」"
                if "图解" in cognitive else
                "建议从数学定义出发，先给出公式再逐项解释物理含义"
            )
            return (
                f"# {topic} 讲解文档（{level}）\n\n"
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
            return (
                f"# {topic} 练习题（{level}）\n\n"
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
            return (
                f"# {topic} — 代码示例（{level}）\n\n"
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
            slides = [
                f"Slide 1: 封面 —— {topic}（{level}）\n"
                f"  - 副标题：从原理到实践的系统讲解\n"
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
