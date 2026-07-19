# RLHF 与 LLM 对齐训练

> RLHF (Reinforcement Learning from Human Feedback) 是将人类偏好注入大语言模型的关键技术，也是 ChatGPT/Claude/Gemini 等产品成功的核心方法论。

---

## 1. 为什么需要对齐（Alignment）？

### 1.1 预训练模型的根本问题

大语言模型通过 Next Token Prediction 在海量文本上预训练后，能完成语法正确的续写，但存在三个关键问题：

1. **目标不对齐**：预训练目标是预测下一个 token，而非"有帮助、无害、诚实"地回答用户问题
2. **有害输出**：互联网文本包含偏见、暴力、虚假信息，模型可能复现这些内容
3. **指令遵循差**：Base model 不会自然地遵循指令格式，需要专门训练

**直观理解**：预训练模型是一个"文字接龙机器"，而我们需要的是一个"可靠助手"。

### 1.2 对齐的目标（HHH 原则）

Anthropic 提出的 HHH 框架：
- **Helpful（有帮助）**：准确回答用户问题，提供有用信息
- **Honest（诚实）**：不编造事实，承认不确定性，区分已知与推测
- **Harmless（无害）**：拒绝有害请求，不生成歧视性/暴力/违法内容

---

## 2. RLHF 三阶段流程

RLHF (Christiano et al., 2017; InstructGPT / Ouyang et al., 2022) 包含三个核心阶段：

```
预训练模型 (Base Model)
    │
    ▼
阶段 1: 监督微调 (SFT)
    │  使用人工编写的高质量 (prompt, response) 对训练
    │
    ▼
阶段 2: 奖励模型训练 (RM)
    │  收集人类偏好对比数据，训练一个给回答打分的奖励模型
    │
    ▼
阶段 3: 强化学习优化 (PPO)
    │  使用 PPO 算法最大化奖励模型的评分
    │
    ▼
对齐后的模型 (Aligned Model)
```

### 2.1 阶段一：监督微调 (Supervised Fine-Tuning, SFT)

**目的**：让 base model 学会遵循指令格式。

**数据**：人工标注者根据 prompt 编写高质量回答，构成 (instruction, response) 对。通常需要 10K-100K 条数据。

**训练**：标准的语言模型交叉熵损失，与预训练相同但数据质量远高于互联网文本。

**SFT 之后**：模型已经能较好地遵循指令，但回答质量仍有提升空间——人类标注的"好回答"是绝对的，而有些问题上不同人有不同偏好。

### 2.2 阶段二：奖励模型训练 (Reward Model, RM)

**核心思想**：与其让人类直接编写完美回答（成本高、有争议），不如让人类进行"比较判断"——给定同一个 prompt 的两个回答，选择更好的那个。比较比创作容易得多。

**数据收集流程**：
1. 对每个 prompt，用 SFT 模型生成多个不同回答（通过调整 temperature/sampling）
2. 人工标注者对两个回答进行偏好选择：A 更好 / B 更好 / 差不多
3. 收集数万到数十万条 (prompt, chosen_response, rejected_response) 三元组

**奖励模型架构**：
- 通常使用 SFT 模型初始化（共享初始知识）
- 将最后的语言建模头替换为回归头（输出一个标量分数）
- 输入：(prompt, response) → 输出：标量奖励值 $r$

**损失函数 (Bradley-Terry 偏好模型)**：

$$\mathcal{L}_{RM} = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} \left[ \log \sigma \big( r_\theta(x, y_w) - r_\theta(x, y_l) \big) \right]$$

其中：
- $x$ 是 prompt
- $y_w$ 是人类偏好的回答 (winner)
- $y_l$ 是人类不偏好的回答 (loser)
- $r_\theta$ 是奖励模型
- $\sigma$ 是 sigmoid 函数

**直观理解**：如果人类认为 A > B，那么奖励模型给 A 的分数应该显著高于 B。损失函数推动 $r(A) - r(B)$ 变大。

### 2.3 阶段三：PPO 强化学习优化

**目的**：使用奖励模型作为"虚拟裁判"，通过强化学习进一步优化 SFT 模型的策略。

**为什么需要 RL 而不是直接对 RM 做梯度下降？**
- RM 只在训练数据分布内可靠，如果直接最大化 RM（即对 RM 做梯度上升），模型会快速找到 RM 的漏洞（reward hacking / Goodhart's Law）
- PPO 通过 KL 散度约束，限制策略不要偏离 SFT 模型太远

**PPO 优化目标**：

