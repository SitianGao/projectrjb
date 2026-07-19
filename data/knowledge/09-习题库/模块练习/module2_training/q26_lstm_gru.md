# 合并的权重矩阵 (4 * hidden_size 对应 f, i, g, o)

> 来源模块: module2_training
> 原始文件: q26_lstm_gru.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】LSTM/GRU文本情感分类：PyTorch实现
【模块】模型训练与评估
【难度】7
【知识点】LSTM、GRU、门控机制、文本分类、词嵌入、情感分析、PyTorch
【描述】
LSTM(Long Short-Term Memory)和GRU(Gated Recurrent Unit)是解决标准RNN
梯度消失问题的两种经典门控循环单元。

LSTM核心公式：
  遗忘门: f_t = sigma(W_f * [h_{t-1}, x_t] + b_f)
  输入门: i_t = sigma(W_i * [h_{t-1}, x_t] + b_i)
  候选值: g_t = tanh(W_g * [h_{t-1}, x_t] + b_g)
  细胞态: C_t = f_t * C_{t-1} + i_t * g_t
  输出门: o_t = sigma(W_o * [h_{t-1}, x_t] + b_o)
  隐藏态: h_t = o_t * tanh(C_t)

GRU核心公式：
  重置门: r_t = sigma(W_r * [h_{t-1}, x_t])
  更新门: z_t = sigma(W_z * [h_{t-1}, x_t])
  候选值: n_t = tanh(W_n * [r_t * h_{t-1}, x_t])
  隐藏态: h_t = (1 - z_t) * h_{t-1} + z_t * n_t

本题要求手动实现LSTM和GRU，并在文本情感分类任务上与PyTorch内置实现对比。

【要求】
1. 手动实现LSTMCell类（遗忘门、输入门、输出门、细胞状态）
2. 手动实现GRUCell类（重置门、更新门）
3. 基于手动Cell构建完整LSTM和GRU模型用于文本分类
4. 使用PyTorch内置nn.LSTM和nn.GRU作为基准
5. 构建简单的情感分类数据集（模拟数据）
6. 训练所有模型，对比精度和训练损失
7. 绘制训练损失曲线

【提示】
- 文本分类流程: Embedding -> LSTM/GRU -> 取最后隐藏态 -> FC -> 分类
- 使用nn.Embedding进行词嵌入
- LSTM需要维护细胞状态C和隐藏状态h
- GRU比LSTM参数更少，只有两个门
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np


# ============ 1. 手动实现LSTM Cell ============

