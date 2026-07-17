# 获取实际权重（包含mask效果）

> 来源模块: module3_deployment
> 原始文件: q44_pruning.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】模型剪枝：非结构化与通道剪枝
【模块】模块3 - 模型部署
【难度】8
【知识点】非结构化剪枝、通道剪枝、torch.nn.utils.prune、稀疏度计算、
          精度-稀疏度权衡、L1范数剪枝
【描述】
本题要求实现两种模型剪枝方法，并比较剪枝前后的模型精度和稀疏度。

1. 非结构化剪枝（Unstructured Pruning）
   - 使用 torch.nn.utils.prune 实现随机剪枝和L1剪枝
   - 计算各层的稀疏度（零元素占比）

2. 通道剪枝（Channel Pruning）
   - 手动实现基于L1范数的通道剪枝
   - 按卷积/全连接层输出通道的L1范数排序，剪除较弱的通道
   - 重建更小的模型

【输入输出】
- 输入：使用sklearn生成的人工数据集
- 输出：打印剪枝前后的稀疏度、精度对比

【要求】
1. 非结构化剪枝：使用 prune.l1_unstructured 对全连接层进行剪枝
2. 非结构化剪枝：使用 prune.random_unstructured 进行对比
3. 分别测试 20%、50%、80% 的剪枝比例
4. 通道剪枝：实现基于L1范数的全连接层通道（神经元）剪枝
5. 通道剪枝：剪除L1范数最小的20%和50%的输出神经元
6. 输出精度-稀疏度对比表格

【提示】
- torch.nn.utils.prune 会创建 weight_mask 属性
- 使用 prune.remove(model, name) 将剪枝永久化
- 通道剪枝需要重建网络（减少输出维度）
- 全连接层的"通道"即输出神经元
=============================
"""

# ========== 参考答案 ==========

import copy
import numpy as np
import torch
import torch.nn as nn
import torch.nn.utils.prune as prune
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split


# ==================== 模型定义 ====================

class FCNet(nn.Module):
    """全连接网络用于剪枝实验"""

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
    return train_loader, X_test, y_test


def train_original_model(train_loader, input_dim=20, epochs=10):
    """训练原始模型"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = FCNet(input_dim=input_dim).to(device)
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


