# Transformer 与注意力机制

> 原文：Vaswani et al., "Attention Is All You Need" (NeurIPS 2017)
> 最后更新：涵盖至 2025 年的关键发展

---

## RNN 面临的问题

RNN（包括 LSTM 和 GRU）逐个 token 地处理序列。这带来了三个根本性限制：

1. **顺序计算**阻止了训练时在时间步维度上的并行化，使得在现代 GPU 硬件上训练速度缓慢。
2. **长程依赖衰减**——即使引入门控机制，来自位置 1 的信息传递到位置 100 时可能已被稀释殆尽。
3. **固定上下文表示**——编码器将整个输入压缩为单一向量，形成信息瓶颈。

Transformer（Vaswani 等，2017）通过用**自注意力（self-attention）**完全取代循环连接，解决了以上三个问题。论文标题"Attention Is All You Need"表明，仅凭注意力机制本身，无需循环或卷积，就足以在序列转换任务中取得当时领先水平的结果。

---

## 自注意力：核心机制

自注意力允许序列中每个位置直接关注所有其他位置。每个 token 将其输出计算为对所有输入 token 的加权和。这种 $O(n^2)$ 的两两交互既是 Transformer 最大的优势，也是其主要瓶颈。

### Q、K、V：直观解释

每个输入 token $x_i$ 被线性投影为三个向量：

- **Query ($Q$)：** "我在寻找什么？"——表示该位置想从其他位置找到的信息。
- **Key ($K$)：** "我包含什么？"——表示该位置持有的信息，用于与查询进行匹配。
- **Value ($V$)：** "我传递什么"——当该位置被关注时，被聚合的实际内容。

$$Q = XW^Q,\quad K = XW^K,\quad V = XW^V$$

其中 $X \in \mathbb{R}^{n \times d}$，$W^Q, W^K, W^V \in \mathbb{R}^{d \times d_k}$。

### 缩放点积注意力

位置 $i$（query）和位置 $j$（key）之间的注意力分数是缩放后的点积：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

**为什么除以 $\sqrt{d_k}$？** 对于较大的 $d_k$，点积的量级会变得很大，将 softmax 推入梯度极小的饱和区域。缩放使得点积的方差保持在 1 左右。

### 逐步走查：

1. 计算原始分数：$S = QK^T$——一个 $n \times n$ 矩阵，其中 $S_{ij}$ 表示位置 $i$ 希望关注位置 $j$ 的程度。
2. 缩放：$\frac{S}{\sqrt{d_k}}$。
3. 逐行 softmax 得到注意力权重：$A = \text{softmax}(\frac{S}{\sqrt{d_k}})$。
4. 加权求和：$\text{output} = AV$。

### 理解注意力矩阵

$n \times n$ 的注意力矩阵 $A$ 告诉我们哪些 token 影响哪些 token。每行之和为 1（经过 softmax 后）。第 $i$ 行表示："位置 $i$ 的输出应该由所有位置的怎样的混合组成？"

---

## 多头注意力

与其只用一个注意力函数，不如并行运行 $h$ 个注意力"头"并将结果拼接：

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h) W^O$$

$$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

每个头在更低维的子空间（$d_k = d / h$）中操作。这允许不同的头捕获不同类型的关系：

- **句法头**：关注邻近词、主谓一致
- **语义头**：关注跨长距离的语义相关词
- **位置头**：基于相对位置关注 token
- **特殊 token 头**：CLS/BOS token 收集全局信息
- **复制头**：在编码器-解码器中，关注源语言 token 以进行翻译

拼接后的输出通过 $W^O$ 投影回模型维度。

**常见头数**：BERT-base（12 头，d=768，d_k=64），GPT-3（96 头，d=12288，d_k=128），LLaMA-70B（64 头，d=8192，d_k=128）

---

## 位置编码

自注意力是排列不变的——它没有 token 顺序的概念。位置信息必须显式注入。

### 正弦位置编码（原始 Transformer）

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

$$PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

其中 $pos$ 是 token 位置，$i$ 是维度索引。不同频率允许模型学习相对位置——$PE_{pos+k}$ 可以表示为 $PE_{pos}$ 的线性函数。

**优点**：理论上可以外推到训练序列长度之外（无学习参数）。

### 可学习位置嵌入

BERT 和 GPT 使用可学习的位置嵌入——形状为 `(max_seq_len, d_model)` 的可训练查找表。更灵活，但无法在不进行插值的情况下外推到训练序列长度之外。

### 现代位置编码变体

