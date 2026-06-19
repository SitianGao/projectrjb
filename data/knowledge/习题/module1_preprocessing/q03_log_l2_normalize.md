# 确保非负：若存在负数，平移使最小值为0

> 来源模块: module1_preprocessing
> 原始文件: q03_log_l2_normalize.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】Log/Logistic归一化与L2向量单位化
【模块】数据预处理
【难度】2
【知识点】对数归一化、Logistic归一化、L2归一化、numpy向量运算
【描述】
除了Min-Max和Z-Score，还有其他常用的归一化方法：
1. Log归一化：X_norm = log(1 + X) / log(1 + X_max)，适用于右偏分布
2. Logistic归一化：X_norm = 1 / (1 + exp(-X))，将数据映射到(0, 1)
3. L2归一化：X_norm = X / ||X||_2，将每个样本向量归一化为单位向量

【要求】
1. 手动实现Log归一化，将数据映射到[0, 1]
2. 手动实现Logistic(Sigmoid)归一化，将数据映射到(0, 1)
3. 手动实现L2归一化，使每个样本的L2范数为1
4. 对比归一化前后的数据分布特征（均值、方差、范围）
5. 处理边界情况（零向量、负值等）

【提示】
- Log归一化要求数据非负，需先处理负值
- Logistic归一化不需要数据非负
- L2归一化按行（样本）计算，注意处理零向量
=============================
"""

# ========== 参考答案 ==========

import numpy as np


def log_normalize(X):
    """
    Log归一化：X_norm = log(1 + X) / log(1 + X_max)
    按列归一化到[0, 1]，要求数据非负。

    参数:
        X: numpy数组（非负）

    返回:
        X_norm: 归一化后的数组
    """
    X = np.array(X, dtype=np.float64)

    # 确保非负：若存在负数，平移使最小值为0
    col_min = np.min(X, axis=0)
    if np.any(col_min < 0):
        X = X - col_min + 1e-10  # 避免全零

    col_max = np.max(X, axis=0)
    # 处理最大值为0的情况
    col_max[col_max == 0] = 1.0

    X_norm = np.log(1.0 + X) / np.log(1.0 + col_max)
    return X_norm


def logistic_normalize(X):
    """
    Logistic归一化（Sigmoid变换）：X_norm = 1 / (1 + exp(-X))
    将数据映射到(0, 1)区间。

    参数:
        X: numpy数组

    返回:
        X_norm: 归一化后的数组
    """
    X = np.array(X, dtype=np.float64)
    # 数值稳定性处理，防止exp溢出
    X_norm = 1.0 / (1.0 + np.exp(-X))
    return X_norm


def l2_normalize(X):
    """
    L2归一化：X_norm = X / ||X||_2
    将每个样本（行向量）归一化为单位向量。

    参数:
        X: numpy二维数组，每行一个样本

    返回:
        X_norm: L2归一化后的数组
    """
    X = np.array(X, dtype=np.float64)
    # 计算每行的L2范数
    l2_norms = np.sqrt(np.sum(X ** 2, axis=1, keepdims=True))
    # 处理零向量
    l2_norms[l2_norms == 0] = 1.0
    X_norm = X / l2_norms
    return X_norm


def print_stats(X, name):
    """打印数组的基本统计信息。"""
    print(f"\n--- {name} ---")
    print(f"  均值: {np.round(np.mean(X, axis=0), 4)}")
    print(f"  标准差: {np.round(np.std(X, axis=0), 4)}")
    print(f"  最小值: {np.round(np.min(X, axis=0), 4)}")
    print(f"  最大值: {np.round(np.max(X, axis=0), 4)}")


def solve():
    """主函数：演示三种归一化方法。"""
    np.random.seed(42)

    # ========== 准备数据 ==========
    X = np.random.randint(1, 100, size=(6, 3)).astype(np.float64)
    print("=== 原始数据 ===")
    print(X)
    print_stats(X, "原始数据")

    # ========== 1. Log归一化 ==========
    print("\n" + "=" * 60)
    print("1. Log归一化")
    print("=" * 60)
    X_log = log_normalize(X)
    print(np.round(X_log, 4))
    print_stats(X_log, "Log归一化后")
    print(f"\n范围验证: [{X_log.min():.4f}, {X_log.max():.4f}]")

    # ========== 2. Logistic归一化 ==========
    print("\n" + "=" * 60)
    print("2. Logistic归一化")
    print("=" * 60)
    X_logistic = logistic_normalize(X)
    print(np.round(X_logistic, 4))
    print_stats(X_logistic, "Logistic归一化后")
    print(f"\n范围验证: ({X_logistic.min():.4f}, {X_logistic.max():.4f})")

    # ========== 3. L2归一化 ==========
    print("\n" + "=" * 60)
    print("3. L2归一化")
    print("=" * 60)
    X_l2 = l2_normalize(X)
    print(np.round(X_l2, 4))
    print_stats(X_l2, "L2归一化后")

    # 验证L2范数
    l2_norms = np.sqrt(np.sum(X_l2 ** 2, axis=1))
    print(f"\n各样本L2范数: {np.round(l2_norms, 6)}")
    print("说明: L2归一化后每个样本的L2范数应为1.0")

    # ========== 边界情况测试 ==========
    print("\n" + "=" * 60)
    print("边界情况测试")
    print("=" * 60)

    # 含零向量的情况
    X_edge = np.array([[0, 0, 0], [1, 2, 3], [4, 5, 6]], dtype=np.float64)
    print(f"\n含零向量的数据:\n{X_edge}")
    X_l2_edge = l2_normalize(X_edge)
    print(f"L2归一化后:\n{X_l2_edge}")
    l2_norms_edge = np.sqrt(np.sum(X_l2_edge ** 2, axis=1))
    print(f"L2范数: {l2_norms_edge}")
    print("说明: 零向量归一化后仍为零向量")

    # 含负值的数据测试Log归一化
    X_neg = np.array([[-5, 10], [0, 20], [5, 30]], dtype=np.float64)
    print(f"\n含负值的数据:\n{X_neg}")
    X_log_neg = log_normalize(X_neg)
    print(f"Log归一化后（自动平移）:\n{np.round(X_log_neg, 4)}")

    # ========== 与sklearn normalize对比L2 ==========
    from sklearn.preprocessing import normalize
    X_sklearn_l2 = normalize(X, norm='l2')
    print(f"\n=== L2归一化与sklearn对比 ===")
    print(f"最大绝对误差: {np.max(np.abs(X_l2 - X_sklearn_l2)):.2e}")
    assert np.allclose(X_l2, X_sklearn_l2, atol=1e-10)
    print("验证通过: L2归一化与sklearn结果一致。")


if __name__ == "__main__":
    solve()

```