def evaluate_accuracy(model, X_test, y_test):
    """评估模型准确率"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()
    with torch.no_grad():
        X_t = torch.FloatTensor(X_test).to(device)
        outputs = model(X_t)
        _, predicted = torch.max(outputs, 1)
        acc = (predicted.cpu().numpy() == y_test).mean()
    return acc


# ==================== 非结构化剪枝 ====================

def apply_unstructured_pruning(model, amount=0.5, method="l1"):
    """对模型的所有全连接层应用非结构化剪枝

    Args:
        model: PyTorch模型
        amount: 剪枝比例 (0-1)
        method: 剪枝方法 ("l1" 或 "random")

    Returns:
        model: 剪枝后的模型
    """
    model = copy.deepcopy(model)

    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            if method == "l1":
                prune.l1_unstructured(module, name="weight", amount=amount)
            elif method == "random":
                prune.random_unstructured(module, name="weight", amount=amount)

    return model


def compute_sparsity(model):
    """计算模型的全局稀疏度（零元素占比）"""
    total_params = 0
    zero_params = 0

    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            # 获取实际权重（包含mask效果）
            weight = module.weight
            if hasattr(module, 'weight_mask'):
                weight = weight * module.weight_mask
            total_params += weight.numel()
            zero_params += (weight == 0).sum().item()

    return zero_params / total_params if total_params > 0 else 0.0


def compute_layer_sparsity(model):
    """计算每层的稀疏度"""
    layer_sparsity = {}
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            weight = module.weight
            if hasattr(module, 'weight_mask'):
                weight = weight * module.weight_mask
            total = weight.numel()
            zeros = (weight == 0).sum().item()
            layer_sparsity[name] = zeros / total if total > 0 else 0.0
    return layer_sparsity


def remove_pruning(model):
    """永久化剪枝（移除mask，将零值写入权重）"""
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            try:
                prune.remove(module, "weight")
            except ValueError:
                pass  # 该层未被剪枝
    return model


# ==================== 通道剪枝（手动实现） ====================

def channel_pruning_l1(model, X_test, y_test, prune_ratio=0.2, input_dim=20):
    """基于L1范数的通道（神经元）剪枝

    对每个全连接层，计算每个输出神经元（行）的L1范数，
    剪除L1范数最小的 prune_ratio 比例的神经元，
    然后重建一个更小的网络。

    Args:
        model: 原始模型
        prune_ratio: 剪枝比例
        input_dim: 输入维度

    Returns:
        pruned_model: 剪枝后的新模型
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()

    # 获取原始模型权重
    w1 = model.fc1.weight.data.cpu().numpy()  # (hidden1, input_dim)
    b1 = model.fc1.bias.data.cpu().numpy()    # (hidden1,)
    w2 = model.fc2.weight.data.cpu().numpy()  # (hidden2, hidden1)
    b2 = model.fc2.bias.data.cpu().numpy()    # (hidden2,)
    w3 = model.fc3.weight.data.cpu().numpy()  # (num_classes, hidden2)
    b3 = model.fc3.bias.data.cpu().numpy()    # (num_classes,)

    # ---- 剪枝 fc1 的输出神经元 ----
    l1_norms_fc1 = np.sum(np.abs(w1), axis=1)  # (hidden1,)
    n_keep_fc1 = max(1, int(len(l1_norms_fc1) * (1 - prune_ratio)))
    keep_indices_fc1 = np.argsort(l1_norms_fc1)[-n_keep_fc1:]
    keep_indices_fc1 = np.sort(keep_indices_fc1)

    new_w1 = w1[keep_indices_fc1, :]   # (n_keep_fc1, input_dim)
    new_b1 = b1[keep_indices_fc1]       # (n_keep_fc1,)

    # fc2 的输入维度相应调整
    new_w2 = w2[:, keep_indices_fc1]    # (hidden2, n_keep_fc1)

    # ---- 剪枝 fc2 的输出神经元 ----
    l1_norms_fc2 = np.sum(np.abs(w2), axis=1)  # (hidden2,)
    n_keep_fc2 = max(1, int(len(l1_norms_fc2) * (1 - prune_ratio)))
    keep_indices_fc2 = np.argsort(l1_norms_fc2)[-n_keep_fc2:]
    keep_indices_fc2 = np.sort(keep_indices_fc2)

    new_w2 = new_w2[keep_indices_fc2, :]  # (n_keep_fc2, n_keep_fc1)
    new_b2 = b2[keep_indices_fc2]          # (n_keep_fc2,)

    # fc3 的输入维度相应调整
    new_w3 = w3[:, keep_indices_fc2]  # (num_classes, n_keep_fc2)
    new_b3 = b3

    # ---- 构建剪枝后的模型 ----
    pruned_model = FCNet(
        input_dim=input_dim,
        hidden1=n_keep_fc1,
        hidden2=n_keep_fc2,
        num_classes=2
    ).to(device)

    # 加载剪枝后的权重
    pruned_model.fc1.weight.data = torch.FloatTensor(new_w1).to(device)
    pruned_model.fc1.bias.data = torch.FloatTensor(new_b1).to(device)
    pruned_model.fc2.weight.data = torch.FloatTensor(new_w2).to(device)
    pruned_model.fc2.bias.data = torch.FloatTensor(new_b2).to(device)
    pruned_model.fc3.weight.data = torch.FloatTensor(new_w3).to(device)
    pruned_model.fc3.bias.data = torch.FloatTensor(new_b3).to(device)

    print(f"  通道剪枝比例: {prune_ratio*100:.0f}%")
    print(f"  原始结构: {input_dim} -> {w1.shape[0]} -> {w2.shape[0]} -> 2")
    print(f"  剪枝结构: {input_dim} -> {n_keep_fc1} -> {n_keep_fc2} -> 2")

    # 参数量对比
    orig_params = w1.size + b1.size + w2.size + b2.size + w3.size + b3.size
    pruned_params = new_w1.size + new_b1.size + new_w2.size + new_b2.size + \
                    new_w3.size + new_b3.size
    print(f"  原始参数量: {orig_params}")
    print(f"  剪枝参数量: {pruned_params}")
    print(f"  参数压缩比: {pruned_params/orig_params:.2%}")

    return pruned_model


