# 随机插入缺失值

> 来源模块: module1_preprocessing
> 原始文件: q04_missing_values.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】缺失值处理：均值/中位数/众数/插值法填充
【模块】数据预处理
【难度】3
【知识点】pandas缺失值处理、均值填充、中位数填充、众数填充、线性插值、sklearn.impute
【描述】
真实数据集中经常存在缺失值（NaN），不同的填充策略适用于不同的场景。
本题创建一个含缺失值的DataFrame，分别用以下方法填充缺失值：
1. 均值填充：用该列均值填充
2. 中位数填充：用该列中位数填充
3. 众数填充：用该列出现频率最高的值填充
4. 线性插值填充：利用前后值进行线性插值

【要求】
1. 创建一个含随机缺失值的DataFrame（至少10行、4列、缺失率约15%）
2. 分别实现四种填充方法，并输出填充结果
3. 计算并对比各方法填充后的数据统计信息（均值、方差）
4. 使用sklearn的SimpleImputer验证均值和中位数填充
5. 分析各方法的优缺点

【提示】
- pandas的fillna()和interpolate()是常用方法
- sklearn的SimpleImputer支持mean/median/most_frequent策略
- 众数可能有多个值，通常取第一个
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer


def create_missing_data(n_rows=15, n_cols=4, missing_rate=0.15, seed=42):
    """
    创建含随机缺失值的DataFrame。

    参数:
        n_rows: 行数
        n_cols: 列数
        missing_rate: 缺失率
        seed: 随机种子

    返回:
        df: 含缺失值的DataFrame
    """
    np.random.seed(seed)
    data = {
        'A': np.random.randn(n_rows) * 10 + 50,      # 正态分布
        'B': np.random.randint(10, 100, n_rows),       # 整数
        'C': np.random.exponential(5, n_rows),          # 指数分布
        'D': np.random.choice([1, 2, 3, 4, 5], n_rows) # 离散值
    }
    df = pd.DataFrame(data)

    # 随机插入缺失值
    mask = np.random.random(df.shape) < missing_rate
    df_missing = df.mask(mask)

    return df_missing, df  # 返回缺失版和原始版


def fill_mean(df):
    """均值填充。"""
    return df.fillna(df.mean(numeric_only=True))


def fill_median(df):
    """中位数填充。"""
    return df.fillna(df.median(numeric_only=True))


def fill_mode(df):
    """众数填充。"""
    result = df.copy()
    for col in result.columns:
        mode_vals = result[col].mode()
        if len(mode_vals) > 0:
            result[col].fillna(mode_vals.iloc[0], inplace=True)
    return result


def fill_interpolate(df):
    """线性插值填充。"""
    return df.interpolate(method='linear').ffill().bfill()


def compare_stats(original, filled_dict):
    """对比各填充方法的统计信息。"""
    print("\n" + "=" * 70)
    print(f"{'方法':<15} {'均值(A)':<10} {'方差(A)':<10} {'均值(B)':<10} {'方差(B)':<10}")
    print("-" * 70)

    print(f"{'原始数据':<15} {original['A'].mean():<10.2f} {original['A'].var():<10.2f}"
          f" {original['B'].mean():<10.2f} {original['B'].var():<10.2f}")

    for name, df in filled_dict.items():
        print(f"{name:<15} {df['A'].mean():<10.2f} {df['A'].var():<10.2f}"
              f" {df['B'].mean():<10.2f} {df['B'].var():<10.2f}")


def solve():
    """主函数：演示四种缺失值填充方法。"""
    # ========== 1. 创建数据 ==========
    df_missing, df_original = create_missing_data()

    print("=== 含缺失值的数据 ===")
    print(df_missing.to_string())
    print(f"\n缺失值统计:\n{df_missing.isnull().sum()}")
    print(f"总缺失值数: {df_missing.isnull().sum().sum()}")
    print(f"缺失率: {df_missing.isnull().mean().mean():.2%}")

    # ========== 2. 四种填充方法 ==========
    df_mean = fill_mean(df_missing.copy())
    df_median = fill_median(df_missing.copy())
    df_mode = fill_mode(df_missing.copy())
    df_interp = fill_interpolate(df_missing.copy())

    print("\n=== 均值填充结果 ===")
    print(df_mean.to_string())

    print("\n=== 中位数填充结果 ===")
    print(df_median.to_string())

    print("\n=== 众数填充结果 ===")
    print(df_mode.to_string())

    print("\n=== 线性插值填充结果 ===")
    print(df_interp.to_string())

    # ========== 3. 统计信息对比 ==========
    filled_dict = {
        '均值填充': df_mean,
        '中位数填充': df_median,
        '众数填充': df_mode,
        '插值填充': df_interp
    }
    compare_stats(df_original, filled_dict)

    # ========== 4. 与sklearn SimpleImputer对比验证 ==========
    print("\n" + "=" * 60)
    print("与sklearn SimpleImputer对比验证")
    print("=" * 60)

    # 均值填充对比
    imputer_mean = SimpleImputer(strategy='mean')
    df_sklearn_mean = pd.DataFrame(
        imputer_mean.fit_transform(df_missing),
        columns=df_missing.columns
    )

    # 中位数填充对比
    imputer_median = SimpleImputer(strategy='median')
    df_sklearn_median = pd.DataFrame(
        imputer_median.fit_transform(df_missing),
        columns=df_missing.columns
    )

    print(f"\n均值填充 - 与sklearn最大差异: "
          f"{np.max(np.abs(df_mean.values - df_sklearn_mean.values)):.2e}")
    print(f"中位数填充 - 与sklearn最大差异: "
          f"{np.max(np.abs(df_median.values - df_sklearn_median.values)):.2e}")

    # ========== 5. 方法优缺点分析 ==========
    print("\n" + "=" * 60)
    print("各填充方法优缺点分析")
    print("=" * 60)
    print("""
均值填充:
  优点 - 简单易用，不改变数据总体均值
  缺点 - 降低了方差，不适合偏态分布

中位数填充:
  优点 - 对异常值鲁棒，适合偏态分布
  缺点 - 仍然降低了方差

众数填充:
  优点 - 适合分类变量，保持值的离散性
  缺点 - 可能引入偏差，不适合连续变量

线性插值填充:
  优点 - 考虑数据时序关系，结果更自然
  缺点 - 要求缺失值前后有数据，首尾缺失值需额外处理
""")


if __name__ == "__main__":
    solve()

```
