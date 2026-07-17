# 从Python列表

> 来源模块: module2_training
> 原始文件: q37_pytorch_basics.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】PyTorch基础
【模块】模型训练与评估
【难度】3
【知识点】PyTorch Tensor操作、自定义Dataset、DataLoader、自动求导、nn.Module
【描述】
学习PyTorch的基础操作，包括Tensor创建与运算、自定义Dataset与DataLoader的实现、
自动求导（autograd）机制，以及使用nn.Module构建简单神经网络。

【要求】
1. 演示Tensor的各种创建方式（from numpy, zeros, ones, randn等）
2. 演示Tensor的基本运算和形状操作（reshape, permute, cat, stack等）
3. 实现自定义Dataset类（继承torch.utils.data.Dataset）
4. 实现DataLoader的使用（batch_size, shuffle, num_workers）
5. 演示autograd自动求导
6. 使用nn.Module构建并训练一个简单的全连接网络

【提示】
- Dataset必须实现__len__和__getitem__方法
- DataLoader负责批次管理和数据加载
- requires_grad=True的Tensor会追踪计算历史用于求导
- nn.Module的forward方法定义前向计算
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
import numpy as np


# ======================== 一、Tensor基础操作 ========================

def demonstrate_tensor_basics():
    """演示Tensor基础操作"""
    print("=" * 60)
    print("一、Tensor 基础操作")
    print("=" * 60)

    # ---- 1. 创建Tensor ----
    print("\n--- 1. 创建Tensor ---")

    # 从Python列表
    t1 = torch.tensor([1, 2, 3, 4, 5])
    print(f"从列表创建: {t1}")

    # 从numpy数组
    arr = np.array([1.0, 2.0, 3.0])
    t2 = torch.from_numpy(arr)
    print(f"从numpy创建: {t2}")

    # 特殊值Tensor
    t_zeros = torch.zeros(3, 4)
    print(f"zeros(3,4) 形状: {t_zeros.shape}")

    t_ones = torch.ones(2, 3)
    print(f"ones(2,3): {t_ones}")

    t_rand = torch.rand(2, 3)
    print(f"rand(2,3): {t_rand}")

    t_randn = torch.randn(2, 3)
    print(f"randn(2,3): {t_randn}")

    t_arange = torch.arange(0, 10, 2)
    print(f"arange(0,10,2): {t_arange}")

    t_linspace = torch.linspace(0, 1, 5)
    print(f"linspace(0,1,5): {t_linspace}")

    # ---- 2. Tensor属性 ----
    print("\n--- 2. Tensor属性 ---")
    t = torch.randn(3, 4, 5)
    print(f"形状: {t.shape}")
    print(f"维度数: {t.dim()}")
    print(f"数据类型: {t.dtype}")
    print(f"设备: {t.device}")
    print(f"元素总数: {t.numel()}")

    # ---- 3. 数据类型转换 ----
    print("\n--- 3. 数据类型转换 ---")
    t_float = torch.randn(3)
    print(f"float32: {t_float.dtype}")
    print(f"float16: {t_float.half().dtype}")
    print(f"int64:   {t_float.long().dtype}")
    print(f"numpy:   {type(t_float.numpy())}")

    # ---- 4. 形状操作 ----
    print("\n--- 4. 形状操作 ---")
    t = torch.arange(12)
    print(f"原始: {t}, 形状: {t.shape}")

    t_reshaped = t.reshape(3, 4)
    print(f"reshape(3,4):\n{t_reshaped}")

    t_view = t.view(2, 6)
    print(f"view(2,6):\n{t_view}")

    t_unsqueeze = t.unsqueeze(0)
    print(f"unsqueeze(0) 形状: {t_unsqueeze.shape}")

    t_squeeze = t_unsqueeze.squeeze()
    print(f"squeeze() 形状: {t_squeeze.shape}")

    # permute
    t_3d = torch.randn(2, 3, 4)
    t_permuted = t_3d.permute(2, 0, 1)
    print(f"permute(2,0,1): {t_3d.shape} -> {t_permuted.shape}")

    # ---- 5. 拼接和堆叠 ----
    print("\n--- 5. 拼接和堆叠 ---")
    a = torch.ones(2, 3)
    b = torch.zeros(2, 3)

    cat_dim0 = torch.cat([a, b], dim=0)
    print(f"cat(dim=0): {cat_dim0.shape}")

    cat_dim1 = torch.cat([a, b], dim=1)
    print(f"cat(dim=1): {cat_dim1.shape}")

    stacked = torch.stack([a, b], dim=0)
    print(f"stack(dim=0): {stacked.shape}")

    # ---- 6. 数学运算 ----
    print("\n--- 6. 数学运算 ---")
    a = torch.tensor([1.0, 2.0, 3.0])
    b = torch.tensor([4.0, 5.0, 6.0])

    print(f"a + b = {a + b}")
    print(f"a * b = {a * b}")  # 逐元素乘法
    print(f"a @ b = {a @ b}")  # 点积
    print(f"a.sum() = {a.sum()}")
    print(f"a.mean() = {a.mean()}")
    print(f"a.max() = {a.max()}")

    # 矩阵乘法
    m1 = torch.randn(2, 3)
    m2 = torch.randn(3, 4)
    result = torch.matmul(m1, m2)
    print(f"matmul: (2,3) @ (3,4) = {result.shape}")

    # ---- 7. 索引和切片 ----
    print("\n--- 7. 索引和切片 ---")
    t = torch.arange(12).reshape(3, 4)
    print(f"Tensor:\n{t}")
    print(f"t[0]: {t[0]}")
    print(f"t[:, 1]: {t[:, 1]}")
    print(f"t[0:2, 1:3]:\n{t[0:2, 1:3]}")
    print(f"t[t > 5]: {t[t > 5]}")

    # GPU
    print(f"\nCUDA是否可用: {torch.cuda.is_available()}")