class ManualLSTMCell(nn.Module):
    """手动实现的LSTM单元"""

    def __init__(self, input_size, hidden_size):
        super(ManualLSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        # 合并的权重矩阵 (4 * hidden_size 对应 f, i, g, o)
        self.W_ih = nn.Parameter(torch.randn(input_size, 4 * hidden_size) * 0.01)
        self.W_hh = nn.Parameter(torch.randn(hidden_size, 4 * hidden_size) * 0.01)
        self.bias_ih = nn.Parameter(torch.zeros(4 * hidden_size))
        self.bias_hh = nn.Parameter(torch.zeros(4 * hidden_size))

    def forward(self, x_t, h_prev, c_prev):
        """
        x_t: (batch, input_size)
        h_prev: (batch, hidden_size)
        c_prev: (batch, hidden_size)
        返回: h_t, c_t
        """
        gates = x_t @ self.W_ih + self.bias_ih + h_prev @ self.W_hh + self.bias_hh

        # 分割为四个门
        f, i, g, o = gates.chunk(4, dim=-1)

        f_t = torch.sigmoid(f)  # 遗忘门
        i_t = torch.sigmoid(i)  # 输入门
        g_t = torch.tanh(g)     # 候选值
        o_t = torch.sigmoid(o)  # 输出门

        c_t = f_t * c_prev + i_t * g_t  # 细胞状态
        h_t = o_t * torch.tanh(c_t)     # 隐藏状态

        return h_t, c_t


# ============ 2. 手动实现GRU Cell ============

class ManualGRUCell(nn.Module):
    """手动实现的GRU单元"""

    def __init__(self, input_size, hidden_size):
        super(ManualGRUCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        # 重置门和更新门 (2 * hidden_size 对应 r, z)
        self.W_ih_rz = nn.Parameter(torch.randn(input_size, 2 * hidden_size) * 0.01)
        self.W_hh_rz = nn.Parameter(torch.randn(hidden_size, 2 * hidden_size) * 0.01)
        self.bias_rz = nn.Parameter(torch.zeros(2 * hidden_size))

        # 候选值
        self.W_ih_n = nn.Parameter(torch.randn(input_size, hidden_size) * 0.01)
        self.W_hh_n = nn.Parameter(torch.randn(hidden_size, hidden_size) * 0.01)
        self.bias_n = nn.Parameter(torch.zeros(hidden_size))

    def forward(self, x_t, h_prev):
        """
        x_t: (batch, input_size)
        h_prev: (batch, hidden_size)
        返回: h_t
        """
        # 重置门和更新门
        rz = x_t @ self.W_ih_rz + self.bias_rz + h_prev @ self.W_hh_rz
        r_t, z_t = rz.chunk(2, dim=-1)
        r_t = torch.sigmoid(r_t)  # 重置门
        z_t = torch.sigmoid(z_t)  # 更新门

        # 候选值
        n_t = torch.tanh(
            x_t @ self.W_ih_n + self.bias_n + (r_t * h_prev) @ self.W_hh_n
        )

        # 最终隐藏状态
        h_t = (1 - z_t) * h_prev + z_t * n_t
        return h_t


# ============ 3. 基于手动Cell的文本分类模型 ============

class ManualLSTMClassifier(nn.Module):
    """基于手动LSTM的文本分类模型"""

    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes):
        super(ManualLSTMClassifier, self).__init__()
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm_cell = ManualLSTMCell(embed_dim, hidden_size)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        """
        x: (batch, seq_len) 整数token序列
        """
        batch_size, seq_len = x.size()
        embedded = self.embedding(x)  # (batch, seq_len, embed_dim)

        h_t = torch.zeros(batch_size, self.hidden_size, device=x.device)
        c_t = torch.zeros(batch_size, self.hidden_size, device=x.device)

        for t in range(seq_len):
            h_t, c_t = self.lstm_cell(embedded[:, t, :], h_t, c_t)

        out = self.fc(h_t)  # 使用最后隐藏状态分类
        return out


class ManualGRUClassifier(nn.Module):
    """基于手动GRU的文本分类模型"""

    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes):
        super(ManualGRUClassifier, self).__init__()
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.gru_cell = ManualGRUCell(embed_dim, hidden_size)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        batch_size, seq_len = x.size()
        embedded = self.embedding(x)

        h_t = torch.zeros(batch_size, self.hidden_size, device=x.device)

        for t in range(seq_len):
            h_t = self.gru_cell(embedded[:, t, :], h_t)

        out = self.fc(h_t)
        return out


# ============ 4. PyTorch内置LSTM/GRU分类模型 ============