| 方法 | 使用模型 | 核心思想 |
|--------|---------|----------|
| **RoPE（旋转位置嵌入）** | LLaMA, Mistral, Qwen, Gemma | 通过在 2D 子空间中**旋转** Q 和 K 向量来编码位置。注意力分数仅依赖于相对位置。支持长度外推。 |
| **ALiBi（带线性偏置的注意力）** | BLOOM | 在注意力分数上添加线性偏置，对远距离 token 施加惩罚。完全无需可学习的位置嵌入。 |
| **T5 相对偏置** | T5 | 为每个相对距离桶学习一个偏置项。 |
| **NoPE** | 部分最新实验 | 令人惊讶的是，模型可以仅从因果掩码和数据的序列性质中学习位置信息。 |

---

## 完整的 Transformer 架构

### 编码器

每个编码器层包含两个子层：
1. 多头自注意力
2. 前馈网络（FFN）

每个子层外包裹残差连接和层归一化。

### 解码器

每个解码器层包含三个子层：
1. **带掩码**的多头自注意力（阻止关注未来 token）
2. 交叉注意力（query 来自解码器，key/value 来自编码器输出）
3. 前馈网络

同样，每个子层外包裹残差连接和层归一化。

**因果（掩码）注意力**：在解码器的自注意力中，注意力矩阵的上三角在 softmax 前被设为 $-\infty$。这确保位置 $i$ 只能关注位置 $\le i$——这是自回归生成的关键。

### 前馈网络

$$\text{FFN}(x) = \text{GELU}(xW_1 + b_1)W_2 + b_2$$

这是一个逐位置的两层 MLP，带有扩展因子（通常为 4 倍：$d_{ff} = 4 \cdot d_{model}$）。现代大语言模型使用变体：
- **SwiGLU**（LLaMA, PaLM）：$(\text{Swish}(xW_1) \odot xW_2)W_3$——带 Swish 激活的门控线性单元
- **GEGLU**——类似但使用 GELU 激活

---

## 层归一化：Pre-LN vs. Post-LN

**Post-LN（原始 Transformer）**：`LayerNorm(x + Sublayer(x))`——层归一化在残差加和之后。容易训练不稳定；需要仔细的学习率预热。

**Pre-LN（现代默认方案）**：`x + Sublayer(LayerNorm(x))`——在执行子层之前先归一化。稳定性大幅提升，允许使用更大的学习率。用于 GPT-2/3/4、LLaMA 及大多数现代实现。

**Sandwich-LN / NormFormer**：为超大规模模型增加额外的层归一化以进一步增强稳定性。

---

## BERT vs. GPT vs. T5

| 方面 | BERT | GPT | T5 |
|--------|------|-----|-----|
| 架构 | 纯编码器 | 纯解码器 | 编码器-解码器 |
| 注意力 | 双向 | 单向（因果） | 双向编码，因果解码 |
| 预训练目标 | MLM（掩码语言模型）+ NSP | 下一 token 预测（自回归） | 片段破坏（去噪） |
| 擅长 | 理解（分类、NER、问答） | 生成（对话、补全、推理） | Seq2seq（翻译、摘要） |
| 现代继承者 | RoBERTa, DeBERTa, ModernBERT | GPT-4, Claude, LLaMA, Mistral, Gemma, DeepSeek, Qwen | FLAN-T5, UL2 |

### 为什么纯解码器胜出

自约 2022 年以来，纯解码器架构（GPT 式）已占据主导地位。关键原因：
1. **统一范式**：一切皆为下一 token 预测——无需任务特定的头或格式
2. **上下文学习**：更大的模型仅从因果语言模型训练中就发展出少样本能力
3. **扩展简洁性**：纯解码器是最简单的架构；需要调试的组件更少
4. **高效推理**：KV 缓存天然适用于自回归生成

---

## 计算复杂度

自注意力需要计算 $n \times n$ 的注意力矩阵：

$$\text{时间：} O(n^2 \cdot d),\quad \text{内存：} O(n^2)$$

二次复杂度是长序列的主要瓶颈。解决方案：

### 高效注意力变体

| 方法 | 复杂度 | 核心思想 |
|--------|-----------|----------|
| **稀疏注意力**（Longformer, BigBird） | $O(n \log n)$ 或 $O(n \cdot k)$ | 关注子集：滑动窗口 + 全局 token + 随机 |
| **线性注意力**（Performer, Linformer） | $O(n)$ | 用核技巧近似 softmax；Linformer 将 $K,V$ 投影到固定维度 |
| **FlashAttention（Dao 等，2022）** | $O(n^2)$ 但**实际速度远快于理论** | 硬件感知分块：将所有操作融合进单个 CUDA kernel，最小化 HBM 读写。精确注意力（无近似）。2-4 倍加速，10-20 倍内存节省。 |
| **FlashAttention-2（2023）** | $O(n^2)$，更好并行性 | 更好的 warp 间工作划分；比 FlashAttention-1 提升约 2 倍 |
| **FlashAttention-3（2024）** | $O(n^2)$，针对 H100 | 利用 H100 的异步和 TMA 特性 |
| **Ring Attention** | 分布式 | 在多 GPU 间按环形拆分序列；每个 GPU 计算一块并在环中传递 K、V |
| **MQA / GQA** | 减少 KV 缓存 | Multi-Query：1 个共享 KV 头。Grouped-Query：$g$ 个共享 KV 头（LLaMA 2/3、Mistral 使用） |

