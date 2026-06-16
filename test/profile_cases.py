"""
三组画像对话案例 —— ProfileAgent 多轮对话集成测试

覆盖三类典型学生：
  案例1：零基础入门型（小张 — 文科转专业）
  案例2：编程转AI型（小李 — 计算机科班）
  案例3：跨专业应用型（小王 — 生物信息学研究生）

用法：
  cd d:/projectrjb && python -m pytest test/profile_cases.py -vv --noconftest
"""
import sys
import os
import json
import asyncio
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from agents.profile_agent import ProfileAgent


# ============================================================
# Mock LLM —— 返回符合 prompt 要求的 JSON
# ============================================================

def _mock_llm_response(profile_overrides: dict) -> list:
    """构建一个返回指定 profile 的 Mock LLM，分多 chunk 流式返回。"""
    import copy
    overrides = copy.deepcopy(profile_overrides)

    full = {
        "profile": {
            "knowledge_level": "未明确",
            "learning_goal": "未明确",
            "cognitive_style": "未明确",
            "weakness": [],
            "interest": [],
            "pace_preference": "中速均衡型",
        },
        "completeness": 0.3,
        "confidence": 0.5,
        "sources": ["dialogue"],
        "next_questions": [],
    }
    # 深合并：profile 子字段合并，顶层字段覆盖
    if "profile" in overrides:
        full["profile"].update(overrides.pop("profile"))
    full.update(overrides)

    raw = json.dumps(full, ensure_ascii=False)
    n = max(1, len(raw) // 3)
    return [raw[i:i + n] for i in range(0, len(raw), n)]


class MultiTurnMockLLM:
    """多轮 Mock：按调用顺序返回预设的 JSON"""

    def __init__(self, responses: list):
        """
        responses: 每轮一个 dict，表示该轮 LLM 应返回的 profile JSON
        """
        self.responses = responses
        self.call_index = 0
        self.calls = []

    async def chat_stream(self, system, user, model=None):
        self.calls.append({"system": system, "user": user})
        if self.call_index >= len(self.responses):
            # 超出预设轮次，返回空 JSON
            chunks = _mock_llm_response({"completeness": 0.3})
            for c in chunks:
                yield c
            return
        resp = self.responses[self.call_index]
        self.call_index += 1
        chunks = _mock_llm_response(resp)
        for c in chunks:
            yield c


# ============================================================
# 案例 1：小张 — 零基础入门型
# ============================================================

CASE_1_NAME = "小张 — 零基础入门型（文科转专业，数学弱，偏好视频）"

CASE_1_DIALOGUES = [
    # 第 1 轮
    {
        "message": "老师你好，我是大二学生，这学期选了人工智能导论课。我之前是文科背景，计算机基础比较差，有点担心跟不上。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "初级，文科背景，计算机基础薄弱",
                "learning_goal": "跟上人工智能导论课程进度，课程及格",
                "cognitive_style": "未明确",
                "weakness": ["计算机基础"],
                "interest": [],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.35,
            "confidence": 0.75,
            "sources": ["dialogue"],
            "next_questions": [
                "你之前有没有学过编程语言（比如 Python）？",
                "你的数学基础怎么样？",
                "你平时喜欢通过什么方式学习新知识（看书/看视频/动手做）？",
            ],
        },
    },
    # 第 2 轮
    {
        "message": "我只上过一门大学计算机基础课，会一点Python基本语法，但也就hello world和if-else的水平。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "初级，具备Python基础语法入门，无实际编程经验",
                "learning_goal": "跟上人工智能导论课程进度，课程及格",
                "cognitive_style": "未明确",
                "weakness": ["计算机基础", "编程能力"],
                "interest": [],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.45,
            "confidence": 0.78,
            "sources": ["dialogue"],
            "next_questions": [
                "你的数学基础怎么样（微积分、线性代数、概率论）？",
                "你平时喜欢通过什么方式学习？",
            ],
        },
    },
    # 第 3 轮
    {
        "message": "数学我坦白说不太行，高考数学刚及格，线性代数和概率论都还没学过。高数学过但基本忘光了。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "初级（大二），Python入门，数学基础薄弱——高数遗忘、未学线代/概率",
                "learning_goal": "跟上人工智能导论课程进度，考试及格",
                "cognitive_style": "未明确",
                "weakness": ["计算机基础", "编程能力", "数学基础（高数、线代、概率论）"],
                "interest": [],
                "pace_preference": "慢速深入型",
            },
            "completeness": 0.55,
            "confidence": 0.82,
            "sources": ["dialogue"],
            "next_questions": [
                "你平时偏好用什么方式学习？比如看B站视频、看书、还是喜欢动手写代码？",
            ],
        },
    },
    # 第 4 轮
    {
        "message": "我比较喜欢看B站视频学习，很容易看懂。看书的话容易犯困走神，不太适合我。动手写代码的话基础太差经常卡住。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "初级（大二），Python入门，数学薄弱",
                "learning_goal": "跟上人工智能导论课程进度，考试及格",
                "cognitive_style": "视觉型（偏好视频/图解），不偏好阅读文本和独立编程",
                "weakness": ["计算机基础", "编程能力", "数学基础（高数、线代、概率论）"],
                "interest": [],
                "pace_preference": "慢速深入型",
            },
            "completeness": 0.70,
            "confidence": 0.88,
            "sources": ["dialogue"],
            "next_questions": [
                "你有没有特别感兴趣的AI应用领域（比如人脸识别、智能语音、推荐算法）？",
            ],
        },
    },
    # 第 5 轮
    {
        "message": "兴趣的话...我对人脸识别和智能音箱这些比较好奇，日常生活中能接触到的。我的目标就是能听懂课、考试及格，不做太深入的项目。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "初级（大二），Python入门，数学薄弱",
                "learning_goal": "通过人工智能导论考试，达到基本理解水平",
                "cognitive_style": "视觉型（偏好视频/图解），不偏好阅读文本和独立编程",
                "weakness": ["计算机基础", "编程能力", "数学基础（高数、线代、概率论）"],
                "interest": ["计算机视觉（人脸识别）", "语音识别（智能音箱）"],
                "pace_preference": "慢速深入型",
            },
            "completeness": 0.80,
            "confidence": 0.90,
            "sources": ["dialogue"],
            "next_questions": [],
        },
    },
]

