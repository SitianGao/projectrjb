# 校准数据（用于静态量化）

> 来源模块: module3_deployment
> 原始文件: q45_quantization.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】模型量化：动态量化与静态量化
【模块】模块3 - 模型部署
【难度】7
【知识点】PyTorch动态量化、静态量化、INT8校准、量化感知训练(QAT概念)、
          模型大小对比、推理速度对比、精度损失分析
【描述】
本题要求实现PyTorch模型的量化，包括动态量化和静态量化，
并对比量化前后的模型大小、推理速度和精度。

1. 动态量化（Dynamic Quantization）
   - 将全连接层的权重从FP32量化为INT8
   - 激活值在推理时动态量化

2. 静态量化（Static Quantization）
   - 需要校准数据集（calibration dataset）
   - 权重和激活值都预先量化
   - 使用 torch.quantization.prepare 和 convert

3. 量化效果评估
   - 模型文件大小
   - 推理延迟
   - 准确率变化

【输入输出】
- 输入：sklearn生成的人工数据集
- 输出：打印量化前后对比表格（大小、速度、精度）

【要求】
1. 实现动态量化：torch.quantization.quantize_dynamic
2. 实现静态量化：使用torch.quantization.prepare/convert流程
3. 使用校准数据集进行INT8校准
4. 对比FP32/INT8模型文件大小
5. 对比推理延迟（100次平均）
6. 对比准确率变化
7. 输出详细对比表格

【提示】
- 动态量化最简单: torch.quantization.quantize_dynamic(model, {nn.Linear}, dtype=torch.qint8)
- 静态量化需要模型支持量化（使用QuantStub/DeQuantStub）
- 校准时用model.eval()并前向传播若干批数据
- 获取模型大小: os.path.getsize() 或计算参数内存占用
=============================
"""

# ========== 参考答案 ==========

import copy
import io
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.quantization
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split


# ==================== 模型定义 ====================

class FCNet(nn.Module):
    """普通全连接网络（用于动态量化）"""

    def __init__(self, input_dim=20, hidden1=128, hidden2=64, num_classes=2):
        super(FCNet, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden1)
        self.fc2 = nn.Linear(hidden1, hidden2)
        self.fc3 = nn.Linear(hidden2, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class QuantizableFCNet(nn.Module):
    """可量化的全连接网络（用于静态量化）

    需要使用QuantStub和DeQuantStub来标记量化区域的边界。
    """

    def __init__(self, input_dim=20, hidden1=128, hidden2=64, num_classes=2):
        super(QuantizableFCNet, self).__init__()
        self.quant = torch.quantization.QuantStub()
        self.fc1 = nn.Linear(input_dim, hidden1)
        self.fc2 = nn.Linear(hidden1, hidden2)
        self.fc3 = nn.Linear(hidden2, num_classes)
        self.relu = nn.ReLU()
        self.dequant = torch.quantization.DeQuantStub()

    def forward(self, x):
        x = self.quant(x)
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        x = self.dequant(x)
        return x


# ==================== 数据准备 ====================

def prepare_data():
    """生成分类数据"""
    X, y = make_classification(
        n_samples=2000, n_features=20, n_informative=10,
        n_classes=2, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train), torch.LongTensor(y_train)
    )
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

    # 校准数据（用于静态量化）
    cal_dataset = TensorDataset(
        torch.FloatTensor(X_train[:200]),
        torch.LongTensor(y_train[:200]),
    )
    cal_loader = DataLoader(cal_dataset, batch_size=32, shuffle=False)

    return train_loader, cal_loader, X_test, y_test


# ==================== 训练 ====================

def train_model(model, train_loader, epochs=10):
    """训练模型"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(epochs):
        model.train()
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

    return model


# ==================== 评估工具 ====================

def evaluate_accuracy(model, X_test, y_test):
    """评估准确率"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()
    with torch.no_grad():
        X_t = torch.FloatTensor(X_test).to(device)
        outputs = model(X_t)
        _, predicted = torch.max(outputs, 1)
        acc = (predicted.cpu().numpy() == y_test).mean()
    return acc


def measure_inference_time(model, X_test, n_runs=100):
    """测量推理延迟"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()
    X_t = torch.FloatTensor(X_test[:100]).to(device)

    # 预热
    with torch.no_grad():
        for _ in range(10):
            _ = model(X_t)

    # 测量
    start = time.time()
    with torch.no_grad():
        for _ in range(n_runs):
            _ = model(X_t)
    elapsed = (time.time() - start) / n_runs

    return elapsed * 1000  # 转为ms


def get_model_size_mb(model):
    """计算模型大小（MB）"""
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    size_bytes = buffer.getbuffer().nbytes
    return size_bytes / (1024 * 1024)


def get_model_size_on_disk_mb(model, path="/tmp/model_temp.pt"):
    """保存模型到磁盘并获取文件大小"""
    torch.save(model, path)
    size_mb = os.path.getsize(path) / (1024 * 1024)
    os.remove(path)
    return size_mb


# ==================== 动态量化 ====================

