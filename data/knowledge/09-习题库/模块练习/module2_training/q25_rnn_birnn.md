# 前向和后向使用独立的RNN cell

> 来源模块: module2_training
> 原始文件: q25_rnn_birnn.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】RNN/Bi-RNN：手动实现与PyTorch对比
【模块】模型训练与评估
【难度】6
【知识点】RNN、双向RNN(Bi-RNN)、序列预测、时间步、隐藏状态、梯度裁剪
【描述】
循环神经网络(RNN)是处理序列数据的基础模型。本题要求手动实现RNN和
双向RNN的计算逻辑，然后与PyTorch的nn.RNN进行对比。

RNN核心公式：
  h_t = tanh(W_ih * x_t + b_ih + W_hh * h_{t-1} + b_hh)
  y_t = W_ho * h_t + b_o

Bi-RNN：
  前向: h_t^f = RNN_forward(x_t, h_{t-1}^f)
  后向: h_t^b = RNN_backward(x_t, h_{t+1}^b)
  输出: y_t = concat(h_t^f, h_t^b)

任务：正弦波序列预测 - 给定前20个时间步的sin值，预测后续5个时间步的值

【要求】
1. 手动实现RNNCell类（单步RNN计算单元）
2. 手动实现RNNManual类（多步循环）
3. 手动实现BiRNNManual类（双向RNN）
4. 使用nn.RNN作为基准对比
5. 在正弦波预测任务上训练和对比
6. 绘制预测曲线对比图
7. 打印各模型预测误差(MSE)

【提示】
- 使用nn.Parameter定义可训练权重
- 梯度裁剪防止梯度爆炸: torch.nn.utils.clip_grad_norm_
- Bi-RNN前向和后向使用独立的权重
- 序列预测任务使用MSE损失
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np


# ============ 1. 手动实现RNN Cell ============

