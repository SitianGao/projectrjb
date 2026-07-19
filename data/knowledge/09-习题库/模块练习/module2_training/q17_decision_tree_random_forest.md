# 子图1: 精度-深度曲线

> 来源模块: module2_training
> 原始文件: q17_decision_tree_random_forest.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】决策树与随机森林：分类与特征重要性分析
【模块】模型训练与评估
【难度】4
【知识点】决策树、随机森林、特征重要性、树深度调优、交叉验证
【描述】
决策树和随机森林是常用的监督学习算法。本题要求使用scikit-learn实现
DecisionTreeClassifier和RandomForestClassifier，分析特征重要性和
树的深度对模型性能的影响。

数据集说明：
- 使用sklearn内置的葡萄酒数据集(wine dataset)
- 178个样本，13个特征，3个类别
- 分析不同树深度(1~15)下训练精度和测试精度的变化

【要求】
1. 加载wine数据集，划分训练集(70%)和测试集(30%)
2. 训练DecisionTreeClassifier(max_depth=None)，打印分类报告
3. 训练RandomForestClassifier(n_estimators=100)，打印分类报告
4. 分析树深度(1~15)对决策树精度的影响，绘制精度-深度曲线
5. 提取并打印随机森林的特征重要性Top5
6. 绘制特征重要性条形图
7. 使用5折交叉验证评估两个模型

【提示】
- 使用sklearn.datasets.load_wine加载葡萄酒数据集
- 使用sklearn.metrics.classification_report输出分类报告
- 随机森林通过集成多棵决策树降低过拟合风险
- 树深度过大会导致过拟合，训练精度高但测试精度低
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score


def solve():
    # ---- 1. 加载数据 ----
    wine = load_wine()
    X, y = wine.data, wine.target
    feature_names = wine.feature_names
    target_names = wine.target_names

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    print(f"训练集大小: {X_train.shape[0]}, 测试集大小: {X_test.shape[0]}")
    print(f"特征数: {X_train.shape[1]}, 类别数: {len(target_names)}")

    # ---- 2. 决策树分类 ----
    print("\n" + "=" * 60)
    print("决策树分类 (DecisionTreeClassifier)")
    print("=" * 60)
    dt = DecisionTreeClassifier(max_depth=None, random_state=42)
    dt.fit(X_train, y_train)
    y_pred_dt = dt.predict(X_test)
    acc_dt = accuracy_score(y_test, y_pred_dt)
    print(f"测试准确率: {acc_dt:.4f}")
    print(classification_report(y_test, y_pred_dt, target_names=target_names))

    # ---- 3. 随机森林分类 ----
    print("=" * 60)
    print("随机森林分类 (RandomForestClassifier)")
    print("=" * 60)
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    acc_rf = accuracy_score(y_test, y_pred_rf)
    print(f"测试准确率: {acc_rf:.4f}")
    print(classification_report(y_test, y_pred_rf, target_names=target_names))

    # ---- 4. 树深度影响分析 ----
    depths = range(1, 16)
    train_accs = []
    test_accs = []

    for d in depths:
        dt_temp = DecisionTreeClassifier(max_depth=d, random_state=42)
        dt_temp.fit(X_train, y_train)
        train_accs.append(accuracy_score(y_train, dt_temp.predict(X_train)))
        test_accs.append(accuracy_score(y_test, dt_temp.predict(X_test)))

    best_depth = list(depths)[np.argmax(test_accs)]
    print(f"\n最佳树深度: {best_depth}, 对应测试精度: {max(test_accs):.4f}")

    # ---- 5. 特征重要性 Top5 ----
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    print("\n随机森林特征重要性 Top5:")
    print("-" * 40)
    for i in range(5):
        print(f"  {i+1}. {feature_names[indices[i]]:<30s} {importances[indices[i]]:.4f}")

    # ---- 6. 交叉验证 ----
    print("\n" + "=" * 60)
    print("5折交叉验证")
    print("=" * 60)
    cv_dt = cross_val_score(dt, X, y, cv=5, scoring="accuracy")
    cv_rf = cross_val_score(rf, X, y, cv=5, scoring="accuracy")
    print(f"决策树:  {cv_dt.mean():.4f} (+/- {cv_dt.std():.4f})")
    print(f"随机森林: {cv_rf.mean():.4f} (+/- {cv_rf.std():.4f})")

    # ---- 7. 绘图 ----
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 子图1: 精度-深度曲线
    axes[0].plot(depths, train_accs, "bo-", label="训练精度", linewidth=2)
    axes[0].plot(depths, test_accs, "rs-", label="测试精度", linewidth=2)
    axes[0].axvline(x=best_depth, color="green", linestyle="--",
                    label=f"最佳深度={best_depth}")
    axes[0].set_xlabel("树深度")
    axes[0].set_ylabel("准确率")
    axes[0].set_title("决策树: 精度与深度关系")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 子图2: 特征重要性
    top_n = 8
    axes[1].barh(range(top_n), importances[indices[:top_n]][::-1], color="steelblue")
    axes[1].set_yticks(range(top_n))
    axes[1].set_yticklabels([feature_names[i] for i in indices[:top_n]][::-1])
    axes[1].set_xlabel("特征重要性")
    axes[1].set_title("随机森林: 特征重要性排名")

    # 子图3: 交叉验证对比
    axes[2].bar(
        ["决策树", "随机森林"],
        [cv_dt.mean(), cv_rf.mean()],
        yerr=[cv_dt.std(), cv_rf.std()],
        capsize=5, color=["#4C72B0", "#DD8452"],
        alpha=0.8
    )
    axes[2].set_ylabel("准确率")
    axes[2].set_title("5折交叉验证对比")
    axes[2].set_ylim(0.7, 1.0)
    axes[2].grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("q17_decision_tree_random_forest.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图片已保存: q17_decision_tree_random_forest.png")


if __name__ == "__main__":
    solve()

```