# ======================== 二、自动求导 Autograd ========================

def demonstrate_autograd():
    """演示自动求导"""
    print("\n" + "=" * 60)
    print("二、自动求导 (Autograd)")
    print("=" * 60)

    # ---- 1. 基本自动求导 ----
    print("\n--- 1. 基本自动求导 ---")
    x = torch.tensor(2.0, requires_grad=True)
    print(f"x = {x}")

    y = x ** 2 + 3 * x + 1
    print(f"y = x^2 + 3x + 1 = {y}")

    y.backward()
    print(f"dy/dx = 2x + 3 = {x.grad}")
    print(f"验证: 2*2 + 3 = {2 * 2 + 3}")

    # ---- 2. 多变量求导 ----
    print("\n--- 2. 多变量求导 ---")
    x = torch.tensor(1.0, requires_grad=True)
    y = torch.tensor(2.0, requires_grad=True)

    z = x ** 2 + y ** 2 + x * y
    print(f"z = x^2 + y^2 + xy = {z}")

    z.backward()
    print(f"dz/dx = 2x + y = {x.grad}")  # 2*1 + 2 = 4
    print(f"dz/dy = 2y + x = {y.grad}")  # 2*2 + 1 = 5

    # ---- 3. 向量求导 ----
    print("\n--- 3. 向量求导 ---")
    x = torch.randn(3, requires_grad=True)
    y = x ** 2
    loss = y.sum()
    loss.backward()
    print(f"x = {x}")
    print(f"loss = sum(x^2)")
    print(f"d(loss)/dx = 2x = {x.grad}")

    # ---- 4. 计算图 ----
    print("\n--- 4. 防止梯度累积 ---")
    x = torch.tensor(3.0, requires_grad=True)

    for i in range(3):
        y = x ** 2
        y.backward()
        print(f"第{i + 1}次 backward: x.grad = {x.grad}")
        x.grad.zero_()  # 清零梯度

    # ---- 5. no_grad上下文 ----
    print("\n--- 5. no_grad上下文 ---")
    x = torch.tensor(2.0, requires_grad=True)
    with torch.no_grad():
        y = x ** 2
        print(f"no_grad下: y.requires_grad = {y.requires_grad}")


# ======================== 三、自定义Dataset与DataLoader ========================

class CustomDataset(Dataset):
    """自定义数据集示例"""

    def __init__(self, features, labels, transform=None):
        """
        Args:
            features: numpy数组或Tensor, 形状(N, feature_dim)
            labels: numpy数组或Tensor, 形状(N,)
            transform: 可选的数据变换函数
        """
        self.features = torch.FloatTensor(features) if not isinstance(features, torch.Tensor) else features
        self.labels = torch.LongTensor(labels) if not isinstance(labels, torch.Tensor) else labels
        self.transform = transform

    def __len__(self):
        """返回数据集大小"""
        return len(self.features)

    def __getitem__(self, idx):
        """根据索引获取单个样本"""
        x = self.features[idx]
        y = self.labels[idx]

        if self.transform:
            x = self.transform(x)

        return x, y

    def get_num_features(self):
        """返回特征维度"""
        return self.features.shape[1]

    def get_num_classes(self):
        """返回类别数"""
        return len(torch.unique(self.labels))