class ManualRNNCell(nn.Module):
    """手动实现的单步RNN单元"""

    def __init__(self, input_size, hidden_size):
        super(ManualRNNCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        # 可训练参数
        self.W_ih = nn.Parameter(torch.randn(input_size, hidden_size) * 0.01)
        self.b_ih = nn.Parameter(torch.zeros(hidden_size))
        self.W_hh = nn.Parameter(torch.randn(hidden_size, hidden_size) * 0.01)
        self.b_hh = nn.Parameter(torch.zeros(hidden_size))

    def forward(self, x_t, h_prev):
        """
        x_t: (batch, input_size)
        h_prev: (batch, hidden_size)
        """
        h_t = torch.tanh(
            x_t @ self.W_ih + self.b_ih + h_prev @ self.W_hh + self.b_hh
        )
        return h_t


# ============ 2. 手动实现RNN ============

class ManualRNN(nn.Module):
    """手动实现的多步RNN"""

    def __init__(self, input_size, hidden_size):
        super(ManualRNN, self).__init__()
        self.hidden_size = hidden_size
        self.rnn_cell = ManualRNNCell(input_size, hidden_size)

    def forward(self, x, h_0=None):
        """
        x: (batch, seq_len, input_size)
        返回: outputs (batch, seq_len, hidden_size), h_n (batch, hidden_size)
        """
        batch_size, seq_len, _ = x.size()
        if h_0 is None:
            h_0 = torch.zeros(batch_size, self.hidden_size, device=x.device)

        h_t = h_0
        outputs = []
        for t in range(seq_len):
            h_t = self.rnn_cell(x[:, t, :], h_t)
            outputs.append(h_t)

        outputs = torch.stack(outputs, dim=1)  # (batch, seq_len, hidden_size)
        return outputs, h_t


# ============ 3. 手动实现Bi-RNN ============

class ManualBiRNN(nn.Module):
    """手动实现的双向RNN"""

    def __init__(self, input_size, hidden_size):
        super(ManualBiRNN, self).__init__()
        self.hidden_size = hidden_size
        # 前向和后向使用独立的RNN cell
        self.forward_cell = ManualRNNCell(input_size, hidden_size)
        self.backward_cell = ManualRNNCell(input_size, hidden_size)

    def forward(self, x, h_0_fwd=None, h_0_bwd=None):
        """
        x: (batch, seq_len, input_size)
        返回: outputs (batch, seq_len, 2*hidden_size)
        """
        batch_size, seq_len, _ = x.size()
        device = x.device

        if h_0_fwd is None:
            h_0_fwd = torch.zeros(batch_size, self.hidden_size, device=device)
        if h_0_bwd is None:
            h_0_bwd = torch.zeros(batch_size, self.hidden_size, device=device)

        # 前向
        fwd_outputs = []
        h_t = h_0_fwd
        for t in range(seq_len):
            h_t = self.forward_cell(x[:, t, :], h_t)
            fwd_outputs.append(h_t)

        # 后向
        bwd_outputs = []
        h_t = h_0_bwd
        for t in range(seq_len - 1, -1, -1):
            h_t = self.backward_cell(x[:, t, :], h_t)
            bwd_outputs.insert(0, h_t)

        # 拼接
        outputs = []
        for t in range(seq_len):
            combined = torch.cat([fwd_outputs[t], bwd_outputs[t]], dim=-1)
            outputs.append(combined)

        outputs = torch.stack(outputs, dim=1)  # (batch, seq_len, 2*hidden_size)
        return outputs


# ============ 4. 完整序列预测模型 ============

class SequencePredictor(nn.Module):
    """序列预测模型（使用不同RNN后端）"""

    def __init__(self, input_size, hidden_size, output_size,
                 rnn_type="manual_rnn"):
        super(SequencePredictor, self).__init__()
        self.rnn_type = rnn_type

        if rnn_type == "manual_rnn":
            self.rnn = ManualRNN(input_size, hidden_size)
            fc_input = hidden_size
        elif rnn_type == "manual_birnn":
            self.rnn = ManualBiRNN(input_size, hidden_size)
            fc_input = hidden_size * 2
        elif rnn_type == "pytorch_rnn":
            self.rnn = nn.RNN(input_size, hidden_size, batch_first=True)
            fc_input = hidden_size
        elif rnn_type == "pytorch_birnn":
            self.rnn = nn.RNN(input_size, hidden_size, batch_first=True,
                              bidirectional=True)
            fc_input = hidden_size * 2

        self.fc = nn.Linear(fc_input, output_size)

    def forward(self, x):
        if self.rnn_type in ["manual_rnn", "pytorch_rnn"]:
            if self.rnn_type == "manual_rnn":
                rnn_out, _ = self.rnn(x)
            else:
                rnn_out, _ = self.rnn(x)
            # 取最后一个时间步
            out = self.fc(rnn_out[:, -1, :])
        elif self.rnn_type == "manual_birnn":
            rnn_out = self.rnn(x)
            out = self.fc(rnn_out[:, -1, :])
        elif self.rnn_type == "pytorch_birnn":
            rnn_out, _ = self.rnn(x)
            out = self.fc(rnn_out[:, -1, :])
        return out


# ============ 5. 数据生成 ============

def generate_sine_data(n_samples=200, seq_len=20, pred_len=5):
    """生成正弦波序列预测数据"""
    X = []
    Y = []
    for _ in range(n_samples):
        phase = np.random.uniform(0, 2 * np.pi)
        freq = np.random.uniform(0.5, 1.5)
        t = np.linspace(0, (seq_len + pred_len) * 0.1, seq_len + pred_len)
        signal = np.sin(freq * t + phase)
        X.append(signal[:seq_len].reshape(-1, 1))
        Y.append(signal[seq_len:].reshape(-1))
    return torch.FloatTensor(np.array(X)), torch.FloatTensor(np.array(Y))


def train_model(model, X_train, y_train, X_test, y_test,
                n_epochs=50, lr=0.01, name="Model"):
    """训练模型"""
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    losses = []
    for epoch in range(n_epochs):
        model.train()
        optimizer.zero_grad()
        pred = model(X_train)
        loss = criterion(pred, y_train)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        losses.append(loss.item())

        if (epoch + 1) % 10 == 0:
            model.eval()
            with torch.no_grad():
                test_pred = model(X_test)
                test_mse = criterion(test_pred, y_test).item()
            print(f"  [{name}] Epoch {epoch+1}/{n_epochs} "
                  f"TrainLoss={loss.item():.6f} TestMSE={test_mse:.6f}")

    model.eval()
    with torch.no_grad():
        final_pred = model(X_test)
        final_mse = criterion(final_pred, y_test).item()
    return final_mse, losses


def solve():
    torch.manual_seed(42)
    np.random.seed(42)

    # ---- 1. 生成数据 ----
    X, y = generate_sine_data(n_samples=300, seq_len=20, pred_len=5)
    split = 250
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]
    print(f"训练集: {X_train.shape}, 测试集: {X_test.shape}")

    # ---- 2. 定义模型 ----
    input_size = 1
    hidden_size = 32
    output_size = 5

    models = {
        "Manual RNN": SequencePredictor(input_size, hidden_size, output_size,
                                         "manual_rnn"),
        "PyTorch RNN": SequencePredictor(input_size, hidden_size, output_size,
                                          "pytorch_rnn"),
        "Manual Bi-RNN": SequencePredictor(input_size, hidden_size, output_size,
                                            "manual_birnn"),
        "PyTorch Bi-RNN": SequencePredictor(input_size, hidden_size, output_size,
                                             "pytorch_birnn"),
    }

    # ---- 3. 训练和对比 ----
    print("\n" + "=" * 60)
    results = {}
    for name, model in models.items():
        print(f"\n训练 {name}...")
        mse, losses = train_model(
            model, X_train, y_train, X_test, y_test,
            n_epochs=50, lr=0.01, name=name
        )
        results[name] = {"mse": mse, "losses": losses, "model": model}

    # ---- 4. 结果对比 ----
    print("\n" + "=" * 60)
    print("对比结果")
    print("=" * 60)
    print(f"{'模型':<20} {'测试MSE':>12}")
    print("-" * 34)
    for name, res in results.items():
        print(f"{name:<20} {res['mse']:>12.6f}")

    # ---- 5. 单元测试：验证手动RNN与PyTorch RNN输出是否结构一致 ----
    print("\n" + "=" * 60)
    print("RNN单元验证")
    print("=" * 60)
    with torch.no_grad():
        test_input = torch.randn(1, 20, 1)
        manual_rnn_out, _ = models["Manual RNN"].rnn(test_input)
        pytorch_rnn_out, _ = models["PyTorch RNN"].rnn(test_input)
        print(f"Manual RNN输出形状: {manual_rnn_out.shape}")
        print(f"PyTorch RNN输出形状: {pytorch_rnn_out.shape}")
        print(f"两者输出形状一致: {manual_rnn_out.shape == pytorch_rnn_out.shape}")

    # ---- 6. 预测可视化 ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    sample_idx = 0
    t_input = np.arange(20)
    t_output = np.arange(20, 25)

    for ax, (name, res) in zip(axes.flat, results.items()):
        model = res["model"]
        model.eval()
        with torch.no_grad():
            pred = model(X_test[sample_idx:sample_idx+1]).squeeze().numpy()
        true_input = X_test[sample_idx].squeeze().numpy()
        true_output = y_test[sample_idx].squeeze().numpy()

        ax.plot(t_input, true_input, "b-", label="Input", linewidth=2)
        ax.plot(t_output, true_output, "g-", label="Ground Truth", linewidth=2)
        ax.plot(t_output, pred, "r--", label="Prediction", linewidth=2)
        ax.set_title(name)
        ax.legend(fontsize=8)
        ax.set_xlabel("Time Step")
        ax.set_ylabel("Value")

    plt.tight_layout()
    plt.savefig("q25_rnn_birnn.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图片已保存: q25_rnn_birnn.png")


if __name__ == "__main__":
    solve()

```
