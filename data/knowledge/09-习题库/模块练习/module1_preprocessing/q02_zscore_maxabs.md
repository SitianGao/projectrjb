# 处理标准差为零的情况

> 来源模块: module1_preprocessing
> 原始文件: q02_zscore_maxabs.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】Z-Score标准化与MaxAbs标准化
【模块】数据预处理
【难度】2
【知识点】Z-Score标准化、MaxAbs标准化、sklearn.preprocessing.StandardScaler/MaxAbsScaler
【描述】
Z-Score标准化（也叫标准差标准化）将数据转换为均值为0、标准差为1的分布。
公式为：X_norm = (X - mean) / std

MaxAbs标准化将数据除以每列的绝对值最大值，使结果落在[-1, 1]区间。
公式为：X_norm = X / max(|X|)

【要求】
1. 手动实现Z-Score标准化（StandardScaler），并与sklearn对比
2. 手动实现MaxAbs标准化（MaxAbsScaler），并与sklearn对比
3. 处理标准差为零的边界情况
4. 输出标准化后的均值、标准差、最大绝对误差等统计信息

【提示】
- Z-Score中ddof参数影响标准差计算，sklearn默认使用ddof=0（总体标准差）
- MaxAbsScaler不会移动/居中数据，只做缩放
- 注意处理标准差为0的列
=============================
"""

# ========== 参考答案 ==========

import numpy as np
from sklearn.preprocessing import StandardScaler, MaxAbsScaler


def manual_zscore_fit_transform(X_train):
    """
    手动实现Z-Score标准化。

    参数:
        X_train: numpy二维数组

    返回:
        X_norm: 标准化后的数据
        params: dict，包含mean和std
    """
    X = np.array(X_train, dtype=np.float64)
    col_mean = np.mean(X, axis=0)
    col_std = np.std(X, axis=0, ddof=0)  # ddof=0 与 sklearn 一致

    # 处理标准差为零的情况
    col_std[col_std == 0] = 1.0

    X_norm = (X - col_mean) / col_std
    params = {'mean': col_mean, 'std': col_std}
    return X_norm, params


def manual_zscore_transform(X_test, params):
    """使用已有参数对测试数据进行Z-Score标准化。"""
    X = np.array(X_test, dtype=np.float64)
    return (X - params['mean']) / params['std']


def manual_maxabs_fit_transform(X_train):
    """
    手动实现MaxAbs标准化。

    参数:
        X_train: numpy二维数组

    返回:
        X_norm: 标准化后的数据
        params: dict，包含每列的绝对值最大值
    """
    X = np.array(X_train, dtype=np.float64)
    col_maxabs = np.max(np.abs(X), axis=0)

    # 处理最大绝对值为0的情况
    col_maxabs[col_maxabs == 0] = 1.0

    X_norm = X / col_maxabs
    params = {'maxabs': col_maxabs}
    return X_norm, params


def manual_maxabs_transform(X_test, params):
    """使用已有参数对测试数据进行MaxAbs标准化。"""
    X = np.array(X_test, dtype=np.float64)
    return X / params['maxabs']


def solve():
    """主函数：演示手动Z-Score和MaxAbs标准化并与sklearn对比。"""
    np.random.seed(42)

    # ========== 准备数据 ==========
    X_train = np.random.randn(20, 4) * 10 + 50
    X_test = np.random.randn(5, 4) * 10 + 50

    print("=" * 60)
    print("第一部分：Z-Score 标准化")
    print("=" * 60)

    # 手动实现
    X_train_zs_manual, zs_params = manual_zscore_fit_transform(X_train)
    X_test_zs_manual = manual_zscore_transform(X_test, zs_params)

    # sklearn实现
    scaler_zs = StandardScaler()
    X_train_zs_sklearn = scaler_zs.fit_transform(X_train)
    X_test_zs_sklearn = scaler_zs.transform(X_test)

    print(f"\n原始训练集 - 均值: {np.round(np.mean(X_train, axis=0), 2)}")
    print(f"原始训练集 - 标准差: {np.round(np.std(X_train, axis=0, ddof=0), 2)}")
    print(f"\n手动Z-Score后 - 均值: {np.round(np.mean(X_train_zs_manual, axis=0), 10)}")
    print(f"手动Z-Score后 - 标准差: {np.round(np.std(X_train_zs_manual, axis=0, ddof=0), 10)}")
    print(f"\n训练集最大绝对误差: {np.max(np.abs(X_train_zs_manual - X_train_zs_sklearn)):.2e}")
    print(f"测试集最大绝对误差: {np.max(np.abs(X_test_zs_manual - X_test_zs_sklearn)):.2e}")

    print("\n" + "=" * 60)
    print("第二部分：MaxAbs 标准化")
    print("=" * 60)

    # 手动实现
    X_train_ma_manual, ma_params = manual_maxabs_fit_transform(X_train)
    X_test_ma_manual = manual_maxabs_transform(X_test, ma_params)

    # sklearn实现
    scaler_ma = MaxAbsScaler()
    X_train_ma_sklearn = scaler_ma.fit_transform(X_train)
    X_test_ma_sklearn = scaler_ma.transform(X_test)

    print(f"\n原始训练集 - 每列绝对值最大值: {np.round(ma_params['maxabs'], 2)}")
    print(f"手动MaxAbs后 - 每列绝对值最大值: {np.round(np.max(np.abs(X_train_ma_manual), axis=0), 4)}")
    print(f"\n训练集最大绝对误差: {np.max(np.abs(X_train_ma_manual - X_train_ma_sklearn)):.2e}")
    print(f"测试集最大绝对误差: {np.max(np.abs(X_test_ma_manual - X_test_ma_sklearn)):.2e}")

    # ========== 边界情况测试 ==========
    print("\n" + "=" * 60)
    print("第三部分：边界情况测试（含标准差为0的列）")
    print("=" * 60)

    X_edge = np.array([
        [3, 10, 0],
        [3, 20, 0],
        [3, 30, 0],
        [3, 40, 0]
    ], dtype=np.float64)

    X_edge_zs, zs_edge_params = manual_zscore_fit_transform(X_edge)
    X_edge_ma, ma_edge_params = manual_maxabs_fit_transform(X_edge)

    print(f"\n含常数列的数据:\n{X_edge}")
    print(f"\nZ-Score标准化后:\n{X_edge_zs}")
    print(f"说明: 第1列和第3列标准差为0，标准化后保持为0")
    print(f"\nMaxAbs标准化后:\n{X_edge_ma}")

    # 与sklearn对比
    scaler_zs_edge = StandardScaler()
    X_edge_zs_sklearn = scaler_zs_edge.fit_transform(X_edge)
    scaler_ma_edge = MaxAbsScaler()
    X_edge_ma_sklearn = scaler_ma_edge.fit_transform(X_edge)

    assert np.allclose(X_edge_zs, X_edge_zs_sklearn, atol=1e-10)
    assert np.allclose(X_edge_ma, X_edge_ma_sklearn, atol=1e-10)
    print("\n验证通过: 手动实现与sklearn结果一致。")


if __name__ == "__main__":
    solve()

```
