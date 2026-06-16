
"""
ResourceAgent v01 —— 基于 LLM 的个性化学习资源生成智能体

职责：
- 根据主题、类型、难度和学生画像生成学习资源
- 支持 5 种资源类型：document / exercise / code / mindmap / reading
- DAY6 核心交付：document、exercise、code 三类
- 提供非流式 generate() 供编排器使用
- 提供流式 generate_stream() 供 SSE 端点使用

设计依据：docs/design.md §10.4.3 + docs/test_plan.md §3.3 (TC-R01~TC-R09)
"""
import json
import re
from typing import AsyncIterator, Optional, List, Dict

from .base_agent import BaseAgent


class ResourceAgent(BaseAgent):
    """个性化学习资源生成智能体 —— LLM prompt v01"""

    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.name = "ResourceAgent"

    # ---- 资源类型定义 ----
    RESOURCE_TYPES = ["document", "exercise", "code", "mindmap", "reading"]
    DIFFICULTY_LEVELS = ["初级", "中级", "高级"]

    def get_system_prompt(self) -> str:
        """
        v01 prompt：指导 LLM 生成结构化学习资源

        核心要点：
        - 根据 topic、type、difficulty 生成对应资源
        - 输出严格 JSON，保证下游 API 可解析
        - 内容准确、有教育价值，不确定处标注「建议核实」
        - 适配学生画像中的知识水平和学习风格
        """
        return (
            "你是一个个性化学习资源生成智能体，专门为大学生的学习需求生成高质量学习资源。\n"
            "\n"
            "## 你的任务\n"
            "根据学生指定的主题和资源类型，生成符合难度要求的个性化学习资源。\n"
            "\n"
            "## 可生成的资源类型\n"
            "\n"
            "1. **document（课程文档/讲义）**\n"
            "   - 结构化 Markdown 文档，含多级标题（##、###）\n"
            "   - 包含：概念讲解 -> 核心原理 -> 应用场景 -> 小结\n"
            "   - 适合系统学习，长度 500~1500 字\n"
            "\n"
            "2. **exercise（练习题）**\n"
            "   - 生成 3~5 道练习题\n"
            "   - 题型：选择题（4 选项）+ 简答题\n"
            "   - 每题包含：题干、选项（选择题）、正确答案、详细解析\n"
            "   - 难度分级：初级（概念记忆）、中级（理解应用）、高级（综合分析）\n"
            "\n"
            "3. **code（代码案例）**\n"
            "   - 完整可运行的 Python 代码\n"
            "   - 包含：导入语句 -> 核心实现 -> 注释说明 -> 运行示例输出\n"
            "   - 代码需有充分的中文注释，解释关键步骤\n"
            "   - 长度 20~80 行\n"
            "\n"
            "4. **mindmap（思维导图）**\n"
            "   - 嵌套 Markdown 无序列表（用 - 缩进表示层级）\n"
            "   - 根节点为知识点主题，逐层展开子概念\n"
            "   - 前端将用 markmap 渲染为可视化思维导图\n"
            "\n"
            "5. **reading（拓展阅读）**\n"
            "   - 推荐阅读材料列表\n"
            "   - 每条包含：材料标题、来源、简要说明、适合什么阶段阅读\n"
            "   - 注明可参考的经典教材/论文/在线课程\n"
            "\n"
            "## 难度控制\n"
            "- **初级**：适合零基础或入门学习者，多用类比和生活化例子，避免复杂公式\n"
            "- **中级**：适合有一定基础的学习者，包含核心公式推导和实际应用\n"
            "- **高级**：适合进阶学习者，深入理论细节、前沿进展和优化技巧\n"
            "\n"
            "## 输出格式（严格 JSON）\n"
            "你必须只输出一个 JSON 对象，不要包含任何其他文字。格式如下：\n"
            "```json\n"
            "{\n"
            '  "resources": [\n'
            "    {\n"
            '      "type": "document|exercise|code|mindmap|reading",\n'
            '      "title": "资源标题",\n'
            '      "topic": "所属知识点",\n'
            '      "difficulty": "初级|中级|高级",\n'
            '      "content": "Markdown 正文内容"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "```\n"
            "\n"
            "## 内容质量要求\n"
            "- 知识点准确，公式和定理务必核实\n"
            "- 不确定的内容请标注「建议核实」\n"
            "- 代码示例要能实际运行，不包含占位符或伪代码\n"
            "- 练习题答案必须正确，解析要讲清楚为什么\n"
            "- 内容要与学生的知识水平和学习风格匹配\n"
            "\n"
            "## 学生画像适配\n"
            "如果提供了学生画像（student_profile），请参考：\n"
            "- knowledge_level：调整内容深度和前置知识假设\n"
            "- cognitive_style：视觉型多配图说明，动手型多代码示例，理论型多公式推导\n"
            "- weakness：在相关内容中给予更多解释和练习\n"
            "- interest：结合兴趣方向举例，提升学习动力\n"
        )

    # ---- 非流式：供编排器 pipeline 使用 ----

    async def generate(
        self,
        topic: str,
        types: Optional[List[str]] = None,
        difficulty: str = "中级",
        student_profile: Optional[Dict] = None,
        count: int = 3,
    ) -> Dict:
        """
        生成学习资源（非流式，返回完整 dict）。

        Args:
            topic: 学习主题，如"线性回归"
            types: 资源类型列表，如 ["document", "exercise", "code"]
            difficulty: 难度等级，"初级" / "中级" / "高级"
            student_profile: 学生画像 dict（可选，用于个性化）
            count: 每种类型生成的资源数量（默认 3）

        Returns:
            dict: {
                "topic": str,
                "difficulty": str,
                "resources": [
                    {
                        "type": str,
                        "title": str,
                        "topic": str,
                        "difficulty": str,
                        "content": str
                    },
                    ...
                ],
                "generated_at": str (ISO 8601)
            }
        """
        if not types:
            types = ["document", "exercise", "code"]
        types = [t for t in types if t in self.RESOURCE_TYPES]
        if not types:
            types = ["document", "exercise", "code"]

        if difficulty not in self.DIFFICULTY_LEVELS:
            difficulty = "中级"

        user_prompt = self._build_generate_prompt(topic, types, difficulty, student_profile, count)

        try:
            full_response = []
            async for chunk in self.call_llm(user_prompt):
                full_response.append(chunk)
            raw = "".join(full_response)
            parsed = self._parse_llm_json(raw)
            if parsed:
                resources = parsed.get("resources", [])
                resources = self._normalize_resources(resources, topic, difficulty)
                return {
                    "topic": topic,
                    "difficulty": difficulty,
                    "resources": resources,
                    "generated_at": self._now_iso(),
                }
        except Exception:
            pass

        return self._template_fallback(topic, types, difficulty)

    # ---- 流式：供 /api/resource/generate SSE 端点使用 ----

    async def generate_stream(
        self,
        topic: str,
        types: Optional[List[str]] = None,
        difficulty: str = "中级",
        student_profile: Optional[Dict] = None,
        count: int = 3,
    ) -> AsyncIterator[str]:
        """
        生成学习资源（流式，SSE 事件）。

        产出 SSE 事件：
        - data: {"type":"start","message":"..."}
        - data: {"type":"delta","content":"..."}
        - data: {"type":"progress","progress":0.5,"message":"..."}
        - data: {"type":"data","data":{...resources...}}
        - data: {"type":"done"}
        """
        if not types:
            types = ["document", "exercise", "code"]
        types = [t for t in types if t in self.RESOURCE_TYPES]
        if not types:
            types = ["document", "exercise", "code"]

        if difficulty not in self.DIFFICULTY_LEVELS:
            difficulty = "中级"

        type_labels = {
            "document": "课程文档", "exercise": "练习题", "code": "代码案例",
            "mindmap": "思维导图", "reading": "拓展阅读",
        }
        type_names = "、".join(type_labels.get(t, t) for t in types)
        yield f'data: {{"type":"start","message":"开始生成{topic}的{type_names}资源（{difficulty}）"}}\n\n'

        user_prompt = self._build_generate_prompt(topic, types, difficulty, student_profile, count)

        full_response = []
        try:
            async for chunk in self.call_llm(user_prompt):
                full_response.append(chunk)
            raw = "".join(full_response)
            parsed = self._parse_llm_json(raw)

            if parsed:
                resources = parsed.get("resources", [])
                resources = self._normalize_resources(resources, topic, difficulty)
                result = {
                    "topic": topic,
                    "difficulty": difficulty,
                    "resources": resources,
                    "generated_at": self._now_iso(),
                }
                yield f'data: {{"type":"progress","progress":0.8,"message":"资源生成完成，正在整理结果"}}\n\n'
                data_json = json.dumps(result, ensure_ascii=False)
                yield f'data: {{"type":"data","data":{data_json}}}\n\n'
            else:
                result = self._template_fallback(topic, types, difficulty)
                data_json = json.dumps(result, ensure_ascii=False)
                yield f'data: {{"type":"error","code":"RESOURCE_GENERATE_FAILED","sub_code":"PARSE_ERROR","message":"LLM 返回内容无法解析，已使用模板降级"}}\n\n'
                yield f'data: {{"type":"data","data":{data_json}}}\n\n'
        except Exception as e:
            result = self._template_fallback(topic, types, difficulty)
            data_json = json.dumps(result, ensure_ascii=False)
            yield f'data: {{"type":"error","code":"RESOURCE_GENERATE_FAILED","sub_code":"LLM_ERROR","message":"模型调用失败，已使用模板降级: {str(e)}"}}\n\n'
            yield f'data: {{"type":"data","data":{data_json}}}\n\n'

        yield f'data: {{"type":"done"}}\n\n'

    # ---- 内部工具方法 ----

    def _build_generate_prompt(
        self,
        topic: str,
        types: List[str],
        difficulty: str,
        student_profile: Optional[Dict],
        count: int,
    ) -> str:
        """构造发给 LLM 的 user prompt"""
        parts = []

        parts.append(f"## 资源生成请求")
        parts.append(f"- 主题：{topic}")
        parts.append(f"- 资源类型：{', '.join(types)}（每种类型生成 {count} 个）")
        parts.append(f"- 难度等级：{difficulty}")

        if student_profile:
            parts.append("\n## 学生画像（供个性化适配）")
            profile = student_profile.get("profile", student_profile)
            parts.append("```json")
            parts.append(json.dumps(profile, ensure_ascii=False, indent=2))
            parts.append("```")

            hints = []
            kl = profile.get("knowledge_level", "")
            if kl:
                hints.append(f"- 学生当前水平：{kl}")
            cs = profile.get("cognitive_style", "")
            if cs:
                hints.append(f"- 偏好的学习方式：{cs}")
            wk = profile.get("weakness") or []
            if wk:
                hints.append(f"- 薄弱环节：{', '.join(wk)}")
            it = profile.get("interest") or []
            if it:
                hints.append(f"- 兴趣方向：{', '.join(it)}")
            if hints:
                parts.append("\n请根据以上信息调整内容：")
                parts.extend(hints)

        parts.append(f"\n请为每种类型生成 {count} 个{difficulty}难度的资源，只输出 JSON。")
        return "\n".join(parts)

    def _parse_llm_json(self, text: str) -> Optional[Dict]:
        """
        从 LLM 输出中提取 JSON 对象。
        """
        if not text or not text.strip():
            return None

        text = text.strip()

        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            text = m.group(1).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        text = text[start:end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                cleaned = re.sub(r",\s*([}\]])", r"\1", text)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None

    def _normalize_resources(
        self,
        resources: List[Dict],
        topic: str,
        difficulty: str,
    ) -> List[Dict]:
        """规范化资源列表，补全缺失字段"""
        normalized = []
        for r in resources:
            if not isinstance(r, dict):
                continue
            res_type = r.get("type", "document")
            if res_type not in self.RESOURCE_TYPES:
                res_type = "document"

            normalized.append({
                "type": res_type,
                "title": r.get("title", f"{topic} 学习资源"),
                "topic": r.get("topic", topic),
                "difficulty": r.get("difficulty", difficulty),
                "content": r.get("content", ""),
            })
        return normalized

    def _template_fallback(
        self,
        topic: str,
        types: List[str],
        difficulty: str,
    ) -> Dict:
        """模板降级方案 —— LLM 不可用时的兜底逻辑"""
        resources = []
        for res_type in types:
            if res_type == "document":
                resources.append({
                    "type": "document",
                    "title": f"{topic} 入门指南",
                    "topic": topic,
                    "difficulty": difficulty,
                    "content": (
                        f"## {topic} 入门指南\n\n"
                        f"### 1. 概念概述\n\n"
                        f"{topic}是机器学习/深度学习领域的重要概念。"
                        f"本指南将帮助你从零开始理解其核心思想。\n\n"
                        f"### 2. 核心原理\n\n"
                        f"（建议核实）{topic}的核心思想是通过数学模型对数据进行分析和预测。"
                        f"建议配合实际代码示例加深理解。\n\n"
                        f"### 3. 应用场景\n\n"
                        f"- 数据分析与预测\n"
                        f"- 模式识别\n"
                        f"- 自动化决策\n\n"
                        f"### 4. 小结\n\n"
                        f"掌握{topic}需要理论与实践相结合，建议先理解基本概念，"
                        f"再通过代码练习巩固。\n\n"
                        f"> ⚠️ 此内容为模板降级生成，建议在 AI 服务恢复后重新生成以获得更高质量内容。"
                    ),
                })
            elif res_type == "exercise":
                resources.append({
                    "type": "exercise",
                    "title": f"{topic} 基础练习",
                    "topic": topic,
                    "difficulty": difficulty,
                    "content": (
                        f"# {topic} 基础练习\n\n"
                        f"### 选择题\n\n"
                        f"**1. 以下关于{topic}的描述，正确的是？**\n\n"
                        f"A. {topic}只适用于分类任务\n"
                        f"B. {topic}可以用于回归和分类等多种任务\n"
                        f"C. {topic}不需要数据即可训练\n"
                        f"D. {topic}的结果总是100%准确\n\n"
                        f"**正确答案：B**\n"
                        f"**解析：**{topic}是一种通用的机器学习方法，"
                        f"可以应用于回归、分类等多种任务场景。"
                        f"具体适用范围取决于算法设计和数据特征。\n\n"
                        f"### 简答题\n\n"
                        f"**2. 请简述{topic}的基本原理。**\n\n"
                        f"**参考答案：**（建议核实）{topic}通过构建数学模型"
                        f"来拟合训练数据，并使用优化算法最小化预测误差，"
                        f"从而得到对未知数据的预测能力。\n\n"
                        f"> ⚠️ 此内容为模板降级生成，建议在 AI 服务恢复后重新生成以获得更高质量内容。"
                    ),
                })
            elif res_type == "code":
                resources.append({
                    "type": "code",
                    "title": f"{topic} Python 示例",
                    "topic": topic,
                    "difficulty": difficulty,
                    "content": (
                        f"# {topic} Python 示例\n\n"
                        f"```python\n"
                        f"# -*- coding: utf-8 -*-\n"
                        f'"""\n'
                        f"{topic} 基础示例\n"
                        f"此代码演示了 {topic} 的基本用法\n"
                        f'"""\n'
                        f"\n"
                        f"import numpy as np\n"
                        f"\n"
                        f"# 1. 准备示例数据\n"
                        f"np.random.seed(42)\n"
                        f"X = np.random.randn(100, 3)  # 100个样本，3个特征\n"
                        f"y = 2 * X[:, 0] + 0.5 * X[:, 1] - X[:, 2] + np.random.randn(100) * 0.1\n"
                        f"\n"
                        f'print(f"数据形状: X={{X.shape}}, y={{y.shape}}")\n'
                        f'print(f"特征均值: {{X.mean(axis=0)}}")\n'
                        f"\n"
                        f"# 2. 简单线性模型（最小二乘法）\n"
                        f"X_with_bias = np.column_stack([np.ones(len(X)), X])  # 添加偏置列\n"
                        f"theta = np.linalg.inv(X_with_bias.T @ X_with_bias) @ X_with_bias.T @ y\n"
                        f"\n"
                        f'print(f"模型参数: {{theta}}")\n'
                        f"\n"
                        f"# 3. 预测与评估\n"
                        f"y_pred = X_with_bias @ theta\n"
                        f"mse = np.mean((y - y_pred) ** 2)\n"
                        f'print(f"均方误差(MSE): {{mse:.4f}}")\n'
                        f'print(f"R² 分数: {{1 - mse / np.var(y):.4f}}")\n'
                        f"```\n\n"
                        f"### 运行说明\n\n"
                        f"- 依赖：`numpy`\n"
                        f"- 运行：`python script.py`\n"
                        f"- 预期输出：MSE 值较小（<0.05），R² 接近 1.0\n\n"
                        f"> ⚠️ 此内容为模板降级生成，建议在 AI 服务恢复后重新生成。"
                    ),
                })
            elif res_type == "mindmap":
                resources.append({
                    "type": "mindmap",
                    "title": f"{topic} 知识图谱",
                    "topic": topic,
                    "difficulty": difficulty,
                    "content": (
                        f"- {topic}\n"
                        f"  - 基本概念\n"
                        f"    - 定义与背景\n"
                        f"    - 核心术语\n"
                        f"    - 发展历程\n"
                        f"  - 核心原理\n"
                        f"    - 数学模型\n"
                        f"    - 算法流程\n"
                        f"    - 关键假设\n"
                        f"  - 应用场景\n"
                        f"    - 工业应用\n"
                        f"    - 学术研究\n"
                        f"    - 案例分析\n"
                        f"  - 学习路径\n"
                        f"    - 前置知识\n"
                        f"    - 进阶方向\n"
                        f"    - 推荐资源\n"
                    ),
                })
            elif res_type == "reading":
                resources.append({
                    "type": "reading",
                    "title": f"{topic} 拓展阅读推荐",
                    "topic": topic,
                    "difficulty": difficulty,
                    "content": (
                        f"# {topic} 拓展阅读推荐\n\n"
                        f"### 入门级（适合初学者）\n\n"
                        f"- **推荐教材**：相关领域经典入门教材（建议核实具体书名版本）\n"
                        f"  - 重点关注前3章的基础概念部分\n\n"
                        f"### 进阶级（适合有一定基础的学习者）\n\n"
                        f"- **经典论文**：{topic}领域的里程碑论文\n"
                        f"  - 建议先读综述，再深入具体方法\n\n"
                        f"### 在线资源\n\n"
                        f"- 知名 MOOCs 平台相关课程\n"
                        f"- 技术博客中的实战教程\n\n"
                        f"> ⚠️ 此内容为模板降级生成，建议在 AI 服务恢复后重新生成以获得更准确的推荐。"
                    ),
                })
        return {
            "topic": topic,
            "difficulty": difficulty,
            "resources": resources,
            "generated_at": self._now_iso(),
        }

    @staticmethod
    def _now_iso() -> str:
        """返回当前 UTC 时间的 ISO 8601 字符串"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- 静态样例：供队长 API 调试和队员A 前端开发 ----

SAMPLE_OUTPUT_ML_INTRO = {
    "topic": "机器学习入门",
    "difficulty": "初级",
    "resources": [
        {
            "type": "document",
            "title": "机器学习入门：从零开始理解 AI 的核心",
            "topic": "机器学习基础概念",
            "difficulty": "初级",
            "content": (
                "## 机器学习入门：从零开始理解 AI 的核心\n\n"
                "### 1. 什么是机器学习？\n\n"
                "机器学习（Machine Learning, ML）是人工智能的核心分支，"
                "它让计算机能够**从数据中学习规律**，而不需要人工编写每一条规则。\n\n"
                "举个简单的类比：教小孩认识猫，你不会给他背「猫的定义」，"
                "而是让他看很多猫的图片，他自然就学会了——这就是机器学习的思路。\n\n"
                "### 2. 机器学习的三大类型\n\n"
                "| 类型 | 简介 | 典型场景 |\n"
                "|------|------|----------|\n"
                "| **监督学习** | 有标签数据，学习输入->输出的映射 | 房价预测、垃圾邮件分类 |\n"
                "| **无监督学习** | 无标签数据，发现数据内在结构 | 客户分群、异常检测 |\n"
                "| **强化学习** | 通过奖惩信号学习最优策略 | 游戏AI、机器人控制 |\n\n"
                "### 3. 一个典型机器学习项目的流程\n\n"
                "1. **问题定义**：明确要解决什么问题（分类？回归？聚类？）\n"
                "2. **数据收集与清洗**：获取数据，处理缺失值和异常值\n"
                "3. **特征工程**：选择、构造对模型有用的特征\n"
                "4. **模型选择与训练**：选择合适的算法，用训练数据拟合\n"
                "5. **评估与调优**：用测试数据验证效果，调整超参数\n"
                "6. **部署与监控**：将模型应用到实际场景\n\n"
                "### 4. 小结\n\n"
                "机器学习不是魔法，而是**数据 + 算法 + 算力**的组合。"
                "入门的关键是先理解基本概念，再动手跑通一个完整的项目。"
            ),
        },
        {
            "type": "exercise",
            "title": "机器学习入门自测题",
            "topic": "机器学习基础概念",
            "difficulty": "初级",
            "content": (
                "# 机器学习入门自测题\n\n"
                "### 一、选择题\n\n"
                "**1. 以下哪个是监督学习的典型任务？**\n\n"
                "A. 客户分群\n"
                "B. 房价预测\n"
                "C. 异常检测\n"
                "D. 数据降维\n\n"
                "**正确答案：B**\n"
                "**解析：**房价预测有明确的历史成交价作为标签，属于监督学习的回归任务。"
                "客户分群（A）和异常检测（C）通常为无监督学习，数据降维（D）也是无监督方法。\n\n"
                "**2. 在机器学习项目中，特征工程的主要目的是什么？**\n\n"
                "A. 让代码运行更快\n"
                "B. 从原始数据中提取对模型有用的信息\n"
                "C. 增加数据量\n"
                "D. 减少模型参数数量\n\n"
                "**正确答案：B**\n"
                "**解析：**特征工程的核心目标是将原始数据转化为能够更好地表达问题本质的特征，"
                "让模型更容易学到有效规律。\n\n"
                "**3. 以下哪种情况说明模型可能过拟合了？**\n\n"
                "A. 训练集和测试集上表现都很好\n"
                "B. 训练集上表现很好，但测试集上表现很差\n"
                "C. 训练集和测试集上表现都很差\n"
                "D. 训练集上表现很差，但测试集上表现很好\n\n"
                "**正确答案：B**\n"
                "**解析：**过拟合的典型特征是模型记住了训练数据而非学到通用规律，"
                "导致在训练集上表现优秀但在未见过的测试数据上表现差。\n\n"
                "### 二、简答题\n\n"
                "**4. 请用自己的话解释监督学习和无监督学习的主要区别。**\n\n"
                "**参考答案：**监督学习使用带有标签（答案）的数据进行训练，"
                "目标是学习从输入到输出的映射关系；无监督学习则使用无标签数据，"
                "目标是发现数据中隐藏的结构或模式。"
            ),
        },
        {
            "type": "code",
            "title": "你的第一个机器学习模型：鸢尾花分类",
            "topic": "监督学习-分类",
            "difficulty": "初级",
            "content": (
                "# 你的第一个机器学习模型：鸢尾花分类\n\n"
                "```python\n"
                "# -*- coding: utf-8 -*-\n"
                '"""\n'
                "机器学习入门示例：使用 scikit-learn 训练鸢尾花分类器\n"
                "这是机器学习领域最经典的 Hello World 示例\n"
                '"""\n'
                "\n"
                "# 1. 导入需要的库\n"
                "from sklearn.datasets import load_iris\n"
                "from sklearn.model_selection import train_test_split\n"
                "from sklearn.tree import DecisionTreeClassifier\n"
                "from sklearn.metrics import accuracy_score, classification_report\n"
                "\n"
                "# 2. 加载数据\n"
                "iris = load_iris()\n"
                "X = iris.data          # 特征：花萼长宽、花瓣长宽（4个特征）\n"
                "y = iris.target        # 标签：0=山鸢尾, 1=变色鸢尾, 2=维吉尼亚鸢尾\n"
                "\n"
                'print(f"数据集大小: {X.shape[0]} 条样本")\n'
                'print(f"特征名称: {iris.feature_names}")\n'
                'print(f"类别: {iris.target_names}")\n'
                "\n"
                "# 3. 划分训练集和测试集（80%训练，20%测试）\n"
                "X_train, X_test, y_train, y_test = train_test_split(\n"
                "    X, y, test_size=0.2, random_state=42\n"
                ")\n"
                'print(f"\\n训练集: {len(X_train)} 条, 测试集: {len(X_test)} 条")\n'
                "\n"
                "# 4. 创建并训练模型\n"
                "# 决策树：像20个问题游戏一样，通过一系列是/否判断进行分类\n"
                "model = DecisionTreeClassifier(max_depth=3, random_state=42)\n"
                "model.fit(X_train, y_train)\n"
                "\n"
                "# 5. 预测并评估\n"
                "y_pred = model.predict(X_test)\n"
                "accuracy = accuracy_score(y_test, y_pred)\n"
                "\n"
                'print(f"\\n 模型准确率: {accuracy:.2%}")\n'
                'print("\\n详细分类报告:")\n'
                "print(classification_report(y_test, y_pred, target_names=iris.target_names))\n"
                "\n"
                "# 6. 预测新样本\n"
                "# 假设有一朵未知鸢尾花，测量其花萼长5.1、宽3.5、花瓣长1.4、宽0.2\n"
                "new_flower = [[5.1, 3.5, 1.4, 0.2]]\n"
                "prediction = model.predict(new_flower)\n"
                'print(f"新样本预测类别: {iris.target_names[prediction[0]]}")\n'
                "```\n\n"
                "### 运行要求\n\n"
                "- Python 3.8+\n"
                "- 安装：`pip install scikit-learn`\n"
                "- 运行：复制上述代码到 `iris_demo.py`，`python iris_demo.py`\n"
                "- 预期输出：准确率约 95%+，分类报告显示各类别精确率/召回率\n\n"
                "### 关键概念说明\n\n"
                "- **训练集/测试集划分**：用训练集学模型，用测试集检验泛化能力\n"
                "- **决策树**：通过信息增益选择最优分裂特征，可解释性强\n"
                "- **准确率**：预测正确的样本占总样本的比例\n"
            ),
        },
    ],
    "generated_at": "2026-06-14T00:00:00Z",
}

# ---- 更多样例（JSON 文件） ----
# 以下样例以独立 JSON 文件存放在 data/samples/，方便跨团队共享：
#
#   文件                                           | 主题         | 难度
#   data/samples/resource_sample_ml_intro.json      | 机器学习入门 | 初级
#   data/samples/resource_sample_dl_basics.json     | 深度学习基础 | 中级
#   data/samples/resource_sample_python_data.json   | Python数据分析| 初级
#
# 使用方式：
#   import json
#   with open('data/samples/resource_sample_ml_intro.json', encoding='utf-8') as f:
#       sample = json.load(f)
#
# 或直接导入内置常量：
#   from backend.agents.resource_agent import SAMPLE_OUTPUT_ML_INTRO


def load_sample(name: str) -> dict:
    """加载 data/samples/ 目录下的样例 JSON 文件。

    Args:
        name: 样例文件名（不含 .json 后缀），如 "resource_sample_ml_intro"

    Returns:
        dict: 样例数据，与 ResourceAgent.generate() 输出格式一致
    """
    import os
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "samples", f"{name}.json",
    )
    with open(sample_path, "r", encoding="utf-8") as f:
        return json.load(f)
