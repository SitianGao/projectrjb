# 处理分母为零的情况：当某列所有值相同时，range为0，归一化后设为0

> 来源模块: module1_preprocessing
> 原始文件: q01_minmax_normalization.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】Min-Max归一化实现与验证
【模块】数据预处理
【难度】1
【知识点】Min-Max归一化、numpy数组操作、sklearn.preprocessing.MinMaxScaler
【描述】
Min-Max归一化是最常用的数据标准化方法之一，它将原始数据线性映射到[0,1]区间。
公式为：X_norm = (X - X_min) / (X_max - X_min)

本题要求手动实现Min-Max归一化算法，并与sklearn的MinMaxScaler结果进行对比验证。

【要求】
1. 给定一个numpy二维数组，手动实现Min-Max归一化（映射到[0,1]区间）
2. 使用sklearn的MinMaxScaler对同一数据进行归一化
3. 比较两种方法的结果，输出最大绝对误差
4. 支持对测试数据使用训练集的min/max参数进行转换
5. 处理分母为零的情况（当所有值相同时）

【提示】
- 注意按列（特征维度）计算min和max
- 使用numpy的广播机制实现高效计算
- MinMaxScaler的fit_transform等价于先fit再transform
=============================
"""

# ========== 参考答案 ==========

import numpy as np
from sklearn.preprocessing import MinMaxScaler


def manual_minmax_fit_transform(X_train):
    """
    手动实现Min-Max归一化的fit和transform。
    对每列（特征）独立计算min和max，映射到[0,1]。

    参数:
        X_train: numpy二维数组，训练数据

    返回:
        X_norm: 归一化后的数据
        params: dict，包含每列的min和max，用于后续transform
    """
    X = np.array(X_train, dtype=np.float64)
    col_min = np.min(X, axis=0)
    col_max = np.max(X, axis=0)
    col_range = col_max - col_min

    # 处理分母为零的情况：当某列所有值相同时，range为0，归一化后设为0
    col_range[col_range == 0] = 1.0

    X_norm = (X - col_min) / col_range

    params = {
        'min': col_min,
        'max': col_max,
        'range': col_range
    }
    return X_norm, params


def manual_minmax_transform(X_test, params):
    """
    使用已有参数对测试数据进行Min-Max归一化。

    参数:
        X_test: numpy二维数组，测试数据
        params: dict，fit阶段得到的参数

    返回:
        X_norm: 归一化后的数据
    """
    X = np.array(X_test, dtype=np.float64)
    X_norm = (X - params['min']) / params['range']
    return X_norm


def solve():
    """主函数：演示手动Min-Max归一化并与sklearn对比。"""
    # ========== 1. 准备数据 ==========
    np.random.seed(42)
    X_train = np.random.randint(0, 100, size=(10, 3)).astype(np.float64)
    X_test = np.random.randint(0, 100, size=(3, 3)).astype(np.float64)

    print("=== 原始训练数据 ===")
    print(X_train)
    print("\n=== 原始测试数据 ===")
    print(X_test)

    # ========== 2. 手动实现Min-Max归一化 ==========
    X_train_manual, params = manual_minmax_fit_transform(X_train)
    X_test_manual = manual_minmax_transform(X_test, params)

    print("\n=== 手动实现 - 训练集归一化结果 ===")
    print(np.round(X_train_manual, 4))
    print("\n=== 手动实现 - 测试集归一化结果 ===")
    print(np.round(X_test_manual, 4))

    # ========== 3. sklearn MinMaxScaler ==========
    scaler = MinMaxScaler()
    X_train_sklearn = scaler.fit_transform(X_train)
    X_test_sklearn = scaler.transform(X_test)

    print("\n=== sklearn MinMaxScaler - 训练集归一化结果 ===")
    print(np.round(X_train_sklearn, 4))
    print("\n=== sklearn MinMaxScaler - 测试集归一化结果 ===")
    print(np.round(X_test_sklearn, 4))

    # ========== 4. 对比结果 ==========
    train_diff = np.abs(X_train_manual - X_train_sklearn)
    test_diff = np.abs(X_test_manual - X_test_sklearn)

    print("\n=== 对比结果 ===")
    print(f"训练集最大绝对误差: {np.max(train_diff):.10f}")
    print(f"测试集最大绝对误差: {np.max(test_diff):.10f}")
    print(f"训练集归一化后范围: [{X_train_manual.min():.4f}, {X_train_manual.max():.4f}]")

    # ========== 5. 边界情况测试 ==========
    print("\n=== 边界情况：所有值相同的列 ===")
    X_edge = np.array([[5, 1], [5, 2], [5, 3]], dtype=np.float64)
    X_edge_manual, params_edge = manual_minmax_fit_transform(X_edge)
    print("输入数据:")
    print(X_edge)
    print("归一化结果:")
    print(X_edge_manual)
    print("说明: 第一列所有值相同(5)，归一化后为0；第二列正常归一化。")

    # 验证sklearn处理方式是否一致
    scaler_edge = MinMaxScaler()
    X_edge_sklearn = scaler_edge.fit_transform(X_edge)
    print("sklearn结果:")
    print(X_edge_sklearn)

    assert np.allclose(X_edge_manual, X_edge_sklearn, atol=1e-10), \
        "手动实现与sklearn结果不一致！"
    print("\n验证通过: 手动实现与sklearn结果一致。")


if __name__ == "__main__":
    solve()

```
