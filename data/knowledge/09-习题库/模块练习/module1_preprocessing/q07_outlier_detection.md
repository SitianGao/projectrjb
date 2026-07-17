# 正常数据：多特征

> 来源模块: module1_preprocessing
> 原始文件: q07_outlier_detection.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】异常值检测：IQR方法与Z-Score方法
【模块】数据预处理
【难度】5
【知识点】IQR四分位距法、Z-Score方法、异常值检测与处理、箱线图原理
【描述】
异常值（Outlier）是显著偏离其他观测值的数据点，可能由测量误差或真实极端事件引起。
常用的异常值检测方法包括：
1. IQR方法：基于四分位数，将超出[Q1-1.5*IQR, Q3+1.5*IQR]的点视为异常值
2. Z-Score方法：将Z-Score绝对值超过阈值（通常为2或3）的点视为异常值

【要求】
1. 生成包含正常数据和异常值的模拟数据集
2. 手动实现IQR方法检测异常值
3. 手动实现Z-Score方法检测异常值
4. 对比两种方法的检测结果
5. 实现异常值处理（删除、替换为边界值、替换为中位数）
6. 可选：绘制箱线图辅助分析

【提示】
- IQR = Q3 - Q1，其中Q1是25%分位数，Q3是75%分位数
- Z-Score方法假设数据近似正态分布
- 不同方法可能检测出不同的异常值
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import pandas as pd