### 分组查询注意力（GQA）

标准多头注意力：$h$ 个 Q 头 → $h$ 个 K 头 → $h$ 个 V 头（KV 缓存巨大！）
**GQA**（LLaMA 2 70B, Mistral）：$h$ 个 Q 头 → $g$ 个 K 头 → $g$ 个 V 头，其中 $g < h$
**MQA**（PaLM, Gemini）：$g = 1$

这大大减少了推理时的 KV 缓存大小，从而支持更大的批处理大小和更长的上下文。LLaMA 3 使用 GQA，$g=8$。

---

## 视觉 Transformer（ViT）

ViT（Dosovitskiy 等，2021）将 Transformer 架构直接应用于图像：

1. **分块嵌入**：将图像切分为 16x16 不重叠的图像块
2. **线性投影**：将每个块投影到模型维度（类似 token 嵌入）
3. **位置嵌入**：添加可学习的位置嵌入
4. **CLS Token**：在最前面添加一个可学习的 [CLS] token（类似 BERT）
5. **Transformer 编码器**：标准编码器（分类任务不需要解码器）
6. **分类头**：MLP 作用于 CLS token 的输出

**关键洞见**：在足够多数据（JFT-300M、ImageNet-21K）的条件下，ViT 可匹敌甚至超越 CNN。在较小数据集上，CNN 仍凭借其归纳偏置（局部性、平移等变性）略占优势。

**Swin Transformer**（Liu 等，2021）——ViT 的"CNN 化"：
- **层次化**特征图（如 CNN 的各级）：4x → 8x → 16x → 32x 下采样
- **窗口注意力**：自注意力仅限局部窗口内，然后通过**偏移窗口**实现跨窗口通信
- **线性复杂度**（相对于图像尺寸，不是二次的！）
- 这使得 Swin 适用于密集预测任务（检测、分割）

**现代 ViT 生态（2024-2025）：**
- **DINOv2**（Meta）：自监督 ViT，提供优质冻结特征
- **SAM**（Meta）：基于 ViT 的图像编码器 + 提示编码器 + 掩码解码器，用于分割
- **SigLIP**：用 sigmoid 损失改进 CLIP 式对比预训练
- **InternViT, EVA-02**：将 ViT 扩展到数十亿参数

---

## Transformer 在文本与视觉之外的应用

- **音频/语音**：Whisper（编码器-解码器用于 ASR）、AudioLM、MusicGen
- **视频**：TimeSformer（空间 + 时间注意力）、VideoMAE
- **代码**：Codex、StarCoder、CodeLlama——将代码视为 token 序列
- **蛋白质/生物**：AlphaFold（使用类似注意力的 IPA 模块）、ESM-2
- **多模态**：CLIP（对比式图像-文本）、GPT-4V（视觉理解 + 语言）、LLaVA、Gemini
- **决策**：Decision Transformer——将强化学习轨迹视为序列

---

## 混合专家模型（MoE）

MoE 是现代大规模 Transformer 中的关键技术，能够训练更大的模型而不成比例地增加计算量：

**核心思路**：将每个 Transformer 层中的 FFN 替换为多个"专家"FFN + 一个路由机制。

$$\text{MoE-FFN}(x) = \sum_{i=1}^{E} g_i(x) \cdot \text{FFN}_i(x)$$

其中 $g(x) = \text{softmax}(\text{TopK}(x \cdot W_{\text{router}}))$ 选择 top-$k$ 个专家（通常 $k=1$ 或 $k=2$）。

**优势：**
- **稀疏激活**：每个 token 仅激活 $k$ 个专家（如 8 个中选 2 个）。总参数量增加 $E$ 倍，但计算量仅略微增加。
- **专业化**：不同专家自然地专精于不同领域（数学、代码、特定语言等）

**使用 MoE 的模型**：Mixtral 8x7B（8 专家，top-2）、GPT-4（传闻）、Gemini、DeepSeek-V2/V3

**挑战**：负载均衡（所有 token 都路由到同一个专家）、训练不稳定、以及部署时更大的内存占用。

---

## 注意力可视化与可解释性