CASE_1_EXPECTED_FINAL = {
    "knowledge_level_keywords": ["初级", "Python"],
    "learning_goal_keywords": ["考试", "及格", "通过"],
    "cognitive_style_keywords": ["视觉", "视频"],
    "weakness_count_min": 3,
    "weakness_keywords": ["数学", "编程", "计算机"],
    "interest_keywords": ["人脸识别", "语音", "智能音箱"],
    "completeness_min": 0.70,
    "confidence_min": 0.85,
}


# ============================================================
# 案例 2：小李 — 编程转AI型
# ============================================================

CASE_2_NAME = "小李 — 编程转AI型（计算机科班，数学推导弱，偏好代码）"

CASE_2_DIALOGUES = [
    # 第 1 轮
    {
        "message": "你好，我是计算机专业大三的，Java和Python都很熟，数据结构、算法这些基础课都学过了。这学期想系统学习机器学习和深度学习。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（大三计算机专业），编程能力强（Java/Python），数据结构与算法基础扎实",
                "learning_goal": "系统学习机器学习与深度学习",
                "cognitive_style": "未明确",
                "weakness": [],
                "interest": [],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.35,
            "confidence": 0.82,
            "sources": ["dialogue"],
            "next_questions": [
                "你对机器学习的哪些方向比较感兴趣？比如CV、NLP、推荐系统？",
                "你的数学基础（微积分、线代、概率）怎么样？",
                "你平时更喜欢看书学理论，还是看代码实现来理解？",
            ],
        },
    },
    # 第 2 轮
    {
        "message": "我对NLP特别感兴趣，最近ChatGPT这些大模型太强了。我之前做过一个简单的Java聊天机器人，但完全基于规则的，现在想了解真正的AI是怎么做的。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（大三计算机），Java/Python熟练，有基于规则的聊天机器人项目经验",
                "learning_goal": "系统学习ML/DL，重点掌握NLP方向，理解大模型原理",
                "cognitive_style": "未明确",
                "weakness": [],
                "interest": ["NLP", "大语言模型", "对话系统"],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.50,
            "confidence": 0.85,
            "sources": ["dialogue"],
            "next_questions": [
                "你的数学基础怎么样？比如微积分、线性代数、概率论这些？",
                "你平时更喜欢看论文和书籍，还是看代码实现？",
            ],
        },
    },
    # 第 3 轮
    {
        "message": "数学的话...实话实说我的微积分和线性代数都是应试过的，考试成绩还行但在实际推导的时候经常懵。概率论学得还不错。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（大三计算机），Java/Python熟练，微积分和线代应试水平，概率论基础好",
                "learning_goal": "系统学习ML/DL，重点NLP方向，理解大模型原理",
                "cognitive_style": "未明确",
                "weakness": ["数学推导（微积分、线性代数应用能力弱）"],
                "interest": ["NLP", "大语言模型", "对话系统"],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.58,
            "confidence": 0.84,
            "sources": ["dialogue"],
            "next_questions": [
                "你学习新知识时，更喜欢看书、看视频还是直接看代码实现？",
                "你愿意花多长时间系统学习？有没有具体的时间目标？",
            ],
        },
    },
    # 第 4 轮
    {
        "message": "我觉得看代码实现对我来说最快！经常是看一遍源码就懂了，然后反过去看公式才有感觉。纯看数学推导的话我会比较吃力。时间上我希望半年内能打Kaggle比赛。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（大三计算机），编程能力强，数学推导偏弱（概率论较好）",
                "learning_goal": "6个月内系统掌握ML/DL，具备Kaggle参赛能力，重点NLP方向",
                "cognitive_style": "动手型（偏好代码实现，从代码反推理论）",
                "weakness": ["数学推导（微积分、线性代数应用能力弱）"],
                "interest": ["NLP", "大语言模型", "对话系统", "Kaggle竞赛"],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.72,
            "confidence": 0.88,
            "sources": ["dialogue"],
            "next_questions": [
                "你目前对机器学习了解多少？比如监督学习、无监督学习这些概念熟悉吗？",
            ],
        },
    },
    # 第 5 轮
    {
        "message": "监督学习无监督学习这些概念我大概了解过，看过一些科普文章。但具体算法比如SVM、随机森林、神经网络这些的数学原理还不太懂。对了，我还对图神经网络感兴趣，因为想做知识图谱相关的东西。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（大三计算机），编程强，ML概念有科普级了解，具体算法原理未掌握",
                "learning_goal": "6个月内系统掌握ML/DL核心算法，Kaggle参赛，重点NLP + 知识图谱方向",
                "cognitive_style": "动手型（偏好代码实现，从代码反推理论）",
                "weakness": ["数学推导（微积分/线代应用）", "ML算法数学原理"],
                "interest": ["NLP", "大语言模型", "对话系统", "Kaggle竞赛", "图神经网络", "知识图谱"],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.85,
            "confidence": 0.90,
            "sources": ["dialogue"],
            "next_questions": [],
        },
    },
]

