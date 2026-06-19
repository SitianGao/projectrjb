# 深度学习基础

## 1. 神经网络基础

### 1.1 什么是深度学习？

深度学习（Deep Learning）是机器学习的一个子领域，使用**多层神经网络**自动学习数据的层次化特征表示。浅层学习手工设计特征，深层网络自动从原始数据中逐层抽象出越来越高级的语义特征。

### 1.2 人工神经元

一个神经元接收多个输入，加权求和后通过激活函数输出：

$$y = f\left(\sum_{i=1}^{n} w_i x_i + b\right) = f(\mathbf{w}^T\mathbf{x} + b)$$

- $\mathbf{w}$：权重向量，控制各输入的重要程度
- $b$：偏置，控制神经元激活的阈值
- $f$：激活函数，引入非线性

### 1.3 多层感知机 (MLP)

- **输入层**：接收原始数据
- **隐藏层**：逐层提取特征，层数越多、宽度越大 → 表达能力越强（但也越容易过拟合）
- **输出层**：分类（Softmax）或回归（线性）

### 1.4 前向传播与反向传播

**前向传播**：输入逐层计算到输出
$$\mathbf{a}^{(l)} = f(\mathbf{W}^{(l)}\mathbf{a}^{(l-1)} + \mathbf{b}^{(l)})$$

**反向传播**：利用链式法则从输出层向输入层逐层计算损失对每个参数的梯度，然后通过梯度下降更新参数

$$\mathbf{W} \leftarrow \mathbf{W} - \eta \frac{\partial L}{\partial \mathbf{W}}$$

其中 $\eta$ 为学习率。

---

## 2. 激活函数

| 函数 | 公式 | 输出范围 | 优点 | 缺点 |
|------|------|----------|------|------|
| **Sigmoid** | $\sigma(x)=\frac{1}{1+e^{-x}}$ | (0, 1) | 平滑可导 | 易饱和导致梯度消失 |
| **Tanh** | $\tanh(x)=\frac{e^x-e^{-x}}{e^x+e^{-x}}$ | (-1, 1) | 零中心 | 仍会饱和 |
| **ReLU** | $f(x)=\max(0,x)$ | [0, ∞) | 计算简单，缓解梯度消失 | 神经元可能"死亡"（负半轴梯度为0） |
| **Leaky ReLU** | $f(x)=\max(\alpha x, x)$ | (-∞, ∞) | 解决ReLU死亡问题 | 引入超参数 $\alpha$ |
| **Softmax** | $\frac{e^{x_i}}{\sum_j e^{x_j}}$ | (0, 1) 和为1 | 多分类概率输出 | 仅用于输出层 |

**选型建议**：隐藏层默认用 ReLU，二分类输出用 Sigmoid，多分类输出用 Softmax，回归输出用线性。

---

## 3. 损失函数

### 3.1 回归任务
- **MSE（均方误差）**：$L = \frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2$
- **MAE（平均绝对误差）**：$L = \frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|$（对异常值更鲁棒）
- **Huber Loss**：结合MSE和MAE，小误差用MSE、大误差用MAE

### 3.2 分类任务
- **交叉熵（Cross-Entropy）**：$L = -\sum_{c=1}^{C} y_c \log(\hat{y}_c)$
- 二分类特例（Binary Cross-Entropy）：$L = -[y\log(\hat{y}) + (1-y)\log(1-\hat{y})]$

---

## 4. 优化算法

| 优化器 | 核心思想 | 适用场景 |
|--------|----------|----------|
| **SGD** | 沿梯度方向更新，$w \leftarrow w - \eta \nabla L$ | 基础baseline |
| **SGD + Momentum** | 累积历史梯度动量，加速收敛、减少震荡 | 比纯SGD更稳定 |
| **Adam** | 结合动量 + 自适应学习率（一阶矩 + 二阶矩估计） | **默认首选**，大多数任务表现好 |
| **AdamW** | Adam + 解耦权重衰减 | Transformer训练标配 |

---

## 5. 正则化与防过拟合

| 方法 | 原理 | 使用场景 |
|------|------|----------|
| **L1/L2 正则化** | 在损失函数中加入权重惩罚项 | 线性模型、小型网络 |
| **Dropout** | 训练时随机丢弃神经元（概率 p），迫使网络学习冗余表示 | 全连接层（p=0.5），CNN（p=0.2） |
| **Batch Normalization** | 对每层输入做标准化，加速训练、允许更大学习率 | CNN/MLP 标配 |
| **Layer Normalization** | 沿特征维标准化，不依赖 batch 大小 | Transformer/RNN |
| **Early Stopping** | 验证集 loss 不再下降时停止训练 | 通用 |
| **数据增强** | 图像：随机裁剪/翻转/颜色抖动；文本：回译/同义词替换 | 数据量不足时 |

---

## 6. 卷积神经网络 (CNN)

### 6.1 核心组件

| 组件 | 作用 | 关键参数 |
|------|------|----------|
| **卷积层 (Conv)** | 提取局部特征，权重共享大幅减少参数量 | kernel_size, stride, padding |
| **池化层 (Pooling)** | 降采样，增大感受野，增强平移不变性 | pool_size, stride |
| **全连接层 (FC)** | 高层语义推理与分类 | 输入/输出维度 |

### 6.2 经典架构演进