class PytorchLSTMClassifier(nn.Module):
    """基于PyTorch内置LSTM的文本分类模型"""

    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes):
        super(PytorchLSTMClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        embedded = self.embedding(x)
        _, (h_n, _) = self.lstm(embedded)
        out = self.fc(h_n.squeeze(0))
        return out


class PytorchGRUClassifier(nn.Module):
    """基于PyTorch内置GRU的文本分类模型"""

    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes):
        super(PytorchGRUClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.gru = nn.GRU(embed_dim, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        embedded = self.embedding(x)
        _, h_n = self.gru(embedded)
        out = self.fc(h_n.squeeze(0))
        return out


# ============ 5. 数据生成 ============

def generate_sentiment_data(n_samples=500, seq_len=15, vocab_size=200):
    """生成模拟情感分类数据"""
    # 正面词汇: 0-49, 负面词汇: 50-99, 中性词汇: 100-199
    np.random.seed(42)
    X = []
    y = []

    for _ in range(n_samples):
        label = np.random.randint(0, 2)  # 0=负面, 1=正面
        sentence = []
        for _ in range(seq_len):
            if label == 1:  # 正面
                word = np.random.choice(
                    list(range(0, 50)) * 3 + list(range(100, 200))
                )
            else:  # 负面
                word = np.random.choice(
                    list(range(50, 100)) * 3 + list(range(100, 200))
                )
            sentence.append(word)
        X.append(sentence)
        y.append(label)

    return torch.LongTensor(X), torch.LongTensor(y)


def train_and_eval(model, X_train, y_train, X_test, y_test,
                   n_epochs=30, lr=0.005, name="Model"):
    """训练和评估"""
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    losses = []

    for epoch in range(n_epochs):
        model.train()
        optimizer.zero_grad()
        output = model(X_train)
        loss = criterion(output, y_train)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        losses.append(loss.item())

    # 评估
    model.eval()
    with torch.no_grad():
        pred = model(X_test).argmax(dim=1)
        acc = (pred == y_test).float().mean().item()
    return acc, losses


def solve():
    torch.manual_seed(42)
    np.random.seed(42)

    # ---- 1. 数据准备 ----
    vocab_size = 200
    embed_dim = 32
    hidden_size = 64
    num_classes = 2
    seq_len = 15

    X, y = generate_sentiment_data(n_samples=500, seq_len=seq_len,
                                    vocab_size=vocab_size)
    split = 400
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]
    print(f"训练集: {X_train.shape}, 测试集: {X_test.shape}")
    print(f"正面样本比例: {y_train.float().mean():.2f}")

    # ---- 2. 创建模型 ----
    models = {
        "手动LSTM": ManualLSTMClassifier(vocab_size, embed_dim,
                                             hidden_size, num_classes),
        "手动GRU": ManualGRUClassifier(vocab_size, embed_dim,
                                           hidden_size, num_classes),
        "PyTorch LSTM": PytorchLSTMClassifier(vocab_size, embed_dim,
                                               hidden_size, num_classes),
        "PyTorch GRU": PytorchGRUClassifier(vocab_size, embed_dim,
                                             hidden_size, num_classes),
    }

    # ---- 3. 训练与评估 ----
    print("\n" + "=" * 60)
    print("训练模型...")
    print("=" * 60)
    results = {}
    for name, model in models.items():
        print(f"\n训练 {name}...")
        acc, losses = train_and_eval(
            model, X_train, y_train, X_test, y_test,
            n_epochs=30, lr=0.005, name=name
        )
        results[name] = {"acc": acc, "losses": losses, "model": model}
        print(f"  测试精度: {acc:.4f}")

    # ---- 4. 结果对比 ----
    print("\n" + "=" * 60)
    print("对比结果")
    print("=" * 60)
    print(f"{'模型':<18} {'参数量':>10} {'测试精度':>10}")
    print("-" * 40)
    for name, res in results.items():
        n_params = sum(p.numel() for p in res["model"].parameters())
        print(f"{name:<18} {n_params:>10,} {res['acc']:>10.4f}")

    # ---- 5. 绘图 ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 损失曲线
    for name, res in results.items():
        ax1.plot(res["losses"], label=name, linewidth=1.5)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("损失")
    ax1.set_title("训练损失")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 精度柱状图
    names = list(results.keys())
    accs = [results[n]["acc"] for n in names]
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    bars = ax2.bar(names, accs, color=colors[:len(names)], alpha=0.8)
    ax2.set_ylabel("测试精度")
    ax2.set_title("测试精度对比")
    ax2.set_ylim(0, 1.0)
    ax2.grid(True, alpha=0.3, axis="y")
    for bar, acc in zip(bars, accs):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                 f"{acc:.3f}", ha="center", va="bottom", fontsize=10)
    ax2.tick_params(axis="x", rotation=15)

    plt.tight_layout()
    plt.savefig("q26_lstm_gru.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图片已保存: q26_lstm_gru.png")

    # ---- 6. 验证手动LSTM Cell正确性 ----
    print("\n" + "=" * 60)
    print("LSTM Cell 验证")
    print("=" * 60)
    manual_cell = ManualLSTMCell(embed_dim, hidden_size)
    pytorch_cell = nn.LSTMCell(embed_dim, hidden_size)

    # 复制权重使两者一致
    with torch.no_grad():
        pytorch_cell.weight_ih.copy_(manual_cell.W_ih.t())
        pytorch_cell.weight_hh.copy_(manual_cell.W_hh.t())
        pytorch_cell.bias_ih.copy_(manual_cell.bias_ih + manual_cell.bias_hh)
        pytorch_cell.bias_hh.zero_()

    test_x = torch.randn(2, embed_dim)
    test_h = torch.zeros(2, hidden_size)
    test_c = torch.zeros(2, hidden_size)

    h_manual, c_manual = manual_cell(test_x, test_h, test_c)
    h_pytorch, c_pytorch = pytorch_cell(test_x, (test_h, test_c))

    h_diff = (h_manual - h_pytorch).abs().max().item()
    c_diff = (c_manual - c_pytorch).abs().max().item()
    print(f"隐藏状态最大差异: {h_diff:.8f}")
    print(f"细胞状态最大差异: {c_diff:.8f}")
    print(f"验证通过: {'是' if h_diff < 1e-5 and c_diff < 1e-5 else '否'}")


if __name__ == "__main__":
    solve()

```
