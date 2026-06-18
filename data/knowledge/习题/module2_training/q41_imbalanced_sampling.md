# 需要补充的样本数

> 来源模块: module2_training
> 原始文件: q41_imbalanced_sampling.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】不均衡数据采样方法实践
【模块】模块2 - 模型训练
【难度】5
【知识点】随机过采样、随机欠采样、WeightedRandomSampler、类别不均衡处理、
          采样效果对比、混淆矩阵分析
【描述】
在现实场景中，数据往往存在类别不均衡问题。本题要求实现多种采样策略来处理不均衡数据，
并对比采样前后的分类效果。

需要实现的方法：
1. 随机过采样（Random Oversampling）：对少数类复制样本
2. 随机欠采样（Random Undersampling）：随机删除多数类样本
3. WeightedRandomSampler：PyTorch的加权随机采样器
4. 类别权重损失：在损失函数中对少数类赋予更高权重

使用sklearn生成不均衡数据集（正负样本比约1:9），用简单的全连接网络训练，
对比不同采样策略的效果。

【输入输出】
- 输入：sklearn生成的不均衡二分类数据集，正:负 ≈ 1:9
- 输出：打印每种采样策略的训练结果和对比分析

【要求】
1. 手动实现随机过采样和随机欠采样（不使用imbalanced-learn库）
2. 实现PyTorch的WeightedRandomSampler配置
3. 实现类别权重损失（class_weight）
4. 训练10个epoch，对比各方法的accuracy、precision、recall、F1
5. 重点关注少数类（正样本）的recall提升效果
6. 输出对比表格

【提示】
- 过采样可能导致过拟合，欠采样可能丢失信息
- WeightedRandomSampler的weights与样本频率成反比
- 类别权重 = n_samples / (n_classes * class_count)
- 评估时使用原始（未采样）的测试集
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


# ==================== 网络定义 ====================

class SimpleNet(nn.Module):
    """简单全连接网络"""

    def __init__(self, input_dim=20):
        super(SimpleNet, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
        )

    def forward(self, x):
        return self.net(x)


# ==================== 采样方法 ====================

def random_oversample(X, y, random_state=42):
    """手动实现随机过采样

    对少数类随机复制样本，使两类样本数相等。

    Args:
        X: 特征矩阵 (N, D)
        y: 标签 (N,)

    Returns:
        X_resampled, y_resampled: 重采样后的数据
    """
    rng = np.random.RandomState(random_state)
    classes, counts = np.unique(y, return_counts=True)
    max_count = counts.max()

    X_list = [X]
    y_list = [y]

    for cls in classes:
        cls_count = counts[classes == cls][0]
        if cls_count < max_count:
            # 需要补充的样本数
            n_needed = max_count - cls_count
            # 从该类中随机采样（有放回）
            cls_indices = np.where(y == cls)[0]
            sampled_indices = rng.choice(cls_indices, size=n_needed, replace=True)
            X_list.append(X[sampled_indices])
            y_list.append(y[sampled_indices])

    X_resampled = np.concatenate(X_list, axis=0)
    y_resampled = np.concatenate(y_list, axis=0)

    # 打乱顺序
    shuffle_idx = rng.permutation(len(y_resampled))
    return X_resampled[shuffle_idx], y_resampled[shuffle_idx]


def random_undersample(X, y, random_state=42):
    """手动实现随机欠采样

    随机删除多数类样本，使两类样本数相等。

    Args:
        X: 特征矩阵 (N, D)
        y: 标签 (N,)

    Returns:
        X_resampled, y_resampled: 重采样后的数据
    """
    rng = np.random.RandomState(random_state)
    classes, counts = np.unique(y, return_counts=True)
    min_count = counts.min()

    X_list = []
    y_list = []

    for cls in classes:
        cls_indices = np.where(y == cls)[0]
        # 随机选取min_count个样本（无放回）
        sampled_indices = rng.choice(cls_indices, size=min_count, replace=False)
        X_list.append(X[sampled_indices])
        y_list.append(y[sampled_indices])

    X_resampled = np.concatenate(X_list, axis=0)
    y_resampled = np.concatenate(y_list, axis=0)

    shuffle_idx = rng.permutation(len(y_resampled))
    return X_resampled[shuffle_idx], y_resampled[shuffle_idx]


def create_weighted_sampler(y):
    """创建WeightedRandomSampler

    为每个样本分配权重，权重与类别频率成反比。

    Args:
        y: 标签数组

    Returns:
        WeightedRandomSampler实例
    """
    classes, counts = np.unique(y, return_counts=True)
    class_weights = {cls: len(y) / (len(classes) * count) for cls, count in zip(classes, counts)}

    # 每个样本的权重
    sample_weights = np.array([class_weights[label] for label in y])
    sample_weights = torch.DoubleTensor(sample_weights)

    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(y),
        replacement=True
    )
    return sampler


def compute_class_weights(y):
    """计算类别权重用于损失函数

    weight_i = n_samples / (n_classes * count_i)

    Args:
        y: 标签数组

    Returns:
        torch.FloatTensor: 类别权重张量
    """
    classes, counts = np.unique(y, return_counts=True)
    total = len(y)
    n_classes = len(classes)
    weights = total / (n_classes * counts.astype(float))
    return torch.FloatTensor(weights)


# ==================== 训练与评估 ====================