| 网络 | 年份 | 核心创新 | 参数量 |
|------|------|----------|--------|
| LeNet-5 | 1998 | CNN开创者，手写数字识别 | ~60K |
| AlexNet | 2012 | ReLU + Dropout + GPU训练，ImageNet冠军 | ~60M |
| VGG | 2014 | 小卷积核(3×3)堆叠，深度增加 | ~138M |
| ResNet | 2015 | **残差连接**解决深层网络退化，可训练152层+ | ~25M(50层) |
| DenseNet | 2017 | 稠密连接，每层接收前面所有层的特征 | ~8M(121层) |
| EfficientNet | 2019 | 复合缩放（深度+宽度+分辨率） | ~5M(B0) |

### 6.3 残差连接 (Residual Connection)

$$\mathbf{y} = \mathcal{F}(\mathbf{x}) + \mathbf{x}$$

核心思想：让网络学习残差映射 $\mathcal{F}(\mathbf{x}) = \mathbf{y} - \mathbf{x}$，而非直接学习 $\mathbf{y}$。当 $\mathcal{F}(\mathbf{x}) = 0$ 时退化为恒等映射，保证深层至少不差于浅层。

---

## 7. 循环神经网络 (RNN)

### 7.1 RNN 基本结构

$$h_t = \tanh(W_h h_{t-1} + W_x x_t + b)$$

隐藏状态 $h_t$ 跨时间步传递，理论上能捕捉任意长的序列依赖。

### 7.2 LSTM（长短期记忆网络）

引入三个门控机制：

- **遗忘门**：$f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f)$ — 决定丢弃哪些旧信息
- **输入门**：$i_t = \sigma(W_i \cdot [h_{t-1}, x_t] + b_i)$ — 决定存储哪些新信息
- **输出门**：$o_t = \sigma(W_o \cdot [h_{t-1}, x_t] + b_o)$ — 决定输出哪些信息

### 7.3 GRU（门控循环单元）

LSTM的简化版，合并遗忘门和输入门为**更新门**：
- 参数量更少，训练更快
- 在小数据集上常优于LSTM

### 7.4 选型建议

- 序列标注 → BiLSTM + CRF
- 短序列（<50步）→ GRU
- 长序列 → LSTM
- **现代NLP → Transformer已基本取代RNN**

---

## 8. Transformer

### 8.1 核心创新：自注意力 (Self-Attention)

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

- $Q$（Query）：当前token想要查询什么
- $K$（Key）：每个token能被查询的标签
- $V$（Value）：每个token实际携带的信息
- $\sqrt{d_k}$：缩放因子，防止点积过大导致Softmax梯度消失

### 8.2 多头注意力 (Multi-Head Attention)

$$ \text{MultiHead}(Q,K,V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O $$

每个 head 关注不同的表示子空间（如语法、语义、位置等）。

### 8.3 位置编码 (Positional Encoding)

Transformer 没有循环结构，需要显式注入位置信息：

$$PE_{(pos, 2i)} = \sin(pos / 10000^{2i/d_{model}})$$
$$PE_{(pos, 2i+1)} = \cos(pos / 10000^{2i/d_{model}})$$

### 8.4 经典架构

| 模型 | 特点 | 参数量 | 适用场景 |
|------|------|--------|----------|
| **BERT** | 双向编码，MLM预训练 | 110M(base) | 文本理解、分类、NER |
| **GPT** | 单向解码，自回归生成 | 175B(GPT-3) | 文本生成、对话 |
| **T5** | 统一的Text-to-Text框架 | 60M~11B | 翻译、摘要、QA |
| **ViT** | Transformer应用于图像 | 86M(base) | 图像分类 |

---

## 9. 训练技巧

### 9.1 学习率调度

- **Step Decay**：每N个epoch将学习率乘以 $\gamma$（如0.1）
- **Cosine Annealing**：余弦函数平滑衰减，配合warmup重启
- **Warmup**：训练初期线性增加学习率，避免模型震荡。Transformer训练几乎必备

### 9.2 权重初始化

- **Xavier/Glorot**：适用于Sigmoid/Tanh激活，保持输入输出方差一致
- **He/Kaiming**：适用于ReLU激活，方差缩放因子为 $\sqrt{2/n}$
- 错误初始化会导致梯度消失或爆炸

### 9.3 梯度裁剪 (Gradient Clipping)

限制梯度的最大范数，防止梯度爆炸（RNN训练中尤为重要）

### 9.4 混合精度训练

使用FP16 + FP32混合精度加速训练，减少显存占用（A100/H100标配）

---

## 10. 常见问题与对策

| 问题 | 症状 | 解决 |
|------|------|------|
| **过拟合** | 训练loss低，验证loss高 | Dropout、数据增强、Early Stopping、减少模型容量 |
| **欠拟合** | 训练loss和验证loss都高 | 增加模型容量、降低正则化、延长训练时间 |
| **梯度消失** | 浅层参数几乎不更新 | ReLU、BatchNorm、残差连接、合适初始化 |
| **梯度爆炸** | loss突然变NaN | 梯度裁剪、降低学习率、合适初始化 |
| **类别不平衡** | 模型偏向多数类 | 加权损失、过采样/欠采样、Focal Loss |

---

## 11. 实战建议

1. **从简单开始**：先用小模型 + 小数据验证pipeline，再逐步扩大规模
2. **先过拟合一个batch**：验证模型能学到东西，排除代码bug
3. **监控训练曲线**：loss曲线、accuracy曲线是调试的第一依据
4. **版本对比**：每次改架构/超参数只改一个变量，方便定位问题
5. **善用预训练**：从HuggingFace或torchvision加载预训练权重，微调比自己从头训练效果好得多