CASE_2_EXPECTED_FINAL = {
    "knowledge_level_keywords": ["高级", "计算机", "Java", "Python"],
    "learning_goal_keywords": ["Kaggle", "NLP", "系统"],
    "cognitive_style_keywords": ["动手", "代码"],
    "weakness_keywords": ["数学推导", "微积分"],
    "interest_keywords": ["NLP", "大语言", "对话", "图神经网络", "知识图谱"],
    "completeness_min": 0.75,
    "confidence_min": 0.85,
}


# ============================================================
# 案例 3：小王 — 跨专业应用型
# ============================================================

CASE_3_NAME = "小王 — 跨专业应用型（生物信息学研一，统计好，需针对性路径）"

CASE_3_DIALOGUES = [
    # 第 1 轮
    {
        "message": "你好，我是生物信息学专业研一的学生。我的研究方向是蛋白质结构预测，需要用到深度学习的方法。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（研一生物信息学），有研究方向，需AI工具支撑",
                "learning_goal": "掌握用于蛋白质结构预测的深度学习方法",
                "cognitive_style": "未明确",
                "weakness": [],
                "interest": ["蛋白质结构预测", "生物信息学"],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.35,
            "confidence": 0.78,
            "sources": ["dialogue"],
            "next_questions": [
                "你的编程基础怎么样？主要使用什么语言？",
                "你的数学和统计基础如何？",
                "你希望在多长时间内掌握这些技能？",
            ],
        },
    },
    # 第 2 轮
    {
        "message": "我统计学基础比较好，本科做过很多统计分析和实验设计。R语言很熟练，Python也会写但不算是高手水平，大概能写个脚本处理数据这样。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（研一生物信息学），统计学扎实，R熟练，Python中等（数据处理级别）",
                "learning_goal": "掌握用于蛋白质结构预测的深度学习方法",
                "cognitive_style": "未明确",
                "weakness": ["Python编程深度（非高手水平）"],
                "interest": ["蛋白质结构预测", "生物信息学"],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.48,
            "confidence": 0.83,
            "sources": ["dialogue"],
            "next_questions": [
                "你目前在阅读AI相关论文时，主要遇到什么困难？",
                "你偏好什么样的学习方式？",
            ],
        },
    },
    # 第 3 轮
    {
        "message": "我读AlphaFold的论文时，CNN的部分能大概理解，但图神经网络（GNN）的部分就比较吃力了。因为蛋白质可以表示为3D图结构，GNN对这个很关键。我希望能针对性补一下这块知识。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（研一生物信息学），统计扎实，CNN有基础理解，GNN薄弱",
                "learning_goal": "掌握CNN和GNN，用于蛋白质3D结构预测研究",
                "cognitive_style": "未明确",
                "weakness": ["Python编程深度", "图神经网络（GNN）"],
                "interest": ["蛋白质结构预测", "图神经网络", "AlphaFold", "生物信息学"],
                "pace_preference": "中速均衡型",
            },
            "completeness": 0.60,
            "confidence": 0.85,
            "sources": ["dialogue"],
            "next_questions": [
                "你偏好什么样的学习方式？看论文、看代码、还是系统课程？",
                "你希望在多长时间内掌握这些技能？",
            ],
        },
    },
    # 第 4 轮
    {
        "message": "我平时主要是看论文+看官方代码实现来学习。但我发现一个问题：直接看代码经常卡在某个地方不理解，又不知道去哪里补基础知识。所以我希望有一个针对性强的学习路径，帮我先补必要的ML/DL基础，再深入GNN。时间上我比较紧，希望在3个月内能上手。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（研一生物信息学），统计扎实，R熟练，Python中等，CNN有基础，GNN薄弱",
                "learning_goal": "3个月内：补ML/DL必要基础 → 深入掌握GNN → 应用于蛋白质结构预测",
                "cognitive_style": "动手型+理论型（偏好论文+官方代码学习，需要结构化路径引导）",
                "weakness": ["Python编程深度", "图神经网络（GNN）", "ML/DL基础系统性不足"],
                "interest": ["蛋白质结构预测", "图神经网络", "AlphaFold", "生物信息学"],
                "pace_preference": "快速概览型（3个月目标，时间紧迫）",
            },
            "completeness": 0.75,
            "confidence": 0.88,
            "sources": ["dialogue"],
            "next_questions": [
                "你每周大概能投入多少小时学习？",
            ],
        },
    },
    # 第 5 轮
    {
        "message": "每周大概能投入15个小时吧。另外我对Transformer也挺好奇的，看到有些蛋白质语言模型（比如ESM）用了Transformer架构。不过我不想学太杂，希望能聚焦在对我研究真正有用的东西上。",
        "llm_profile": {
            "profile": {
                "knowledge_level": "中高级（研一生物信息学），统计扎实，Python中等，CNN有基础，GNN薄弱",
                "learning_goal": "3个月内（每周15h）：系统性补ML/DL基础 → GNN → 蛋白质结构预测应用，聚焦研究相关技术",
                "cognitive_style": "动手+理论混合型（论文+代码学习，需结构化路径）",
                "weakness": ["Python编程深度", "GNN", "ML/DL系统性基础"],
                "interest": ["蛋白质结构预测", "图神经网络", "AlphaFold", "Transformer", "蛋白质语言模型（ESM）"],
                "pace_preference": "快速聚焦型（限时+限定范围）",
            },
            "completeness": 0.85,
            "confidence": 0.91,
            "sources": ["dialogue"],
            "next_questions": [],
        },
    },
]