def train_model(train_loader, class_weights=None, epochs=10, lr=0.001, input_dim=20):
    """训练模型"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SimpleNet(input_dim).to(device)

    if class_weights is not None:
        criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    else:
        criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

    return model


def evaluate_model(model, X_test, y_test):
    """评估模型，返回指标字典"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()
    with torch.no_grad():
        X_t = torch.FloatTensor(X_test).to(device)
        outputs = model(X_t)
        _, predicted = torch.max(outputs, 1)
        y_pred = predicted.cpu().numpy()

    # 手动计算指标
    tp = np.sum((y_test == 1) & (y_pred == 1))
    tn = np.sum((y_test == 0) & (y_pred == 1))  # 这是fp
    fp = tn  # 重命名
    fp = np.sum((y_test == 0) & (y_pred == 1))
    fn = np.sum((y_test == 1) & (y_pred == 0))

    acc = np.mean(y_pred == y_test)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "confusion_matrix": confusion_matrix(y_test, y_pred),
    }


# ==================== 主函数 ====================

def solve():
    # 生成不均衡数据：正:负 ≈ 1:9
    X, y = make_classification(
        n_samples=2000,
        n_features=20,
        n_informative=10,
        n_redundant=5,
        n_classes=2,
        weights=[0.9, 0.1],  # 90%为类别0，10%为类别1
        random_state=42,
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("=" * 70)
    print("【不均衡数据采样方法对比】")
    print("=" * 70)

    # 打印原始数据分布
    unique, counts = np.unique(y_train, return_counts=True)
    print(f"\n原始训练集分布: ", end="")
    for cls, cnt in zip(unique, counts):
        print(f"类别{cls}={cnt}({cnt/len(y_train)*100:.1f}%)  ", end="")
    print(f"\n总样本数: {len(y_train)}")

    results = {}
    batch_size = 32

    # ========== 方法0: 基线（不采样） ==========
    print("\n" + "-" * 50)
    print("[0] 基线：不做任何采样处理")
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train), torch.LongTensor(y_train)
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    model_baseline = train_model(train_loader, epochs=10)
    results["基线(无采样)"] = evaluate_model(model_baseline, X_test, y_test)

    # ========== 方法1: 随机过采样 ==========
    print("[1] 随机过采样（少数类复制到与多数类数量一致）")
    X_over, y_over = random_oversample(X_train, y_train)
    unique_o, counts_o = np.unique(y_over, return_counts=True)
    print(f"  过采样后分布: ", end="")
    for cls, cnt in zip(unique_o, counts_o):
        print(f"类别{cls}={cnt}  ", end="")
    print()

    train_dataset = TensorDataset(
        torch.FloatTensor(X_over), torch.LongTensor(y_over)
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    model_over = train_model(train_loader, epochs=10)
    results["随机过采样"] = evaluate_model(model_over, X_test, y_test)

    # ========== 方法2: 随机欠采样 ==========
    print("[2] 随机欠采样（多数类缩减到与少数类数量一致）")
    X_under, y_under = random_undersample(X_train, y_train)
    unique_u, counts_u = np.unique(y_under, return_counts=True)
    print(f"  欠采样后分布: ", end="")
    for cls, cnt in zip(unique_u, counts_u):
        print(f"类别{cls}={cnt}  ", end="")
    print()

    train_dataset = TensorDataset(
        torch.FloatTensor(X_under), torch.LongTensor(y_under)
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    model_under = train_model(train_loader, epochs=10)
    results["随机欠采样"] = evaluate_model(model_under, X_test, y_test)

    # ========== 方法3: WeightedRandomSampler ==========
    print("[3] WeightedRandomSampler（按类别频率加权采样）")
    sampler = create_weighted_sampler(y_train)
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train), torch.LongTensor(y_train)
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler)
    model_wrs = train_model(train_loader, epochs=10)
    results["WeightedRandomSampler"] = evaluate_model(model_wrs, X_test, y_test)

    # ========== 方法4: 类别权重损失 ==========
    print("[4] 类别权重损失（CrossEntropyLoss + class_weight）")
    cls_weights = compute_class_weights(y_train)
    print(f"  类别权重: {cls_weights.tolist()}")
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train), torch.LongTensor(y_train)
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    model_cw = train_model(train_loader, class_weights=cls_weights, epochs=10)
    results["类别权重损失"] = evaluate_model(model_cw, X_test, y_test)

    # ========== 结果汇总 ==========
    print("\n" + "=" * 70)
    print("【结果对比】")
    print("=" * 70)
    print(f"{'方法':<25} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 70)
    for method, metrics in results.items():
        print(f"{method:<25} {metrics['accuracy']:>10.4f} "
              f"{metrics['precision']:>10.4f} {metrics['recall']:>10.4f} "
              f"{metrics['f1']:>10.4f}")

    print("\n【混淆矩阵对比】")
    for method, metrics in results.items():
        cm = metrics["confusion_matrix"]
        print(f"\n  {method}:")
        print(f"    TN={cm[0,0]:4d}  FP={cm[0,1]:4d}")
        print(f"    FN={cm[1,0]:4d}  TP={cm[1,1]:4d}")

    # 分析结论
    print("\n" + "=" * 70)
    print("【分析结论】")
    print("=" * 70)
    print("1. 基线方法通常整体accuracy较高，但少数类recall很低")
    print("2. 过采样和WeightedRandomSampler能有效提升少数类recall")
    print("3. 欠采样可能损失多数类信息，导致整体accuracy下降")
    print("4. 类别权重损失是一种简单有效的不均衡处理方法")
    print("5. 实际应用中建议综合使用多种方法，根据业务需求选择")


if __name__ == "__main__":
    solve()

```
