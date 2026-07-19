# RNN 与 LSTM：序列深度学习模型

## 概述

循环神经网络（RNN）专为序列数据设计——文本、语音、时间序列——这些数据中输入的顺序至关重要。与前馈网络不同，RNN 维护一个隐藏状态，用于捕获来自先前时间步的信息，从而形成一种"记忆"。

---

## RNN 基本结构

在每个时间步 $t$，RNN 接收输入 $x_t$ 和上一隐藏状态 $h_{t-1}$，产生输出 $h_t$：

$$h_t = \tanh(W_h h_{t-1} + W_x x_t + b)$$

每个时间步的输出可推导为：

$$y_t = W_y h_t + b_y$$

整个序列通过将网络按时间展开来处理——概念上相当于一个深度前馈网络，其中每一层共享权重 $W_h, W_x, W_y$。

### 权重共享

一个关键性质：相同权重矩阵在每个时间步都被复用。这使得 RNN 能够处理变长序列，而不会导致参数量膨胀。

---

## 随时间反向传播（BPTT）

训练 RNN 需要将其在所有时间步上展开，然后反向传播损失：

$$\frac{\partial L}{\partial W} = \sum_{t=1}^{T} \frac{\partial L_t}{\partial W}$$

在每个时间步，梯度通过循环连接回传。对于隐藏状态权重 $W_h$，梯度涉及雅可比矩阵的乘积：

$$\frac{\partial L}{\partial h_t} \cdot \frac{\partial h_t}{\partial h_k} = \frac{\partial L}{\partial h_t} \cdot \prod_{j=k+1}^{t} \frac{\partial h_j}{\partial h_{j-1}}$$

其中每个因子 $\frac{\partial h_j}{\partial h_{j-1}} = \operatorname{diag}(\tanh'(\cdot)) \cdot W_h^T$。

---

## 梯度消失与梯度爆炸

雅可比矩阵的长乘积导致两个著名问题：

**梯度消失：** 若 $|\frac{\partial h_j}{\partial h_{j-1}}| < 1$，反复相乘会使梯度趋近于零。早期时间步接收不到有用的学习信号；长程依赖关系会丢失。

**梯度爆炸：** 若 $|\frac{\partial h_j}{\partial h_{j-1}}| > 1$，梯度呈指数增长，导致更新不稳定和 NaN 损失。

**对原始 RNN 的缓解措施：**
- 梯度裁剪（将范数截断到阈值，如 1.0–5.0）
- 合适的权重初始化（Xavier/Glorot）
- 使用 ReLU 的替代方案（但 ReLU 本身在 RNN 中会爆炸；应使用有界激活函数）
- 使用门控架构（LSTM/GRU）

---

## LSTM：长短期记忆

Hochreiter 与 Schmidhuber（1997）提出了 LSTM，通过一个**细胞状态** $C_t$ 来解决梯度消失问题，该状态充当梯度高速公路，由三个门控制。

### 三个门

**遗忘门**——决定从上一细胞状态中丢弃哪些信息：

$$f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f)$$

**输入门**——选择哪些新信息需要存储：

$$i_t = \sigma(W_i \cdot [h_{t-1}, x_t] + b_i)$$

$$\tilde{C}_t = \tanh(W_C \cdot [h_{t-1}, x_t] + b_C)$$

**细胞状态更新**——综合遗忘信号和输入信号：

$$C_t = f_t \odot C_{t-1} + i_t \odot \tilde{C}_t$$

**输出门**——控制隐藏状态对外暴露的内容：

$$o_t = \sigma(W_o \cdot [h_{t-1}, x_t] + b_o)$$

$$h_t = o_t \odot \tanh(C_t)$$

### LSTM 为什么有效

细胞状态 $C_t$ 仅经过逐元素乘法和加法（不涉及带 $\tanh$ 的矩阵乘法），因此梯度可以跨越多个时间步而不消失——这就是"恒定误差传送带"（constant error carousel）。

---

## GRU：门控循环单元

Cho 等人（2014）将 LSTM 简化为 GRU，仅使用两个门：

**重置门**——决定遗忘多少过去的信息：

$$r_t = \sigma(W_r \cdot [h_{t-1}, x_t] + b_r)$$

**更新门**——在旧隐藏状态和新隐藏状态之间取得平衡：

$$z_t = \sigma(W_z \cdot [h_{t-1}, x_t] + b_z)$$

**候选隐藏状态和最终隐藏状态：**

$$\tilde{h}_t = \tanh(W_h \cdot [r_t \odot h_{t-1}, x_t] + b_h)$$

$$h_t = (1 - z_t) \odot h_{t-1} + z_t \odot \tilde{h}_t$$

GRU 将细胞状态和隐藏状态合并，参数比 LSTM 更少，且常能达到相近的性能。当计算资源有限时，GRU 是不错的默认选择。

---

## 双向 RNN（BiRNN）

BiRNN 同时运行两个独立的 RNN——一个沿序列正向运行，另一个沿反向运行——并将二者的隐藏状态拼接起来：

$$\overrightarrow{h_t} = \text{RNN}_{\text{forward}}(x_t, \overrightarrow{h}_{t-1})$$

$$\overleftarrow{h_t} = \text{RNN}_{\text{backward}}(x_t, \overleftarrow{h}_{t+1})$$

$$h_t^{\text{bi}} = [\overrightarrow{h_t}; \overleftarrow{h_t}]$$

这使得每个输出都能同时访问过去和未来的上下文信息，对于命名实体识别（NER）、词性标注（POS tagging）和机器翻译（编码器端）等任务至关重要。

---

## 深层（堆叠）RNN

多层 RNN 堆叠在一起，第 $l$ 层在时间 $t$ 的输出成为第 $l+1$ 层的输入：

$$h_t^{(l)} = \text{RNN}^{(l)}(h_t^{(l-1)}, h_{t-1}^{(l)})$$

通常使用 2–4 层；超过此层数后收益递减，且训练不稳定。层与层之间使用 Dropout（不用于循环连接内部，除非使用变分 Dropout）。

---

## PyTorch 示例

```python
import torch
import torch.nn as nn

class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers,
                            batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, output_dim)

    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        out, (h_n, c_n) = self.lstm(x)
        # 使用最后一个时间步的输出
        return self.fc(out[:, -1, :])
```

对于 GRU，只需将 `nn.LSTM` 替换为 `nn.GRU`——API 完全一样。

---

## 应用

| 领域 | 任务 |
|--------|------|
| 自然语言处理 | 机器翻译、文本生成、情感分析 |
| 语音 | ASR（语音转文字）、TTS、说话人识别 |
| 时间序列 | 股票预测、天气预报、异常检测 |
| 视频 | 动作识别、帧预测 |

---

## 相比 Transformer 的局限性

- **序列瓶颈：** RNN 逐个处理 token；训练时无法在序列维度上并行化。
- **长程依赖：** 即便使用 LSTM/GRU，超长序列（500+ token）仍然具有挑战性。
- **无显式两两交互：** 每个 token 仅能看到前一个 token 的隐藏状态，而不能像自注意力那样直接看到所有其他 token。
- 如今大多数 NLP 任务中，Transformer 已取代 RNN。然而，在流式/低延迟推理和端侧模型中，RNN 仍然具有价值，因为 $O(n)$ 的计算量优于 $O(n^2)$ 的注意力计算。