$$\max_{\pi_\phi} \ \mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_\phi(\cdot|x)} \big[ r_\theta(x, y) - \beta \cdot \text{KL}\big(\pi_\phi(\cdot|x) \| \pi_{\text{SFT}}(\cdot|x)\big) \big]$$

其中：
- $\pi_\phi$ 是正在优化的策略模型
- $\pi_{\text{SFT}}$ 是 SFT 模型（作为参考策略/锚点）
- $\beta$ 是 KL 惩罚系数，控制策略可以偏离 SFT 多远
- $\text{KL}(P \| Q) = \sum P \log(P/Q)$ 衡量两个分布的距离

**PPO 的核心机制**（详见深度强化学习章节）：
1. **Actor**：策略模型 $\pi_\phi$，生成回答
2. **Critic**：价值模型（通常从 RM 初始化），估计期望回报
3. **Clipped Surrogate Objective**：限制每次更新的幅度，防止策略崩溃
4. **GAE (Generalized Advantage Estimation)**：平衡偏差和方差的优势估计

**Reward Hacking 与对策**：
- **过度讨好**：模型学会说"你完全正确！"但无实质内容 → KL 惩罚限制语言风格漂移
- **长度偏好**：RM 倾向于给更长回答高分 → 在奖励中减去长度惩罚
- **RM 过拟合**：RM 在某些领域评分不准确 → 定期用新的人类反馈数据重新训练 RM

---

## 3. RLHF 的变体与改进

### 3.1 DPO (Direct Preference Optimization) — 2023

Rafailov et al. (Stanford, 2023) 提出 DPO，**直接**从偏好数据优化策略模型，完全跳过显式奖励模型训练和 PPO。

**核心公式（DPO 损失函数）**：