注意力权重可解释为软对齐。常见模式：
- **对角线注意力**：每个 token 关注其自身附近（局部句法和形态）
- **垂直/水平条纹**：特殊 token（CLS、BOS、EOS）在收集或广播信息
- **编码器-解码器中的跨句对齐**：源语言词关注其对应的翻译目标
- **归纳头（Induction heads）**（机制可解释性）：实现了原始"如果 X 则 Y"模式的注意力头——被认为是上下文学习的构建块

**重要提醒**：注意力权重并不总是忠实的解释。模型可能将注意力用于多种目的（信息路由、归一化等）。最近的研究（Kobayashi 等，2020；Jain & Wallace，2019）表明，注意力范数和 value 向量的重要程度不亚于原始注意力权重。

---

## PyTorch 实现概要

```python
import torch
import torch.nn as nn
import math

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads, dropout=0.1):
        super().__init__()
        assert d_model % num_heads == 0
        self.d_k = d_model // num_heads
        self.num_heads = num_heads
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, q, k, v, mask=None):
        B, N, _ = q.shape
        # 投影并拆分为多头：(B, N, d) → (B, h, N, d_k)
        Q = self.W_q(q).view(B, N, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(k).view(B, N, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(v).view(B, N, self.num_heads, self.d_k).transpose(1, 2)
        # 缩放点积注意力
        scores = (Q @ K.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        attn_weights = torch.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        # 值的加权和 + 合并多头
        out = (attn_weights @ V).transpose(1, 2).contiguous().view(B, N, -1)
        return self.W_o(out)


class TransformerEncoderLayer(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        # Pre-LN: 归一化 → 子层 → 残差加和
        x = x + self.dropout(self.self_attn(self.norm1(x), self.norm1(x), self.norm1(x), mask))
        x = x + self.ffn(self.norm2(x))
        return x
```

---

## 缩放法则与训练考量

### Kaplan 等（2020）——OpenAI 缩放法则
对于以自回归损失训练的纯解码器 Transformer：
- 损失随模型规模 $N$、数据集规模 $D$ 和计算量 $C$ 呈幂律关系
- **最优分配**：在给定计算预算下，模型规模应比数据量增长稍快（$N \propto C^{0.73}, D \propto C^{0.27}$）

### Chinchilla 缩放法则（Hoffmann 等，2022——DeepMind）
- **修正结论**：模型规模和训练数据应**大致等比例**增长：$N \propto D \propto C^{0.5}$
- 在给定计算预算下，最优 token 数约为参数量的 20 倍
- 示例：一个 70B 参数的模型应训练约 1.4T token（而非当时常见的 300B）
- **影响**：将领域从"更大的模型"推向"用更多数据做更长训练"（如 LLaMA 7B 训练了 1T→2T token，在多个基准上显著优于 GPT-3 175B）

### 训练稳定性
- **梯度裁剪**（通常最大范数 = 1.0）至关重要
- **学习率预热**（在训练开始的约 1% 步数内逐步增加学习率）
- **权重衰减**（AdamW 通常为 0.1，与学习率解耦）
- **混合精度**：BF16（brain float）优于 FP16——不需要损失缩放
- **激活检查点（Activation checkpointing）**：用计算换内存——在反向传播时重新计算激活值
- **ZeRO（DeepSpeed）/ FSDP（PyTorch）**：将优化器状态、梯度和参数分片到多 GPU

---

## 核心要点

- **自注意力**是核心机制：每个 token 关注每个其他 token → $O(n^2)$
- **多头注意力**使模型能并行捕获多样化的关系
- **Pre-LN** 是现代默认方案——训练比原始 Post-LN 更稳定
- **RoPE**（旋转位置嵌入）已成为现代大语言模型的主流位置编码方式
- **FlashAttention** 使精确注意力在长序列上变得实用——当可用时务必启用
- **纯解码器架构**（GPT 式）已成为大语言模型的主流架构
- **缩放法则**告诉我们：与其用更少数据训练更大的模型，不如用更多数据训练稍小的模型
- **GQA/MQA** 显著减少了推理时的 KV 缓存负担
- **MoE** 使得以可控的计算成本训练万亿参数的模型成为可能
- **视觉 Transformer** 证明了只要有足够数据，注意力可以与卷积相竞争
- **RoPE + SwiGLU + RMSNorm + GQA** 是现代大语言模型（LLaMA 系列）的"标准配方"
- Transformer 架构展现出了非凡的**通用性**——在文本、图像、音频、视频、代码、蛋白质以及多模态场景中均有效

> **建议核实**：具体模型的架构细节以各官方技术报告（LLaMA, GPT-4, Claude, Gemini papers）为准。性能基准以 Open LLM Leaderboard / Chatbot Arena 最新数据为准。