# ==================== 主函数 ====================

def solve():
    print("=" * 65)
    print("【模型剪枝：非结构化剪枝与通道剪枝】")
    print("=" * 65)

    # 准备数据并训练原始模型
    print("\n[步骤1] 训练原始模型...")
    train_loader, X_test, y_test = prepare_data()
    model = train_original_model(train_loader, epochs=15)
    base_acc = evaluate_accuracy(model, X_test, y_test)
    print(f"  原始模型准确率: {base_acc:.4f}")

    # ========== 非结构化剪枝实验 ==========
    print("\n" + "=" * 65)
    print("[步骤2] 非结构化剪枝实验")
    print("=" * 65)

    results_unstructured = []

    for amount in [0.2, 0.5, 0.8]:
        for method in ["l1", "random"]:
            pruned_model = apply_unstructured_pruning(model, amount=amount, method=method)
            sparsity = compute_sparsity(pruned_model)
            acc = evaluate_accuracy(pruned_model, X_test, y_test)
            results_unstructured.append({
                "method": f"{method.upper()}-{int(amount*100)}%",
                "sparsity": sparsity,
                "accuracy": acc,
                "acc_drop": base_acc - acc,
            })

    print(f"\n{'方法':<15} {'稀疏度':>10} {'准确率':>10} {'精度下降':>10}")
    print("-" * 50)
    for r in results_unstructured:
        print(f"{r['method']:<15} {r['sparsity']:>10.4f} "
              f"{r['accuracy']:>10.4f} {r['acc_drop']:>10.4f}")

    # 每层稀疏度分析（L1-50%为例）
    print("\n[层稀疏度分析] L1剪枝 50%:")
    pruned_50 = apply_unstructured_pruning(model, amount=0.5, method="l1")
    layer_sp = compute_layer_sparsity(pruned_50)
    for name, sp in layer_sp.items():
        print(f"  {name}: {sp:.4f}")

    # 永久化剪枝
    pruned_permanent = remove_pruning(pruned_50)
    perm_acc = evaluate_accuracy(pruned_permanent, X_test, y_test)
    print(f"  永久化后准确率: {perm_acc:.4f}")

    # ========== 通道剪枝实验 ==========
    print("\n" + "=" * 65)
    print("[步骤3] 通道剪枝实验")
    print("=" * 65)

    results_channel = []

    for prune_ratio in [0.2, 0.5]:
        print(f"\n--- 通道剪枝 {int(prune_ratio*100)}% ---")
        pruned_model = channel_pruning_l1(
            model, X_test, y_test, prune_ratio=prune_ratio, input_dim=20
        )
        ch_acc = evaluate_accuracy(pruned_model, X_test, y_test)
        results_channel.append({
            "prune_ratio": prune_ratio,
            "accuracy": ch_acc,
            "acc_drop": base_acc - ch_acc,
        })
        print(f"  剪枝后准确率: {ch_acc:.4f}")
        print(f"  精度下降: {base_acc - ch_acc:.4f}")

    # ========== 汇总对比 ==========
    print("\n" + "=" * 65)
    print("【剪枝结果汇总】")
    print("=" * 65)
    print(f"  原始模型准确率: {base_acc:.4f}")
    print(f"\n  非结构化剪枝:")
    for r in results_unstructured:
        print(f"    {r['method']:<15} 稀疏度={r['sparsity']:.2%}  "
              f"准确率={r['accuracy']:.4f}  下降={r['acc_drop']:.4f}")
    print(f"\n  通道剪枝:")
    for r in results_channel:
        print(f"    {int(r['prune_ratio']*100)}% 剪枝  "
              f"准确率={r['accuracy']:.4f}  下降={r['acc_drop']:.4f}")


if __name__ == "__main__":
    solve()

```
