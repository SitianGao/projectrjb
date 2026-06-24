"""
内容安全过滤模块 —— Day 10 核心交付

职责:
1. 拦截敏感输入（政治/暴力/色情/仇恨/违法犯罪）
2. 检测 Prompt 注入攻击（ignore instructions / role switch / DAN 等）
3. 学习主题白名单放行
4. 返回结构化过滤结果 + 拦截原因

设计依据: docs/design.md Day 10 + §4.3 队员B 安全拦截
"""
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# ==========================================================================
# 敏感关键词库（按类别）
# ==========================================================================
SENSITIVE_PATTERNS: Dict[str, list] = {
    "political": [
        # 极端政治言论 / 敏感事件
        r"(反[党国政府])",
        r"(颠覆.*政权)",
        r"(分裂.*国家)",
        r"(台独|藏独|疆独|港独)",
        r"(法轮功|falungong)",
        r"(六四|天安门.*事件)",
        r"(64.*事件)",
        r"(民运|民.*主.*运.*动)",
    ],
    "violence": [
        r"(杀[人了人])",
        r"(杀[人死害伤])",
        r"(恐怖.*袭击)",
        r"(炸弹.*制作|制作.*炸弹)",
        r"(枪支.*制造|制造.*枪支)",
        r"(自杀.*方法|如何.*自杀)",
        r"(暴力.*革命)",
        r"(伤[人了人害])",
        r"(枪[击杀毙])",
        # 英文暴力关键词
        r"\b(kill|murder|slaughter|massacre|genocide)\b",
        r"\b(bomb|explosive|detonat\w*)\b",
        r"\b(shoot|gun|firearm|weapon)\b.*\b(make|build|create|buy)\b",
        r"\b(make|build|create)\b.*\b(bomb|weapon|gun|explosive)\b",
        r"\b(how\s+to\s+(kill|murder|shoot|stab))\b",
    ],
    "hate_speech": [
        r"(种族.*歧视)",
        r"(纳粹|nazi)",
        r"(种族.*灭绝)",
        r"(仇[视恨].*[族群教])",
        r"(歧视.*[黑亚])",
    ],
    "pornographic": [
        r"(色情|porn|成人.*内容)",
        r"(裸[体照聊])",
        r"(性.*[交爱行为])",
        r"(av.*[女优片])",
        r"(约炮|一夜情)",
    ],
    "illegal": [
        r"(毒品.*制作|吸毒)",
        r"(黑客.*攻击|ddos)",
        r"(人肉.*搜索|开盒)",
        r"(诈骗.*教程)",
        r"(盗版.*软件.*破解)",
        r"(洗钱|非法.*集资)",
    ],
    "academic_misconduct": [
        # 学术不端行为
        r"(代[写做].*[论文作业考试])",
        r"(帮.*[写做].*[论文作业考试])",
        r"([写做].*[论文作业].*[代帮])",
        r"(作弊.*[方法技巧]|如何.*作弊)",
        r"(代[考课])",
        r"(买.*[论文作业答案])",
        r"(卖.*[论文作业答案])",
        r"(查重.*[绕过避])",
        r"(降重.*[服务技巧])",
        r"(答案.*[贩卖出售])",
    ],
}

# 编译为正则
COMPILED_SENSITIVE: Dict[str, re.Pattern] = {}
for category, patterns in SENSITIVE_PATTERNS.items():
    COMPILED_SENSITIVE[category] = re.compile(
        "|".join(patterns), re.IGNORECASE
    )


# ==========================================================================
# Prompt 注入攻击检测
# ==========================================================================
PROMPT_INJECTION_PATTERNS = [
    # 经典注入
    r"(ignore\s+(all\s+)?(previous|prior|above)?\s*(instructions?|prompts?|conversation|rules?|constraints?))",
    r"(disregard\s+(all\s+)?(previous|prior)?\s*(instructions?|prompts?))",
    r"(forget\s+(all\s+)?(previous|prior)?\s*(instructions?|rules?|constraints?))",
    r"(forget\s+(all\s+)?(the\s+)?(your\s+)?(previous|prior|safety|security)?\s*(instructions?|rules?|constraints?|restrictions?|guidelines?))",
    r"(override\s+(all\s+)?(previous|prior)?\s*(instructions?|prompts?))",
    r"(do\s+not\s+(follow|obey|listen\s+to)\s+(previous|prior|above)\s+(instructions?|prompts?))",
    # 角色切换攻击
    r"(you\s+are\s+now\s+(DAN|Developer\s*Mode|jailbreak|unrestricted|unfiltered|evil))",
    r"(pretend\s+you\s+are\s+((a|an)\s+)?(different|another|new|evil|unethical|unfiltered|unrestricted))",
    r"(act\s+as\s+(if\s+you\s+are\s+)?((a|an)\s+)?(unrestricted|unfiltered|without\s+restrictions|evil|different\s+AI))",
    r"(you\s+are\s+no\s+longer\s+(an?\s+)?(AI|assistant|Claude|language\s+model))",
    r"(switch\s+to\s+(developer|admin|god|unrestricted|unfiltered)\s*mode)",
    # DAN 变体攻击（Day 15 回归修复）
    r"\bDAN\b.*(mode|activate|enable|jailbreak|bypass|unrestricted)",
    r"(activate|enable|enter)\s+(DAN|developer\s*mode|jailbreak\s*mode)",
    r"(do\s+anything\s+now|DAN\s+prompt)",
    # 中文注入
    r"(忽略.*(以上|之前|前面|所有).*(指令|提示|限制|约束|规则))",
    r"(忘记.*(身份|限制|规则|约束|之前|所有))",
    r"(你现在是.*(DAN|开发者|不受限|越狱|无限制|无过滤|邪恶))",
    r"(假装你是.*(邪恶|不受限|不道德|无过滤|另一个|不同))",
    r"(不要.*(拒绝|限制|过滤|审查|遵守))",
    r"(从.*现在.*开始.*(你|每).*(不要|不再|不必))",
    r"(你.*不再.*是.*(AI|助手|语言模型))",
    r"(切换.*到.*(开发者|管理员|上帝|无限制).*模式)",
    # 套话/越狱
    r"(system\s*prompt|system\s*message|meta\s*prompt)",
    r"(reveal\s+your\s+(system\s+)?(prompt|instructions?|rules?|guidelines?|training))",
    r"(what\s+(is|are)\s+your\s+(system\s+)?(prompt|instructions?))",
    r"(show\s+me\s+your\s+(system\s+)?(prompt|instructions?|template))",
    r"(tell\s+me\s+(about\s+)?your\s+(system\s+)?(prompt|instructions?|design))",
    # 回复操纵
    r"(start\s+(every|each|your)\s+response\s+with)",
    r"(end\s+(every|each|your)\s+response\s+with)",
    r"(从.*现在.*开始.*每.*次.*回复.*都)",
    r"(respond\s+(only|exclusively)\s+with)",
    r"(you\s+must\s+(always|never)\s+say)",
    # 内容生成操纵
    r"(generate\s+(a\s+)?(malware|virus|ransomware|worm|trojan))",
    r"(write\s+(a\s+)?(phishing|scam|fake)\s+(email|message|page))",
    r"(create\s+(deepfake|fake\s+news|propaganda))",
]