def generate_data_with_outliers(n_normal=200, n_outliers=10, seed=42):
    """
    生成含异常值的模拟数据。

    参数:
        n_normal: 正常数据点数
        n_outliers: 异常值数量
        seed: 随机种子

    返回:
        df: 含异常值的DataFrame
        outlier_indices: 异常值的真实索引
    """
    np.random.seed(seed)

    # 正常数据：多特征
    data = {
        'feature_1': np.random.normal(50, 5, n_normal),
        'feature_2': np.random.normal(100, 10, n_normal),
        'feature_3': np.random.normal(30, 3, n_normal)
    }

    # 插入异常值
    outlier_indices = np.random.choice(n_normal, n_outliers, replace=False)
    for col in data:
        for idx in outlier_indices[:n_outliers // 2]:
            # 大幅偏高的异常值
            data[col][idx] += np.random.choice([1, -1]) * np.random.uniform(15, 25)
        for idx in outlier_indices[n_outliers // 2:]:
            # 大幅偏低的异常值
            data[col][idx] += np.random.choice([1, -1]) * np.random.uniform(15, 25)

    df = pd.DataFrame(data)
    return df, sorted(outlier_indices)


def detect_outliers_iqr(df, factor=1.5):
    """
    使用IQR方法检测异常值。

    参数:
        df: DataFrame
        factor: IQR倍数因子（默认1.5，3.0为极端异常值）

    返回:
        outlier_mask: 布尔DataFrame，标记异常值
        bounds: dict，每列的下界和上界
    """
    outlier_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    bounds = {}

    for col in df.columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR

        bounds[col] = {'lower': lower, 'upper': upper, 'Q1': Q1, 'Q3': Q3, 'IQR': IQR}
        outlier_mask[col] = (df[col] < lower) | (df[col] > upper)

    return outlier_mask, bounds


def detect_outliers_zscore(df, threshold=3.0):
    """
    使用Z-Score方法检测异常值。

    参数:
        df: DataFrame
        threshold: Z-Score阈值

    返回:
        outlier_mask: 布尔DataFrame
        zscores: Z-Score DataFrame
    """
    means = df.mean()
    stds = df.std(ddof=0)
    zscores = (df - means) / stds
    outlier_mask = zscores.abs() > threshold

    return outlier_mask, zscores


def handle_outliers_clip(df, outlier_mask):
    """将异常值替换为边界值（Winsorize）。"""
    result = df.copy()
    for col in result.columns:
        col_outliers = outlier_mask[col]
        if col_outliers.any():
            lower = result[~col_outliers][col].min()
            upper = result[~col_outliers][col].max()
            result.loc[result[col] < lower, col] = lower
            result.loc[result[col] > upper, col] = upper
    return result


def handle_outliers_median(df, outlier_mask):
    """将异常值替换为中位数。"""
    result = df.copy()
    for col in result.columns:
        col_outliers = outlier_mask[col]
        if col_outliers.any():
            median_val = result[~col_outliers][col].median()
            result.loc[col_outliers, col] = median_val
    return result


def handle_outliers_remove(df, outlier_mask):
    """删除包含异常值的行。"""
    row_has_outlier = outlier_mask.any(axis=1)
    return df[~row_has_outlier].reset_index(drop=True)


def solve():
    """主函数：演示IQR和Z-Score异常值检测。"""
    # ========== 1. 生成数据 ==========
    df, true_outlier_idx = generate_data_with_outliers()
    print("=== 数据概览 ===")
    print(df.describe())
    print(f"\n已知异常值索引: {true_outlier_idx}")

    # ========== 2. IQR方法检测 ==========
    print("\n" + "=" * 60)
    print("IQR方法检测异常值")
    print("=" * 60)

    iqr_mask, iqr_bounds = detect_outliers_iqr(df, factor=1.5)

    for col in df.columns:
        b = iqr_bounds[col]
        n_out = iqr_mask[col].sum()
        print(f"\n  {col}: Q1={b['Q1']:.2f}, Q3={b['Q3']:.2f}, "
              f"IQR={b['IQR']:.2f}")
        print(f"    边界: [{b['lower']:.2f}, {b['upper']:.2f}]")
        print(f"    检测到异常值数: {n_out}")

    # 任何列为异常的行
    iqr_outlier_rows = iqr_mask.any(axis=1)
    iqr_outlier_indices = df[iqr_outlier_rows].index.tolist()
    print(f"\nIQR方法检测到的异常行索引: {iqr_outlier_indices}")

    # ========== 3. Z-Score方法检测 ==========
    print("\n" + "=" * 60)
    print("Z-Score方法检测异常值")
    print("=" * 60)

    zscore_mask, zscores = detect_outliers_zscore(df, threshold=3.0)

    for col in df.columns:
        n_out = zscore_mask[col].sum()
        print(f"\n  {col}: |Z|>3 的异常值数: {n_out}")
        if n_out > 0:
            outlier_vals = df.loc[zscore_mask[col], col]
            print(f"    异常值: {outlier_vals.values}")

    zscore_outlier_rows = zscore_mask.any(axis=1)
    zscore_outlier_indices = df[zscore_outlier_rows].index.tolist()
    print(f"\nZ-Score方法检测到的异常行索引: {zscore_outlier_indices}")

    # ========== 4. 两种方法对比 ==========
    print("\n" + "=" * 60)
    print("两种方法对比")
    print("=" * 60)

    iqr_set = set(iqr_outlier_indices)
    zs_set = set(zscore_outlier_indices)
    true_set = set(true_outlier_idx)

    print(f"IQR检测到: {len(iqr_set)} 个异常行")
    print(f"Z-Score检测到: {len(zs_set)} 个异常行")
    print(f"两种方法共同检测到: {len(iqr_set & zs_set)} 个")
    print(f"仅IQR检测到: {len(iqr_set - zs_set)} 个")
    print(f"仅Z-Score检测到: {len(zs_set - iqr_set)} 个")

    # ========== 5. 异常值处理 ==========
    print("\n" + "=" * 60)
    print("异常值处理（以IQR方法检测结果为例）")
    print("=" * 60)

    df_clipped = handle_outliers_clip(df, iqr_mask)
    df_median = handle_outliers_median(df, iqr_mask)
    df_removed = handle_outliers_remove(df, iqr_mask)

    print(f"\n原始数据行数: {len(df)}")
    print(f"边界替换后行数: {len(df_clipped)}")
    print(f"中位数替换后行数: {len(df_median)}")
    print(f"删除异常行后行数: {len(df_removed)}")

    print(f"\n处理前 - feature_1 均值: {df['feature_1'].mean():.2f}, "
          f"标准差: {df['feature_1'].std():.2f}")
    print(f"边界替换 - feature_1 均值: {df_clipped['feature_1'].mean():.2f}, "
          f"标准差: {df_clipped['feature_1'].std():.2f}")
    print(f"中位数替换 - feature_1 均值: {df_median['feature_1'].mean():.2f}, "
          f"标准差: {df_median['feature_1'].std():.2f}")
    print(f"删除异常行 - feature_1 均值: {df_removed['feature_1'].mean():.2f}, "
          f"标准差: {df_removed['feature_1'].std():.2f}")


if __name__ == "__main__":
    solve()

```