CASE_3_EXPECTED_FINAL = {
    "knowledge_level_keywords": ["高级", "研一", "统计", "R"],
    "learning_goal_keywords": ["蛋白质", "GNN", "3个月", "15"],
    "cognitive_style_keywords": ["动手", "论文"],
    "weakness_keywords": ["Python", "GNN"],
    "interest_keywords": ["蛋白质", "图神经网络", "AlphaFold", "Transformer"],
    "completeness_min": 0.75,
    "confidence_min": 0.85,
}


# ============================================================
# 测试：多轮对话画像构建
# ============================================================

def _check_profile(result, expected):
    """验证 profile 内容与预期匹配"""
    profile = result.get("profile", {})
    # 合并为字符串便于搜索
    profile_str = json.dumps(profile, ensure_ascii=False).lower()

    # 知识水平
    for kw in expected.get("knowledge_level_keywords", []):
        assert kw.lower() in profile_str, f"knowledge_level 应包含关键词: {kw}"

    # 学习目标
    for kw in expected.get("learning_goal_keywords", []):
        assert kw.lower() in profile_str, f"learning_goal 应包含关键词: {kw}"

    # 认知风格
    for kw in expected.get("cognitive_style_keywords", []):
        assert kw.lower() in profile_str, f"cognitive_style 应包含关键词: {kw}"

    # 薄弱点数量
    weakness = profile.get("weakness", [])
    if "weakness_count_min" in expected:
        assert len(weakness) >= expected["weakness_count_min"], \
            f"weakness 至少 {expected['weakness_count_min']} 项，实际: {len(weakness)}"

    # 薄弱点关键词
    for kw in expected.get("weakness_keywords", []):
        weakness_str = " ".join(weakness).lower()
        assert kw.lower() in weakness_str, f"weakness 应包含关键词: {kw}"

    # 兴趣关键词
    for kw in expected.get("interest_keywords", []):
        interest_str = " ".join(profile.get("interest", [])).lower()
        assert kw.lower() in interest_str, f"interest 应包含关键词: {kw}"

    # 完整度
    if "completeness_min" in expected:
        assert result.get("completeness", 0) >= expected["completeness_min"], \
            f"completeness 应 ≥ {expected['completeness_min']}，实际: {result.get('completeness')}"

    # 置信度
    if "confidence_min" in expected:
        assert result.get("confidence", 0) >= expected["confidence_min"], \
            f"confidence 应 ≥ {expected['confidence_min']}，实际: {result.get('confidence')}"