def dynamic_quantization(model):
    """动态量化

    仅将nn.Linear层的权重从FP32量化为INT8。
    激活值在推理时动态量化。

    Args:
        model: FP32模型

    Returns:
        quantized_model: 量化后的模型
    """
    model.eval()
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {nn.Linear},           # 量化的层类型
        dtype=torch.qint8,     # 量化数据类型
    )
    return quantized_model


# ==================== 静态量化 ====================

def static_quantization(model, cal_loader):
    """静态量化

    需要校准数据集来收集激活值的统计信息。

    Args:
        model: 可量化的模型（含QuantStub/DeQuantStub）
        cal_loader: 校准数据DataLoader

    Returns:
        quantized_model: 量化后的模型
    """
    model.eval()

    # 设置量化配置
    model.qconfig = torch.quantization.get_default_qconfig('x86')

    # 准备量化（插入观察者）
    torch.quantization.prepare(model, inplace=True)

    # 校准：用校准数据前向传播
    with torch.no_grad():
        for batch_x, _ in cal_loader:
            model(batch_x)

    # 转换为量化模型
    torch.quantization.convert(model, inplace=True)

    return model


# ==================== 主函数 ====================

def solve():
    print("=" * 65)
    print("【模型量化：动态量化与静态量化对比】")
    print("=" * 65)

    # 准备数据
    print("\n[步骤1] 准备数据并训练模型...")
    train_loader, cal_loader, X_test, y_test = prepare_data()

    # 训练FP32模型（用于动态量化）
    model_fp32 = train_model(FCNet(), train_loader, epochs=15)
    # 训练可量化模型（用于静态量化）
    model_quantizable = train_model(QuantizableFCNet(), train_loader, epochs=15)

    # 基线评估
    base_acc = evaluate_accuracy(model_fp32, X_test, y_test)
    base_size = get_model_size_mb(model_fp32)
    base_time = measure_inference_time(model_fp32, X_test)

    print(f"  FP32模型准确率: {base_acc:.4f}")
    print(f"  FP32模型大小: {base_size:.4f} MB")
    print(f"  FP32推理延迟: {base_time:.3f} ms")

    # ========== 动态量化 ==========
    print("\n" + "-" * 50)
    print("[步骤2] 动态量化 (Dynamic Quantization)")
    print("-" * 50)

    model_dynamic = dynamic_quantization(copy.deepcopy(model_fp32))
    dynamic_acc = evaluate_accuracy(model_dynamic, X_test, y_test)
    dynamic_size = get_model_size_mb(model_dynamic)
    dynamic_time = measure_inference_time(model_dynamic, X_test)

    print(f"  动态量化准确率: {dynamic_acc:.4f}")
    print(f"  动态量化模型大小: {dynamic_size:.4f} MB")
    print(f"  动态量化推理延迟: {dynamic_time:.3f} ms")
    print(f"  模型大小压缩比: {dynamic_size/base_size:.2%}")

    # 打印量化后的权重信息
    print("\n  量化后各层信息:")
    for name, module in model_dynamic.named_modules():
        if hasattr(module, 'weight'):
            if hasattr(module.weight(), 'dtype') if callable(module.weight) else False:
                print(f"    {name}: weight dtype = INT8")
            else:
                w = module.weight
                if callable(w):
                    w = w()
                print(f"    {name}: weight shape = {w.shape}")

    # ========== 静态量化 ==========
    print("\n" + "-" * 50)
    print("[步骤3] 静态量化 (Static Quantization)")
    print("-" * 50)

    model_static = copy.deepcopy(model_quantizable)
    model_static = static_quantization(model_static, cal_loader)

    static_acc = evaluate_accuracy(model_static, X_test, y_test)
    static_size = get_model_size_mb(model_static)
    static_time = measure_inference_time(model_static, X_test)

    print(f"  静态量化准确率: {static_acc:.4f}")
    print(f"  静态量化模型大小: {static_size:.4f} MB")
    print(f"  静态量化推理延迟: {static_time:.3f} ms")

    # ========== 汇总对比 ==========
    print("\n" + "=" * 65)
    print("【量化结果汇总对比】")
    print("=" * 65)
    print(f"{'模型':<20} {'准确率':>10} {'大小(MB)':>12} "
          f"{'延迟(ms)':>12} {'大小压缩':>10} {'精度下降':>10}")
    print("-" * 75)

    results = [
        ("FP32 (原始)", base_acc, base_size, base_time, "-", "-"),
        ("INT8 (动态量化)", dynamic_acc, dynamic_size, dynamic_time,
         f"{dynamic_size/base_size:.2%}", f"{base_acc-dynamic_acc:.4f}"),
        ("INT8 (静态量化)", static_acc, static_size, static_time,
         f"{static_size/base_size:.2%}", f"{base_acc-static_acc:.4f}"),
    ]

    for name, acc, size, latency, compress, drop in results:
        print(f"{name:<20} {acc:>10.4f} {size:>12.4f} "
              f"{latency:>12.3f} {compress:>10} {drop:>10}")

    print("\n【结论】")
    print("1. 动态量化：实现简单，仅量化权重，适合全连接层和RNN")
    print("2. 静态量化：需要校准数据，权重和激活都量化，推理更快")
    print("3. 量化后模型大小显著减小（约2-4倍）")
    print("4. 量化精度损失通常很小（<1%）")


if __name__ == "__main__":
    solve()

```