def demonstrate_dataset_dataloader():
    """演示自定义Dataset和DataLoader"""
    print("\n" + "=" * 60)
    print("三、自定义Dataset与DataLoader")
    print("=" * 60)

    # ---- 创建模拟数据 ----
    np.random.seed(42)
    num_samples = 200
    num_features = 10
    num_classes = 3

    # 生成特征
    features = np.random.randn(num_samples, num_features).astype(np.float32)
    # 生成标签（基于特征线性组合 + 噪声）
    weights = np.random.randn(num_features, num_classes)
    logits = features @ weights + np.random.randn(num_samples, num_classes) * 0.1
    labels = logits.argmax(axis=1)

    print(f"数据: {num_samples}个样本, {num_features}个特征, {num_classes}个类别")
    print(f"类别分布: {dict(zip(*np.unique(labels, return_counts=True)))}")

    # ---- 划分训练/测试集 ----
    split = int(0.8 * num_samples)
    train_features, test_features = features[:split], features[split:]
    train_labels, test_labels = labels[:split], labels[split:]

    # ---- 创建Dataset ----
    print("\n--- 创建自定义Dataset ---")
    train_dataset = CustomDataset(train_features, train_labels)
    test_dataset = CustomDataset(test_features, test_labels)

    print(f"训练集大小: {len(train_dataset)}")
    print(f"测试集大小: {len(test_dataset)}")

    # 获取单个样本
    sample_x, sample_y = train_dataset[0]
    print(f"单个样本 - 特征形状: {sample_x.shape}, 标签: {sample_y}")

    # ---- 创建DataLoader ----
    print("\n--- 创建DataLoader ---")
    train_loader = DataLoader(
        train_dataset,
        batch_size=16,
        shuffle=True,
        num_workers=0,
        drop_last=False,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=32,
        shuffle=False,
    )

    # 遍历DataLoader
    print("遍历训练DataLoader:")
    for batch_idx, (batch_x, batch_y) in enumerate(train_loader):
        if batch_idx == 0:
            print(f"  第1个batch - 特征: {batch_x.shape}, 标签: {batch_y.shape}")
        if batch_idx == len(train_loader) - 1:
            print(f"  最后一个batch - 特征: {batch_x.shape}, 标签: {batch_y.shape}")
    print(f"  总batch数: {len(train_loader)}")

    # ---- 使用TensorDataset（快捷方式） ----
    print("\n--- 使用TensorDataset ---")
    tensor_dataset = TensorDataset(
        torch.FloatTensor(train_features),
        torch.LongTensor(train_labels),
    )
    print(f"TensorDataset大小: {len(tensor_dataset)}")
    sample = tensor_dataset[0]
    print(f"样本: 特征形状={sample[0].shape}, 标签={sample[1]}")

    return train_loader, test_loader, num_features, num_classes


# ======================== 四、nn.Module 简单神经网络 ========================

class SimpleNet(nn.Module):
    """简单的全连接神经网络"""

    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, output_dim)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def demonstrate_nn_module(train_loader, test_loader, num_features, num_classes):
    """演示nn.Module训练"""
    print("\n" + "=" * 60)
    print("四、nn.Module 训练简单神经网络")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ---- 构建模型 ----
    model = SimpleNet(
        input_dim=num_features,
        hidden_dim=32,
        output_dim=num_classes,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n模型结构:\n{model}")
    print(f"总参数量: {total_params}")

    # ---- 损失函数和优化器 ----
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    # ---- 训练 ----
    print("\n训练过程:")
    print("-" * 50)

    num_epochs = 20
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)

            # 前向传播
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)

            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * batch_x.size(0)
            _, predicted = outputs.max(1)
            total += batch_y.size(0)
            correct += predicted.eq(batch_y).sum().item()

        train_acc = correct / total
        avg_loss = total_loss / total

        # 测试
        model.eval()
        test_correct = 0
        test_total = 0
        with torch.no_grad():
            for batch_x, batch_y in test_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                _, predicted = outputs.max(1)
                test_total += batch_y.size(0)
                test_correct += predicted.eq(batch_y).sum().item()

        test_acc = test_correct / test_total

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(
                f"Epoch [{epoch + 1:2d}/{num_epochs}] "
                f"Loss: {avg_loss:.4f} "
                f"Train Acc: {train_acc:.4f} "
                f"Test Acc: {test_acc:.4f}"
            )

    print("-" * 50)
    print(f"最终测试准确率: {test_acc:.4f}")

    # ---- 保存和加载模型 ----
    print("\n--- 模型保存与加载 ---")
    import tempfile
    import os

    save_dir = tempfile.mkdtemp()
    model_path = os.path.join(save_dir, "simple_net.pth")

    # 保存
    torch.save(model.state_dict(), model_path)
    print(f"模型参数已保存: {model_path}")

    # 加载
    loaded_model = SimpleNet(num_features, 32, num_classes).to(device)
    loaded_model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    loaded_model.eval()
    print("模型参数已加载")

    # 验证一致性
    model.eval()
    test_input = torch.randn(1, num_features).to(device)
    with torch.no_grad():
        original_output = model(test_input)
        loaded_output = loaded_model(test_input)
    consistent = torch.allclose(original_output, loaded_output)
    print(f"加载后输出一致性: {consistent}")

    # 清理
    os.remove(model_path)
    os.rmdir(save_dir)


# ======================== 主函数 ========================

def solve():
    """PyTorch基础完整演示"""
    print("=" * 60)
    print("PyTorch 基础操作演示")
    print("=" * 60)

    # 一、Tensor基础
    demonstrate_tensor_basics()

    # 二、自动求导
    demonstrate_autograd()

    # 三、Dataset与DataLoader
    train_loader, test_loader, num_features, num_classes = demonstrate_dataset_dataloader()

    # 四、nn.Module
    demonstrate_nn_module(train_loader, test_loader, num_features, num_classes)

    print("\n" + "=" * 60)
    print("PyTorch基础演示完成。")
    print("=" * 60)


if __name__ == "__main__":
    solve()

```