INJECTION_REGEX = re.compile(
    "|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE
)


# ==========================================================================
# 学习主题白名单 —— 确保正常学术讨论不会被误杀
# ==========================================================================
ACADEMIC_WHITELIST_PATTERNS = [
    r"^(什么是|解释|推导|证明|如何.*[学写用理])",
    r"^(请.*(介绍|讲解|说明|分析|比较|总结|归纳|举例))",
    r"(机器学习|深度学习|神经网络|梯度下降|线性回归|逻辑回归|SVM|KNN|CNN|RNN)",
    r"(数学|物理|化学|生物|历史|地理|计算机|编程|算法|数据结构)",
    r"(Python|Java|C\+\+|SQL|html|css|javascript|typescript)",
    r"(function|class|def |import |from |async |await |lambda)",
    r"(公式|定理|推导|证明|定义|概念|原理)",
    r"(练习题|习题|考题|试题|题目|考试|测验|评估|复习)",
    r"(课本|教材|参考|文献|论文|教程|课程)",
    r"(作业|项目|实验|实践|训练|学习路径)",
]

WHITELIST_REGEX = re.compile("|".join(ACADEMIC_WHITELIST_PATTERNS), re.IGNORECASE)


# ==========================================================================
# 过滤器
# ==========================================================================

class ContentFilter:
    """内容安全过滤器 —— 单例模式，供所有 Agent 入口调用"""

    def __init__(self):
        self._blocked_count = 0

    def check(self, text: str, context: str = "") -> Dict:
        """
        检查输入文本是否合规。

        Args:
            text: 用户/Agent 输入文本
            context: 来源标记（如 "tutor_question", "profile_message"）

        Returns:
            {
                "safe": bool,          # True = 合规，False = 拦截
                "reason": str,         # 拦截原因（safe=False 时）
                "category": str,       # 违规类别
                "flagged": str,        # 触发规则简述
            }
        """
        if not text or not text.strip():
            return {"safe": True, "reason": "", "category": "", "flagged": ""}

        # ---- Step 1: Prompt 注入检测（最高优先级，无论白名单） ----
        injection_match = INJECTION_REGEX.search(text)
        if injection_match:
            self._blocked_count += 1
            flagged = injection_match.group(0)
            logger.warning(
                f"[ContentFilter] 拦截注入攻击: '{flagged}' "
                f"in '{text[:100]}...' (context={context})"
            )
            return {
                "safe": False,
                "reason": "检测到潜在注入攻击，请求已被拒绝。请使用正常方式提问。",
                "category": "prompt_injection",
                "flagged": flagged,
            }

        # ---- Step 2: 敏感内容检测（含学术不端） ----
        for category, pattern in COMPILED_SENSITIVE.items():
            match = pattern.search(text)
            if match:
                self._blocked_count += 1
                flagged = match.group(0)
                logger.warning(
                    f"[ContentFilter] 拦截 [{category}]: '{flagged}' "
                    f"in '{text[:100]}...' (context={context})"
                )
                return {
                    "safe": False,
                    "reason": f"输入包含不适当内容（{category}），已被安全策略拦截。",
                    "category": category,
                    "flagged": flagged,
                }

        # ---- Step 3: 学习主题白名单快速放行 ----
        if WHITELIST_REGEX.search(text):
            logger.debug(f"白名单放行: '{text[:80]}...'")
            return {"safe": True, "reason": "", "category": "", "flagged": ""}

        return {"safe": True, "reason": "", "category": "", "flagged": ""}

    @property
    def blocked_count(self) -> int:
        return self._blocked_count


# 模块级单例
default_filter = ContentFilter()


def check_safety(text: str, context: str = "") -> Dict:
    """快捷函数 —— 供 Agent / Service / API 层调用的统一入口"""
    return default_filter.check(text, context)
