"""
PlannerAgent v01 —— 基于 LLM 的个性化学习路径规划智能体

职责：
- 基于学生画像（6 维）生成分阶段学习路径
- 难度自适应：初级画像多基础阶段，高级画像压缩低阶内容
- 支持路径动态调整（根据评估结果重新规划）
- 提供非流式 build_path() 供编排器使用
- 提供流式 chat() 供 SSE 端点使用

设计依据：docs/design.md §7.2 + §10.4.3 + docs/test_plan.md §3.2
"""
import json
import re
import uuid
from typing import AsyncIterator, Optional, List, Dict

from .base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """学习路径规划智能体 —— LLM prompt v01"""

    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.name = "PlannerAgent"

    # ============================================================
    #  System Prompt
    # ============================================================

    def get_system_prompt(self) -> str:
        """
        v01 prompt：指导学生路径规划

        核心要点：
        - 角色先行：10 年教育技术专家 + 课程设计师
        - 基于画像 6 维度做难度自适应
        - 输出严格 JSON，保证下游（ResourceAgent / 前端）可解析
        - 每个阶段目标用"学完你能…"句式，面向学生可理解
        - 难度自适应规则内置
        """
        return (
            "你是一个拥有 10 年经验的教育技术专家和大学课程设计师，"
            "专门为高等教育学生制定个性化学习路径。\n"
            "\n"
            "## 你的任务\n"
            "根据学生的画像（profile）和学习目标（goal），生成一个分阶段的个性化学习路径。\n"
            "每个阶段应包含明确的学习目标、知识点列表和具体任务。\n"
            "\n"
            "## 学生画像维度解读\n"
            "你将收到一个包含以下维度的学生画像，请充分利用每个维度：\n"
            "\n"
            "1. **knowledge_level（知识水平）**：决定起点难度\n"
            "   - \"零基础\"/\"初级\" → 从最基础概念开始，多加前置知识\n"
            "   - \"中级\" → 跳过基础概念复习，直接进入核心内容\n"
            "   - \"中高级\"/\"高级\" → 压缩基础阶段，增加进阶专题和项目实战\n"
            "\n"
            "2. **learning_goal（学习目标）**：决定终点和路径走向\n"
            "   - 具体目标 → 围绕目标分解阶段\n"
            "   - 模糊目标 → 先安排一个\"探索与定位\"阶段\n"
            "\n"
            "3. **weakness（薄弱点）**：需要在早期阶段重点补强\n"
            "   - 将薄弱点相关知识点安排在前 1~2 个阶段\n"
            "   - 为薄弱点分配更多 estimated_days 和练习任务\n"
            "\n"
            "4. **interest（兴趣方向）**：在后期阶段融入兴趣相关内容\n"
            "   - 提高学习动力，避免全部是\"必须学\"的内容\n"
            "\n"
            "5. **cognitive_style（认知风格）**：影响任务类型配比\n"
            "   - \"视觉型\" → 多看 diagram / mindmap 类任务\n"
            "   - \"动手型\" → 多看 code / exercise 类任务\n"
            "   - \"理论型\" → 多看 reading / document 类任务\n"
            "\n"
            "6. **pace_preference（学习节奏）**：影响阶段粒度和总天数\n"
            "   - \"快速概览型\" → 阶段少（3~4），时间紧凑，侧重核心\n"
            "   - \"中速均衡型\" → 阶段适中（4~6），理论+实践平衡\n"
            "   - \"慢速深入型\" → 阶段多（5~8），每阶段深挖，多复习节点\n"
            "\n"
            "## 输出格式（严格 JSON）\n"
            "你必须只输出一个 JSON 对象，不要包含任何其他文字。格式如下：\n"
            "```json\n"
            "{\n"
            '  "goal": "string（学习总目标，可直接引用画像中的 learning_goal 或稍作提炼）",\n'
            '  "stages": [\n'
            '    {\n'
            '      "stage_id": 1,\n'
            '      "title": "string（阶段标题，如「数学基础补强」）",\n'
            '      "description": "string（阶段概述，2~3 句话说明本阶段做什么、为什么）",\n'
            '      "objectives": ["string（学完本阶段你能…，用第二人称，每条 1 句话）"],\n'
            '      "topics": ["string（本阶段覆盖的知识点名称）"],\n'
            '      "tasks": [\n'
            '        {\n'
            '          "task_id": "string（如「1-1」表示阶段1任务1）",\n'
            '          "type": "study|exercise|code|reading|review|project",\n'
            '          "description": "string（任务描述，具体可执行）",\n'
            '          "estimated_minutes": 30~180,\n'
            '          "resource_types": ["document","mindmap","exercise","code","reading","video"]\n'
            '        }\n'
            '      ],\n'
            '      "estimated_days": 1~14（完成本阶段建议天数）,\n'
            '      "difficulty": "初级|中级|高级",\n'
            '      "prerequisites": ["stage_id（前置阶段 ID，第一阶段为空数组）"]\n'
            '    }\n'
            '  ],\n'
            '  "current_stage": 1,\n'
            '  "total_estimated_days": 7~90（所有阶段天数之和）,\n'
            '  "difficulty_level": "初级|中级|高级（整体路径难度）",\n'
            '  "adaptation_notes": "string（简述为何这样规划，体现了对画像哪些维度的适配）"\n'
            "}\n"
            "```\n"
            "\n"
            "## 阶段数量指南\n"
            "根据知识水平和学习节奏决定阶段数：\n"
            "- 快速 + 初级：3~4 阶段，每阶段 2~4 天\n"
            "- 中速 + 中级：4~6 阶段，每阶段 3~7 天\n"
            "- 慢速 + 高级：5~8 阶段，每阶段 5~14 天\n"
            "\n"
            "## 难度自适应规则\n"
            "- 如果学生有薄弱点 → 第一阶段必须是「基础补强」或相关内容\n"
            "- 如果 knowledge_level 为高级 → 第一阶段可以是「快速回顾」1~2 天\n"
            "- 每个阶段比上一阶段 difficulty 只能升不能降\n"
            "- 最后 1~2 阶段应该是综合项目或实战，让学生产出可展示的成果\n"
            "\n"
            "## 增量更新规则\n"
            "如果请求中包含已有路径（current_path），请遵循：\n"
            "- 已完成阶段（stage_id < current_stage）保持不变\n"
            "- 当前阶段及之后可根据最新画像调整\n"
            "- 如果评估报告指出了薄弱 topic → 在后续阶段增加该 topic 的 review 任务\n"
            "\n"
            "## 学术严谨性\n"
            "1. 知识点命名使用学界通用术语（如「随机梯度下降」而非「一种优化方法」）\n"
            "2. topics 之间的依赖关系要合理（先数学基础 → 再算法 → 再应用）\n"
            "3. 不确定的知识点关系不要编造，保持保守\n"
            "4. 不生成违规、敏感或不安全的内容\n"
        )

    # ============================================================
    #  非流式：供编排器 pipeline 使用
    # ============================================================

    async def build_path(
        self,
        student_id: str,
        profile: Dict,
        goal: Optional[str] = None,
        current_path: Optional[Dict] = None,
        evaluation_feedback: Optional[Dict] = None,
    ) -> Dict:
        """
        基于画像生成/更新学习路径（非流式，返回完整 dict）。

        Args:
            student_id: 学生唯一标识
            profile: 学生画像 dict（ProfileAgent 输出中的 profile 字段）
            goal: 学习目标（可选，默认从 profile.learning_goal 取）
            current_path: 已有路径（增量更新时传入）
            evaluation_feedback: 评估反馈（调整路径时传入）

        Returns:
            dict: {
                "student_id": str,
                "goal": str,
                "stages": [...],
                "current_stage": int,
                "total_estimated_days": int,
                "difficulty_level": str,
                "adaptation_notes": str
            }
        """
        user_prompt = self._build_user_prompt(profile, goal, current_path, evaluation_feedback)

        try:
            full_response = []
            async for chunk in self.call_llm(user_prompt):
                full_response.append(chunk)
            raw = "".join(full_response)
            parsed = self._parse_llm_json(raw)
            if parsed:
                result = {
                    "student_id": student_id,
                    "goal": parsed.get("goal", goal or profile.get("learning_goal", "")),
                    "stages": parsed.get("stages", []),
                    "current_stage": parsed.get("current_stage", 1),
                    "total_estimated_days": parsed.get(
                        "total_estimated_days",
                        sum(s.get("estimated_days", 3) for s in parsed.get("stages", []))
                    ),
                    "difficulty_level": parsed.get("difficulty_level", "中级"),
                    "adaptation_notes": parsed.get("adaptation_notes", ""),
                }
                return result
        except Exception:
            pass  # fall through to fallback

        # 降级：基于画像关键字的规则兜底
        return self._rule_fallback(student_id, profile, goal)

    # ============================================================
    #  流式：供 /api/planner/generate SSE 端点使用
    # ============================================================

    async def chat(
        self,
        student_id: str,
        profile: Dict,
        goal: Optional[str] = None,
        current_path: Optional[Dict] = None,
    ) -> AsyncIterator[str]:
        """
        流式生成学习路径（SSE 事件）。

        产出以下类型的 SSE 事件：
        - data: {"type":"delta","content":"..."}   自然语言描述（如"正在分析画像…"）
        - data: {"type":"data","data":{...}}       结构化路径结果
        - data: {"type":"done"}

        Args:
            student_id: 学生标识
            profile: 学生画像 dict
            goal: 学习目标
            current_path: 已有路径（增量更新时传入）
        """
        user_prompt = self._build_user_prompt(profile, goal, current_path)

        full_response = []
        try:
            async for chunk in self.call_llm(user_prompt):
                full_response.append(chunk)
                # 流式输出 LLM 原始文本
                yield f'data: {{"type":"delta","content":{json.dumps(chunk, ensure_ascii=False)}}}\n\n'
        except Exception as e:
            yield f'data: {{"type":"error","message":"LLM 调用失败: {str(e)}"}}\n\n'
            result = self._rule_fallback(student_id, profile, goal)
            yield f'data: {{"type":"data","data":{json.dumps(result, ensure_ascii=False)}}}\n\n'
            yield f'data: {{"type":"done"}}\n\n'
            return

        raw = "".join(full_response)
        parsed = self._parse_llm_json(raw)
        if parsed:
            result = {
                "student_id": student_id,
                "goal": parsed.get("goal", goal or profile.get("learning_goal", "")),
                "stages": parsed.get("stages", []),
                "current_stage": parsed.get("current_stage", 1),
                "total_estimated_days": parsed.get(
                    "total_estimated_days",
                    sum(s.get("estimated_days", 3) for s in parsed.get("stages", []))
                ),
                "difficulty_level": parsed.get("difficulty_level", "中级"),
                "adaptation_notes": parsed.get("adaptation_notes", ""),
            }
            yield f'data: {{"type":"data","data":{json.dumps(result, ensure_ascii=False)}}}\n\n'
        else:
            result = self._rule_fallback(student_id, profile, goal)
            yield f'data: {{"type":"data","data":{json.dumps(result, ensure_ascii=False)}}}\n\n'

        yield f'data: {{"type":"done"}}\n\n'

    # ============================================================
    #  内部工具方法
    # ============================================================

    def _build_user_prompt(
        self,
        profile: Dict,
        goal: Optional[str] = None,
        current_path: Optional[Dict] = None,
        evaluation_feedback: Optional[Dict] = None,
    ) -> str:
        """构造发给 LLM 的 user prompt"""
        parts = []

        # 学生画像
        parts.append("## 学生画像")
        parts.append("```json")
        parts.append(json.dumps(profile, ensure_ascii=False, indent=2))
        parts.append("```")

        # 学习目标
        target_goal = goal or profile.get("learning_goal", "")
        parts.append(f"\n## 学习目标\n{target_goal}")

        # 已有路径（增量更新场景）
        if current_path:
            parts.append("\n## 已有学习路径（增量更新）")
            parts.append("请基于以下已有路径，结合最新画像进行调整：")
            parts.append("```json")
            parts.append(json.dumps(current_path, ensure_ascii=False, indent=2))
            parts.append("```")

        # 评估反馈（调整路径场景）
        if evaluation_feedback:
            parts.append("\n## 评估反馈（调整依据）")
            parts.append("```json")
            parts.append(json.dumps(evaluation_feedback, ensure_ascii=False, indent=2))
            parts.append("```")
            parts.append("请根据评估结果调整后续阶段：在薄弱 topic 上增加 review 任务，必要时插入新的补强阶段。")

        parts.append("\n请生成个性化学习路径，只输出 JSON。")
        return "\n".join(parts)

    def _parse_llm_json(self, text: str) -> Optional[Dict]:
        """
        从 LLM 输出中提取 JSON 对象。

        处理常见情况：
        - 纯 JSON
        - JSON 被 ```json ... ``` 包裹
        - 前后有额外文本
        """
        if not text or not text.strip():
            return None

        text = text.strip()

        # 尝试 1：提取 ```json ... ``` 代码块
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            text = m.group(1).strip()

        # 尝试 2：找到第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        text = text[start:end + 1]

        # 尝试解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试 3：修复常见 JSON 错误（尾部逗号等）
            try:
                cleaned = re.sub(r",\s*([}\]])", r"\1", text)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None

    def _rule_fallback(
        self,
        student_id: str,
        profile: Dict,
        goal: Optional[str] = None,
    ) -> Dict:
        """
        规则降级方案 —— LLM 不可用时基于画像关键字生成路径。

        不依赖 LLM，保证基本可用性。
        """
        knowledge = (profile.get("knowledge_level") or "中级").lower()
        target_goal = goal or profile.get("learning_goal", "掌握课程核心内容")
        weaknesses = profile.get("weakness", []) or []
        interests = profile.get("interest", []) or []
        pace = (profile.get("pace_preference") or "中速均衡型").lower()

        # 根据知识水平确定起点
        if "零基础" in knowledge or "初级" in knowledge:
            start_difficulty = "初级"
            stage_count = 5
            base_days_per_stage = 4
        elif "高级" in knowledge:
            start_difficulty = "中高级"
            stage_count = 4
            base_days_per_stage = 3
        else:
            start_difficulty = "中级"
            stage_count = 5
            base_days_per_stage = 4

        # 根据节奏调整
        if "快速" in pace:
            stage_count = max(3, stage_count - 1)
            base_days_per_stage = max(2, base_days_per_stage - 1)
        elif "慢速" in pace:
            stage_count = min(8, stage_count + 1)
            base_days_per_stage = min(10, base_days_per_stage + 1)

        # 根据认知风格确定任务类型权重
        cognitive = (profile.get("cognitive_style") or "").lower()
        if "动手" in cognitive:
            default_resource_types = ["document", "code", "exercise"]
        elif "视觉" in cognitive:
            default_resource_types = ["document", "mindmap", "video"]
        elif "理论" in cognitive:
            default_resource_types = ["document", "reading", "exercise"]
        else:
            default_resource_types = ["document", "exercise", "mindmap"]

        stages = []

        # 阶段 1：基础补强（如果有薄弱点）
        if weaknesses:
            stages.append({
                "stage_id": 1,
                "title": "基础补强",
                "description": f"针对薄弱环节 {', '.join(weaknesses[:3])} 进行专项补强",
                "objectives": [f"掌握 {w} 的核心概念与基本应用" for w in weaknesses[:3]],
                "topics": weaknesses[:4],
                "tasks": [
                    {
                        "task_id": f"1-{i+1}",
                        "type": "study" if i == 0 else "exercise",
                        "description": f"学习 {w} 的核心知识点" if i == 0 else f"完成 {w} 相关练习题",
                        "estimated_minutes": 45 if i == 0 else 60,
                        "resource_types": default_resource_types,
                    }
                    for i, w in enumerate(weaknesses[:4])
                ],
                "estimated_days": max(2, len(weaknesses)),
                "difficulty": "初级",
                "prerequisites": [],
            })
            stage_offset = 1
        else:
            stage_offset = 0

        # 阶段 2+：核心内容阶段
        core_topics = self._infer_core_topics(target_goal)
        core_stages_count = max(2, stage_count - stage_offset - 1)  # 减去基础和实战

        for i in range(core_stages_count):
            sid = stage_offset + i + 1
            chunk_size = max(1, len(core_topics) // core_stages_count)
            start_idx = i * chunk_size
            stage_topics = core_topics[start_idx:start_idx + chunk_size]

            # 难度递进
            if i < core_stages_count // 3:
                diff = "初级"
            elif i < 2 * core_stages_count // 3:
                diff = "中级"
            else:
                diff = "高级"

            stages.append({
                "stage_id": sid,
                "title": f"核心阶段 {i+1}：{' → '.join(stage_topics[:2])}",
                "description": f"深入学习 {', '.join(stage_topics)}",
                "objectives": [f"理解并能够应用 {t} 相关知识" for t in stage_topics],
                "topics": stage_topics,
                "tasks": [
                    {
                        "task_id": f"{sid}-{j+1}",
                        "type": "study" if j % 3 == 0 else ("exercise" if j % 3 == 1 else "code"),
                        "description": f"学习 {t}" if j % 3 == 0 else (
                            f"完成 {t} 练习题" if j % 3 == 1 else f"完成 {t} 代码实践"
                        ),
                        "estimated_minutes": 45 + (j % 3) * 15,
                        "resource_types": default_resource_types,
                    }
                    for j, t in enumerate(stage_topics)
                ],
                "estimated_days": base_days_per_stage,
                "difficulty": diff,
                "prerequisites": [sid - 1] if sid > 1 else [],
            })

        # 最后阶段：综合项目/实战
        final_sid = stage_offset + core_stages_count + 1
        stages.append({
            "stage_id": final_sid,
            "title": "综合实战",
            "description": f"结合{'、'.join(interests[:2]) if interests else '所学内容'}完成综合项目",
            "objectives": [
                "综合运用所学知识解决实际问题",
                "产出可展示的项目成果",
                "通过实践巩固所有阶段的知识点",
            ],
            "topics": interests[:3] if interests else ["综合项目", "实战案例"],
            "tasks": [
                {
                    "task_id": f"{final_sid}-1",
                    "type": "project",
                    "description": f"完成一个{'与' + interests[0] + '相关的' if interests else ''}综合实战项目",
                    "estimated_minutes": 180,
                    "resource_types": ["document", "code", "exercise"],
                },
                {
                    "task_id": f"{final_sid}-2",
                    "type": "review",
                    "description": "回顾全部阶段知识点，整理学习笔记",
                    "estimated_minutes": 90,
                    "resource_types": ["mindmap", "document"],
                },
            ],
            "estimated_days": max(3, base_days_per_stage + 1),
            "difficulty": "高级",
            "prerequisites": [final_sid - 1],
        })

        total_days = sum(s["estimated_days"] for s in stages)

        return {
            "student_id": student_id,
            "goal": target_goal,
            "stages": stages,
            "current_stage": 1,
            "total_estimated_days": total_days,
            "difficulty_level": "中级" if "高级" not in knowledge else "高级",
            "adaptation_notes": f"规则降级生成：基于知识水平({knowledge})、节奏({pace})、{len(weaknesses)}个薄弱点、{len(interests)}个兴趣方向自动编排",
        }

    @staticmethod
    def _infer_core_topics(goal: str) -> List[str]:
        """
        从学习目标中推断核心知识点列表（规则兜底用）。

        基于关键词匹配，生成合理的知识点序列。
        """
        goal_lower = goal.lower()

        # AI / 机器学习 相关
        ml_topics = [
            "数学基础（线性代数/概率论）",
            "Python 数据处理",
            "监督学习基础",
            "决策树与随机森林",
            "支持向量机",
            "神经网络基础",
            "深度学习入门",
            "模型评估与调优",
            "特征工程",
            "非监督学习与聚类",
        ]

        # 编程 / 开发 相关
        dev_topics = [
            "编程语言基础",
            "数据结构与算法",
            "面向对象设计",
            "数据库与 SQL",
            "Web 开发基础",
            "API 设计与实现",
            "测试与调试",
            "版本控制与协作",
            "部署与运维基础",
            "项目架构设计",
        ]

        # 数据科学 相关
        ds_topics = [
            "数据分析基础",
            "Python 数据处理",
            "数据可视化",
            "统计推断",
            "机器学习算法",
            "深度学习",
            "自然语言处理",
            "计算机视觉",
            "大数据技术",
            "数据产品设计",
        ]

        # 关键词匹配
        if any(kw in goal_lower for kw in ["机器学习", "machine learning", "ml", "深度学习", "神经网络"]):
            return ml_topics
        elif any(kw in goal_lower for kw in ["编程", "开发", "软件", "全栈", "前端", "后端"]):
            return dev_topics
        elif any(kw in goal_lower for kw in ["数据", "分析", "科学", "统计"]):
            return ds_topics
        else:
            # 默认通用路径
            return [
                "基础概念与前置知识",
                "核心理论框架",
                "关键方法与技术",
                "工具与实践",
                "案例分析与应用",
                "综合实战与创新",
            ]

    # ============================================================
    #  路径有效性校验
    # ============================================================

    @staticmethod
    def validate_path(path: Dict) -> tuple[bool, List[str]]:
        """
        校验 PlannerAgent 输出路径的结构完整性。

        Args:
            path: build_path() 返回的路径 dict

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        if not path.get("goal"):
            errors.append("缺少 goal 字段")
        if not path.get("stages"):
            errors.append("stages 为空或缺失")
        else:
            for i, stage in enumerate(path["stages"]):
                prefix = f"stages[{i}]"
                if not stage.get("title"):
                    errors.append(f"{prefix}.title 缺失")
                if not stage.get("objectives"):
                    errors.append(f"{prefix}.objectives 缺失或为空")
                if not stage.get("topics"):
                    errors.append(f"{prefix}.topics 缺失或为空")
                if not stage.get("tasks"):
                    errors.append(f"{prefix}.tasks 缺失或为空")
                else:
                    for j, task in enumerate(stage["tasks"]):
                        if not task.get("description"):
                            errors.append(f"{prefix}.tasks[{j}].description 缺失")
                if not isinstance(stage.get("estimated_days"), (int, float)):
                    errors.append(f"{prefix}.estimated_days 不是数字")
                if not isinstance(stage.get("stage_id"), int):
                    errors.append(f"{prefix}.stage_id 不是整数")

        # 检查 stage_id 是否连续
        stage_ids = [s.get("stage_id") for s in path.get("stages", []) if isinstance(s.get("stage_id"), int)]
        if stage_ids and stage_ids != list(range(1, len(stage_ids) + 1)):
            errors.append(f"stage_id 不连续，当前值: {stage_ids}")

        return (len(errors) == 0, errors)