class TestCase1Beginner:
    """案例1：小张 — 零基础入门型，5轮对话逐步完善画像"""

    def test_full_multiturn(self):
        """完整5轮对话 → 画像从 0.35 → 0.80"""
        llm = MultiTurnMockLLM([d["llm_profile"] for d in CASE_1_DIALOGUES])
        agent = ProfileAgent(llm)

        history = []
        current_profile = None

        for i, turn in enumerate(CASE_1_DIALOGUES):
            result = asyncio.run(
                agent.build_profile(
                    student_id="case_001",
                    message=turn["message"],
                    history=list(history),
                    current_profile=current_profile,
                )
            )
            # 每轮都应有合法结构
            assert "profile" in result
            assert result["student_id"] == "case_001"
            history.append(turn["message"])
            current_profile = result  # 下一轮的增量基础

            # LLM 被调用了
            assert len(llm.calls) == i + 1

        # 最终轮验证
        _check_profile(result, CASE_1_EXPECTED_FINAL)

        # completeness 应逐轮提升
        assert result["completeness"] >= CASE_1_DIALOGUES[0]["llm_profile"]["completeness"]

    def test_single_turn_first(self):
        """仅第一轮：画像不完整，应返回追问"""
        llm = MultiTurnMockLLM([CASE_1_DIALOGUES[0]["llm_profile"]])
        agent = ProfileAgent(llm)
        result = asyncio.run(
            agent.build_profile("case_001", CASE_1_DIALOGUES[0]["message"])
        )
        assert result["completeness"] < 0.5
        assert len(result["next_questions"]) >= 2


