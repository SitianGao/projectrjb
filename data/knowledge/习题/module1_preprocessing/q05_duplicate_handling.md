# 随机选择一些行作为重复行

> 来源模块: module1_preprocessing
> 原始文件: q05_duplicate_handling.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】重复值检测与处理
【模块】数据预处理
【难度】2
【知识点】pandas重复值检测、duplicated/drop_duplicates、重复值分析
【描述】
数据集中的重复记录可能导致模型训练偏差。本题要求：
1. 生成包含重复行的模拟数据
2. 检测完全重复行和基于关键列的重复行
3. 使用多种策略删除重复行（保留第一个/最后一个）
4. 统计并分析重复值信息

【要求】
1. 创建一个包含至少30行数据的DataFrame，其中约20%为重复行
2. 使用duplicated()检测重复行，输出重复统计信息
3. 使用drop_duplicates()删除重复行，支持keep参数（first/last/False）
4. 支持按指定子集列检测重复
5. 统计删除前后的数据量变化

【提示】
- duplicated()返回布尔Series，标记每行是否为重复行
- drop_duplicates()的keep参数控制保留策略
- subset参数指定只比较特定列
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import pandas as pd


def create_data_with_duplicates(n_rows=30, duplicate_rate=0.2, seed=42):
    """
    创建含重复行的DataFrame。

    参数:
        n_rows: 基础行数
        duplicate_rate: 重复行比例
        seed: 随机种子

    返回:
        df: 含重复行的DataFrame
    """
    np.random.seed(seed)
    n_unique = int(n_rows * (1 - duplicate_rate))
    n_dup = n_rows - n_unique

    # 生成唯一行
    names = [f"用户{i:03d}" for i in range(n_unique)]
    ages = np.random.randint(18, 65, n_unique)
    scores = np.random.randint(0, 100, n_unique)
    cities = np.random.choice(['北京', '上海', '广州', '深圳', '杭州'], n_unique)

    df_unique = pd.DataFrame({
        '姓名': names,
        '年龄': ages,
        '分数': scores,
        '城市': cities
    })

    # 随机选择一些行作为重复行
    dup_indices = np.random.choice(n_unique, size=n_dup, replace=True)
    df_duplicates = df_unique.iloc[dup_indices].copy()

    # 合并并打乱
    df = pd.concat([df_unique, df_duplicates], ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    return df


def detect_duplicates(df, subset=None):
    """
    检测重复行并输出统计信息。

    参数:
        df: DataFrame
        subset: 用于判断重复的列名列表

    返回:
        dup_mask: 布尔Series
    """
    dup_mask = df.duplicated(subset=subset)
    n_dup = dup_mask.sum()
    n_total = len(df)
    n_unique = n_total - n_dup

    print(f"\n--- 重复值检测 {'(基于列: ' + str(subset) + ')' if subset else '(所有列)'} ---")
    print(f"总行数: {n_total}")
    print(f"重复行数: {n_dup}")
    print(f"唯一行数: {n_unique}")
    print(f"重复率: {n_dup / n_total:.2%}")

    if n_dup > 0:
        print(f"\n重复行示例（前5行）:")
        print(df[dup_mask].head().to_string())

    return dup_mask


def remove_duplicates(df, subset=None, keep='first'):
    """
    删除重复行。

    参数:
        df: DataFrame
        subset: 用于判断重复的列名列表
        keep: 保留策略 ('first', 'last', False)

    返回:
        df_clean: 去重后的DataFrame
    """
    df_clean = df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)

    keep_desc = {'first': '保留第一个', 'last': '保留最后一个', False: '不保留'}
    print(f"\n--- 删除重复行 (keep={keep}: {keep_desc.get(keep, keep)}) ---")
    print(f"原始行数: {len(df)}")
    print(f"删除后行数: {len(df_clean)}")
    print(f"删除行数: {len(df) - len(df_clean)}")

    return df_clean


def solve():
    """主函数：演示重复值检测与处理。"""
    # ========== 1. 创建数据 ==========
    df = create_data_with_duplicates()
    print("=== 原始数据（含重复行）===")
    print(df.to_string())
    print(f"\n数据形状: {df.shape}")

    # ========== 2. 检测所有列重复 ==========
    print("\n" + "=" * 60)
    print("检测完全重复行（所有列都相同）")
    print("=" * 60)
    dup_mask = detect_duplicates(df)

    # ========== 3. 按关键列检测重复 ==========
    print("\n" + "=" * 60)
    print("检测基于子集列的重复（按'姓名'列）")
    print("=" * 60)
    dup_mask_subset = detect_duplicates(df, subset=['姓名'])

    # ========== 4. 不同策略删除重复 ==========
    print("\n" + "=" * 60)
    print("策略1: keep='first'（保留第一次出现的行）")
    print("=" * 60)
    df_first = remove_duplicates(df, keep='first')
    print(df_first.to_string())

    print("\n" + "=" * 60)
    print("策略2: keep='last'（保留最后一次出现的行）")
    print("=" * 60)
    df_last = remove_duplicates(df, keep='last')
    print(df_last.to_string())

    print("\n" + "=" * 60)
    print("策略3: keep=False（删除所有重复行）")
    print("=" * 60)
    df_none = remove_duplicates(df, keep=False)
    print(df_none.to_string())

    # ========== 5. 基于子集列去重 ==========
    print("\n" + "=" * 60)
    print("基于'姓名'列去重（保留第一次出现）")
    print("=" * 60)
    df_subset_clean = remove_duplicates(df, subset=['姓名'], keep='first')
    print(df_subset_clean.to_string())

    # ========== 6. 汇总 ==========
    print("\n" + "=" * 60)
    print("汇总统计")
    print("=" * 60)
    print(f"原始数据行数:          {len(df)}")
    print(f"完全去重后(keep=first): {len(df_first)}")
    print(f"完全去重后(keep=last):  {len(df_last)}")
    print(f"完全去重后(keep=False): {len(df_none)}")
    print(f"按姓名去重后:           {len(df_subset_clean)}")


if __name__ == "__main__":
    solve()

```