$$\mathcal{L}_{\text{DPO}}(\pi_\phi; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} \left[ \log \sigma \left( \beta \log \frac{\pi_\phi(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\phi(y_l|x)}{\pi_{\text{ref}}(y_l|x)} \right) \right]$$

**DPO 的优势**：
1. **无需训练 RM**：省去一个模型，节省 GPU 显存和训练时间
2. **数学等价**：在 Bradley-Terry 偏好模型下，DPO 的最优解与 RLHF 等价
3. **实现简单**：只需修改损失函数，无需 PPO 的复杂基础设施
4. **稳定性**：避免了 RL 训练的不稳定性（reward hacking、策略崩溃）

**DPO 的局限**：
- 偏好数据是离线的（固定的），无法像 PPO 那样在线探索新回答
- 对偏好数据的噪声更敏感（没有 RM 的平滑效应）
- 在需要多轮交互反馈的场景下不如在线 RL

### 3.2 其他变体

| 方法 | 年份 | 核心思想 |
|------|------|---------|
| **RLAIF** (RL from AI Feedback) | 2023 | 用 AI（如 Claude/GPT-4）替代人类标注偏好 → 大幅降低成本 |
| **RRHF** (Rank Response HF) | 2023 | 对比学习 + 排序损失，比 PPO 更简单 |
| **KTO** (Kahneman-Tversky Optimization) | 2024 | 不需要偏好对，只需知道回答"好"还是"不好" |
| **SimPO** | 2024 | 参考模型自由的 DPO 变体，用序列平均 log 概率作为隐式奖励 |
| **SPIN** (Self-Play fIne-tuNing) | 2024 | 模型自己生成训练数据，通过自博弈逐步提升 |
| **ReST** (Reinforced Self-Training) | 2023-24 | 迭代地：用当前最佳模型采样 → 过滤高质量样本 → 用这些样本微调 |

### 3.3 Constitutional AI (CAI) — Anthropic 方案

Bai et al. (2022) 提出的替代 RLHF 的方案，减少对人类反馈的依赖：

1. **监督阶段**：用 AI 生成初始回答 → 按宪章原则（Constitution）让 AI 自我批评 → AI 修订回答 → 用修订后的回答监督微调
2. **RL 阶段**：用 AI 评估回答是否符合宪章原则（而不是人类偏好）→ 用 RLAIF 进行强化学习

**优势**：可扩展（不依赖人类标注）、透明（宪章是公开文档）、可控（修改宪章即可调整行为）

---

## 4. 实践注意事项

### 4.1 偏好数据质量

- **标注者之间的分歧**：不同文化背景、价值观的标注者判断可能差异很大 → 需要清晰的标注指南
- **位置偏差**：标注者倾向于选择第一个/第二个选项（order bias）→ 随机交换 A/B 位置
- **长度偏差**：标注者倾向于选择更长的回答 → 在标注指南中明确要求按质量而非长度判断
- **谄媚性 (Sycophancy)**：标注者倾向于同意看起来"自信"但实际错误的回答 → 需要领域专家参与标注

### 4.2 KL 惩罚系数的选择

- $\beta$ 太小 → 策略偏离 SFT 太远，可能出现 reward hacking 和语言质量下降
- $\beta$ 太大 → 策略过于保守，与 SFT 几乎没有区别
- **实践**：通常从 0.02-0.1 开始，监控 KL 散度在 5-15 nats 范围内

### 4.3 训练不稳定性

PPO 阶段的常见问题：
- **策略崩溃**：模型突然开始输出无意义或重复文本 → 使用 clipped surrogate objective
- **奖励分布漂移**：随着策略改进，生成的回答分布与 RM 训练数据分布越来越远 → 定期重新训练 RM
- **训练-推理不匹配**：训练时使用 teacher forcing，推理时自回归 → 逐步增加生成步数

### 4.4 计算与数据预算

| 阶段 | 数据量 | GPU 时（70B 参考） |
|------|--------|-------------------|
| SFT | 10K-100K 指令 | ~数百 GPU 时 |
| RM 训练 | 100K-1M 偏好对 | ~数百 GPU 时 |
| PPO | 与 SFT 相同的 prompt | ~数千 GPU 时（需同时加载 Actor + Critic + RM + Ref 四个模型） |

**DPO 的成本优势**：只需 1 个模型（vs PPO 的 4 个），训练时间约为 RLHF 的 30-50%。

---

## 5. 评估对齐模型

### 5.1 自动化评估

- **AlpacaEval / MT-Bench**：用 GPT-4 作为裁判，比较模型回答与参考回答的质量
- **Chatbot Arena (LMSys)**：众包的人类偏好比较，使用 Elo 评分排名
- **RewardBench**：评估奖励模型本身的准确性
- **TruthfulQA**：衡量模型对常见误解的抵抗力

### 5.2 红队测试 (Red Teaming)

- 系统性地测试模型在有害场景下的表现
- 包括：越狱尝试 (jailbreaking)、偏见检测、虚假信息生成、危险知识泄露
- 大型 AI 公司有专门的红队团队（Anthropic, OpenAI, Google DeepMind）

### 5.3 关键指标

- **胜率 (Win Rate)**：人类评估中 vs 基线模型的胜出比例
- **无害率 (Harmlessness Rate)**：对有害请求正确拒绝的比例
- **事实准确率 (Factuality)**：回答中可验证事实的正确比例

---

## 6. 常见误区

- ❌ **RLHF 只是"评分+优化"** → ✅ 核心在于 KL 约束，防止模型偏离语言自然性。纯粹的奖励最大化会导致 reward hacking
- ❌ **DPO 完全替代了 RLHF** → ✅ DPO 在很多场景表现好且更简单，但在线 RL (PPO) 在需要探索和多轮反馈时仍有优势
- ❌ **对齐训练越久越好** → ✅ 过度对齐会导致"谄媚性"——模型只说用户想听的，失去提供准确但不受欢迎信息的能力
- ❌ **RLHF 解决了所有安全问题** → ✅ RLHF 是重要一步，但无法解决所有对齐问题。越狱攻击、对抗样本等方法仍可绕过安全防护

---

## 7. 关键要点

- RLHF 三阶段：SFT（学会指令格式）→ RM（学习人类偏好）→ PPO（优化策略）
- KL 散度约束是 RLHF 成功的关键，防止策略偏离自然语言分布
- DPO 通过巧妙的数学变换，直接优化偏好数据而无需显式 RM 和 RL，大幅简化流程
- RLAIF 和 Constitutional AI 用 AI 反馈替代人类反馈，是降低成本和提高可扩展性的方向
- 偏好数据质量是最重要的变量——垃圾偏好数据 → 垃圾对齐结果
- 过度对齐存在风险：谄媚性、信息失真、对不确定问题过于自信
- 对齐是一个持续迭代的过程，没有"一劳永逸"的解决方案
- 现代实践趋势：SFT + DPO 已成为社区默认方案（简单、稳定、效果好），PPO 更多用于前沿实验室的极致优化

> **建议核实**：本文涉及的具体算法（PPO、DPO）建议参考原始论文确认公式细节。模型性能数据和排名以 Chatbot Arena 和 Open LLM Leaderboard 最新数据为准。
