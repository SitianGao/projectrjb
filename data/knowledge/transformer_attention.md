# Transformer and Attention Mechanisms

## The Problem with RNNs

RNNs (including LSTMs and GRUs) process sequences token-by-token. This creates three fundamental limitations:

1. **Sequential computation** prevents parallelization across time steps during training, making it slow on modern GPU hardware.
2. **Long-range dependency decay** — even with gating, information from position 1 can be diluted by the time it reaches position 100.
3. **Fixed context representation** — the encoder compresses the entire input into a single vector, creating a bottleneck.

Transformers (Vaswani et al., 2017) address all three by replacing recurrence entirely with **self-attention**.

---

## Self-Attention: Core Mechanism

Self-attention allows every position in the sequence to directly attend to every other position. Each token computes its output as a weighted sum over all input tokens.

### Q, K, V: Intuitive Explanation

Each input token $x_i$ is linearly projected into three vectors:

- **Query ($Q$):** "What am I looking for?" — represents what this position wants to find in other positions.
- **Key ($K$):** "What do I contain?" — represents what information this position holds, used for matching against queries.
- **Value ($V$):** "What I communicate" — the actual content that gets aggregated when this position is attended to.

$$Q = XW^Q,\quad K = XW^K,\quad V = XW^V$$

where $X \in \mathbb{R}^{n \times d}$ and $W^Q, W^K, W^V \in \mathbb{R}^{d \times d_k}$.

### Scaled Dot-Product Attention

The attention score between position $i$ (query) and position $j$ (key) is the scaled dot product:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

**Why scale by $\sqrt{d_k}$?** For large $d_k$, dot products become large in magnitude, pushing the softmax into regions of extremely small gradients. Scaling keeps the variance of the dot product around 1.

### Step-by-step walkthrough:

1. Compute raw scores: $S = QK^T$ — an $n \times n$ matrix where $S_{ij}$ is how much position $i$ wants to attend to position $j$.
2. Scale: $\frac{S}{\sqrt{d_k}}$.
3. Apply softmax row-wise to get attention weights: $A = \text{softmax}(\frac{S}{\sqrt{d_k}})$.
4. Weighted sum of values: $\text{output} = AV$.

---

## Multi-Head Attention

Instead of one attention function, run $h$ parallel attention "heads" and concatenate:

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h) W^O$$

$$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

Each head operates in a lower-dimensional subspace ($d_k = d / h$). This allows different heads to capture different types of relationships: syntactic, semantic, positional, etc. The concatenated output is projected back to the model dimension via $W^O$.

---

## Positional Encoding

Self-attention is permutation-invariant — it has no notion of token order. Positional information must be injected explicitly.

### Sinusoidal Encoding (original Transformer)

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

$$PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

where $pos$ is the token position and $i$ is the dimension index. Different frequencies allow the model to learn relative positions — $PE_{pos+k}$ can be expressed as a linear function of $PE_{pos}$.

### Learned Position Embeddings

BERT and GPT use learned position embeddings — a trainable lookup table of shape `(max_seq_len, d_model)`. More flexible but cannot extrapolate beyond training sequence length.

---

## Full Transformer Architecture

### Encoder

Each encoder layer contains two sub-layers:
1. Multi-Head Self-Attention
2. Feed-Forward Network (FFN)

Each sub-layer is wrapped with a residual connection and layer normalization.

### Decoder

Each decoder layer contains three sub-layers:
1. **Masked** Multi-Head Self-Attention (prevents attending to future tokens)
2. Cross-Attention (queries from decoder, keys/values from encoder output)
3. Feed-Forward Network

Again, residual connections and layer norm around each sub-layer.

### Feed-Forward Network

$$\text{FFN}(x) = \max(0, xW_1 + b_1)W_2 + b_2$$

or with GELU in modern variants. This is a position-wise two-layer MLP with expansion factor (typically 4x: $d_{ff} = 4 \cdot d_{model}$).

---

## Layer Normalization: Pre-LN vs. Post-LN

**Post-LN (original):** `x + Sublayer(LayerNorm(x))` — the layer norm is inside the residual branch. Prone to training instability; requires careful learning rate warmup.

**Pre-LN (modern default):** `x + Sublayer(LayerNorm(x))` — the layer norm is applied before the sublayer, not after. Much more stable, allows larger learning rates, and is used in GPT-2/3 and most modern implementations.

---

## BERT vs. GPT vs. T5

| Aspect | BERT | GPT | T5 |
|--------|------|-----|-----|
| Architecture | Encoder-only | Decoder-only | Encoder-Decoder |
| Attention | Bidirectional | Unidirectional (causal) | Bidirectional enc, causal dec |
| Pretraining | MLM + NSP | Autoregressive LM | Span corruption |
| Best for | Understanding tasks | Generation tasks | Seq2seq tasks |
| Example use | Classification, NER, QA | Text generation, chat | Translation, summarization |

---

## Computational Complexity

Self-attention requires computing an $n \times n$ attention matrix:

$$\text{Time: } O(n^2 \cdot d),\quad \text{Memory: } O(n^2)$$

This is the main bottleneck for long sequences. Solutions:
- **Sparse attention** (Longformer, BigBird): attend to a subset of positions.
- **Linear attention** (Performer, Linformer): approximate the softmax with kernel tricks.
- **FlashAttention**: hardware-aware exact attention that minimizes HBM reads/writes.

---

## Attention Visualization

Attention weights can be interpreted as soft alignment. Common patterns:
- Diagonal attention: each token attends near itself (local syntax).
- Vertical/horizontal stripes: special tokens (e.g., CLS, EOS) gathering or broadcasting.
- Cross-sentence alignment in encoder-decoder: source word attending to its translation.

---

## PyTorch Implementation Outline

```python
import torch
import torch.nn as nn
import math

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0
        self.d_k = d_model // num_heads
        self.num_heads = num_heads
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, q, k, v, mask=None):
        B, N, _ = q.shape
        # Project and split into heads
        Q = self.W_q(q).view(B, N, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(k).view(B, N, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(v).view(B, N, self.num_heads, self.d_k).transpose(1, 2)
        # Scaled dot-product attention
        scores = (Q @ K.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = torch.softmax(scores, dim=-1)
        out = (attn @ V).transpose(1, 2).contiguous().view(B, N, -1)
        return self.W_o(out)
```