class TestCase2CSMajor:
    """案例2：小李 — 编程转AI型，5轮对话从泛到精"""

    def test_full_multiturn(self):
        llm = MultiTurnMockLLM([d["llm_profile"] for d in CASE_2_DIALOGUES])
        agent = ProfileAgent(llm)

        history = []
        current_profile = None

        for i, turn in enumerate(CASE_2_DIALOGUES):
            result = asyncio.run(
                agent.build_profile(
                    student_id="case_002",
                    message=turn["message"],
                    history=list(history),
                    current_profile=current_profile,
                )
            )
            assert "profile" in result
            history.append(turn["message"])
            current_profile = result

        _check_profile(result, CASE_2_EXPECTED_FINAL)

    def test_cognitive_style_emerges(self):
        """第4轮后认知风格应明确为'动手型/代码优先'"""
        llm = MultiTurnMockLLM([d["llm_profile"] for d in CASE_2_DIALOGUES])
        agent = ProfileAgent(llm)

        history = []
        cp = None
        for i, turn in enumerate(CASE_2_DIALOGUES[:4]):
            cp = asyncio.run(
                agent.build_profile("case_002", turn["message"], list(history), cp)
            )
            history.append(turn["message"])

        profile_str = json.dumps(cp["profile"], ensure_ascii=False)
        assert any(kw in profile_str for kw in ["动手", "代码"])

    def test_interest_accumulates(self):
        """兴趣在5轮中不断累积：NLP → 大模型 → GNN → 知识图谱"""
        llm = MultiTurnMockLLM([d["llm_profile"] for d in CASE_2_DIALOGUES])
        agent = ProfileAgent(llm)

        history = []
        cp = None
        for turn in CASE_2_DIALOGUES:
            cp = asyncio.run(
                agent.build_profile("case_002", turn["message"], list(history), cp)
            )
            history.append(turn["message"])

        interests = " ".join(cp["profile"].get("interest", []))
        assert "NLP" in interests
        assert len(cp["profile"].get("interest", [])) >= 4


class TestCase3CrossDiscipline:
    """案例3：小王 — 跨专业应用型，精准需求 + 限时目标"""

    def test_full_multiturn(self):
        llm = MultiTurnMockLLM([d["llm_profile"] for d in CASE_3_DIALOGUES])
        agent = ProfileAgent(llm)

        history = []
        current_profile = None

        for i, turn in enumerate(CASE_3_DIALOGUES):
            result = asyncio.run(
                agent.build_profile(
                    student_id="case_003",
                    message=turn["message"],
                    history=list(history),
                    current_profile=current_profile,
                )
            )
            assert "profile" in result
            history.append(turn["message"])
            current_profile = result

        _check_profile(result, CASE_3_EXPECTED_FINAL)

    def test_learning_goal_reflects_time_constraint(self):
        """学习目标应体现 3个月 + 每周15h 的时间约束"""
        llm = MultiTurnMockLLM([d["llm_profile"] for d in CASE_3_DIALOGUES])
        agent = ProfileAgent(llm)

        history = []
        cp = None
        for turn in CASE_3_DIALOGUES:
            cp = asyncio.run(
                agent.build_profile("case_003", turn["message"], list(history), cp)
            )
            history.append(turn["message"])

        goal_lower = cp["profile"].get("learning_goal", "").lower()
        assert "3个月" in goal_lower or "3" in goal_lower
        assert "15" in goal_lower or "每周" in goal_lower

    def test_pace_is_fast(self):
        """时间紧 → 学习节奏应为快速型"""
        llm = MultiTurnMockLLM([d["llm_profile"] for d in CASE_3_DIALOGUES])
        agent = ProfileAgent(llm)

        history = []
        cp = None
        for turn in CASE_3_DIALOGUES:
            cp = asyncio.run(
                agent.build_profile("case_003", turn["message"], list(history), cp)
            )
            history.append(turn["message"])

        pace = cp["profile"].get("pace_preference", "")
        assert any(kw in pace for kw in ["快速", "快"]), f"pace 应为快速型，实际: {pace}"

    def test_interest_is_specific_not_broad(self):
        """兴趣聚焦于研究方向（蛋白质、GNN），而非泛泛的AI"""
        llm = MultiTurnMockLLM([d["llm_profile"] for d in CASE_3_DIALOGUES])
        agent = ProfileAgent(llm)

        history = []
        cp = None
        for turn in CASE_3_DIALOGUES:
            cp = asyncio.run(
                agent.build_profile("case_003", turn["message"], list(history), cp)
            )
            history.append(turn["message"])

        interests = " ".join(cp["profile"].get("interest", []))
        assert "蛋白质" in interests
        assert "图神经网络" in interests or "GNN" in interests
