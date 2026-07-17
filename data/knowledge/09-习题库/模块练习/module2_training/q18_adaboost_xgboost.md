# AdaBoost

> 来源模块: module2_training
> 原始文件: q18_adaboost_xgboost.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】AdaBoost与XGBoost：集成学习对比
【模块】模型训练与评估
【难度】5
【知识点】AdaBoost、XGBoost、集成学习、弱分类器、训练时间对比、学习曲线
【描述】
集成学习通过组合多个弱学习器来构建强学习器。本题要求使用sklearn的AdaBoost
和xgboost库分别训练分类模型，对比它们的精度和训练时间。

数据集说明：
- 使用sklearn生成make_moons月牙形数据（1000个样本）
- 加入10%噪声使分类更有挑战
- 比较AdaBoost和XGBoost在不同参数设置下的性能

【要求】
1. 生成make_moons数据集，划分训练集和测试集
2. 实现AdaBoost分类器，测试不同基分类器数量n_estimators=[10, 50, 100, 200]
3. 实现XGBoost分类器，测试相同数量的n_estimators
4. 记录每个模型的训练时间和测试精度
5. 绘制精度-弱分类器数量曲线
6. 绘制两种模型的决策边界
7. 打印对比表格

【提示】
- AdaBoost使用sklearn.ensemble.AdaBoostClassifier
- XGBoost使用xgboost.XGBClassifier
- 使用time.time()记录训练时间
- XGBoost通常在相同弱分类器数量下精度更高
=============================
"""

# ========== 参考答案 ==========

import time
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier


def plot_decision_boundary(ax, model, X, y, title):
    """绘制决策边界"""
    h = 0.02
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                         np.arange(y_min, y_max, h))
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)
    ax.contourf(xx, yy, Z, alpha=0.3, cmap=plt.cm.RdBu)
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap=plt.cm.RdBu, edgecolors="k", s=15, alpha=0.6)
    ax.set_title(title)
    ax.set_xlabel("Feature 1")
    ax.set_ylabel("Feature 2")


def solve():
    # ---- 1. 生成数据 ----
    X, y = make_moons(n_samples=1000, noise=0.15, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"训练集: {X_train.shape[0]}, 测试集: {X_test.shape[0]}")

    # ---- 2. 测试不同n_estimators ----
    n_estimators_list = [10, 50, 100, 200]
    ada_results = {"accs": [], "times": []}
    xgb_results = {"accs": [], "times": []}

    print("\n" + "=" * 60)
    print(f"{'n_estimators':<15} {'AdaBoost Acc':>14} {'AdaBoost Time':>14} "
          f"{'XGBoost Acc':>14} {'XGBoost Time':>14}")
    print("=" * 60)

    for n_est in n_estimators_list:
        # AdaBoost
        start = time.time()
        ada = AdaBoostClassifier(
            estimator=DecisionTreeClassifier(max_depth=3),
            n_estimators=n_est,
            learning_rate=0.1,
            random_state=42
        )
        ada.fit(X_train, y_train)
        ada_time = time.time() - start
        ada_acc = accuracy_score(y_test, ada.predict(X_test))
        ada_results["accs"].append(ada_acc)
        ada_results["times"].append(ada_time)

        # XGBoost
        start = time.time()
        xgb = XGBClassifier(
            n_estimators=n_est,
            max_depth=3,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            verbosity=0
        )
        xgb.fit(X_train, y_train)
        xgb_time = time.time() - start
        xgb_acc = accuracy_score(y_test, xgb.predict(X_test))
        xgb_results["accs"].append(xgb_acc)
        xgb_results["times"].append(xgb_time)

        print(f"{n_est:<15} {ada_acc:>14.4f} {ada_time:>13.4f}s "
              f"{xgb_acc:>14.4f} {xgb_time:>13.4f}s")

    print("=" * 60)

    # ---- 3. 最佳模型决策边界 ----
    best_ada = AdaBoostClassifier(
        estimator=DecisionTreeClassifier(max_depth=3),
        n_estimators=100, learning_rate=0.1, random_state=42
    )
    best_ada.fit(X_train, y_train)

    best_xgb = XGBClassifier(
        n_estimators=100, max_depth=3, learning_rate=0.1,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42, verbosity=0
    )
    best_xgb.fit(X_train, y_train)

    # ---- 4. 绘图 ----
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 子图1: 精度曲线
    axes[0].plot(n_estimators_list, ada_results["accs"], "bo-", label="AdaBoost", linewidth=2)
    axes[0].plot(n_estimators_list, xgb_results["accs"], "rs-", label="XGBoost", linewidth=2)
    axes[0].set_xlabel("n_estimators")
    axes[0].set_ylabel("Test Accuracy")
    axes[0].set_title("Accuracy vs n_estimators")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 子图2: 训练时间
    axes[1].plot(n_estimators_list, ada_results["times"], "bo-", label="AdaBoost", linewidth=2)
    axes[1].plot(n_estimators_list, xgb_results["times"], "rs-", label="XGBoost", linewidth=2)
    axes[1].set_xlabel("n_estimators")
    axes[1].set_ylabel("Training Time (s)")
    axes[1].set_title("Training Time vs n_estimators")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # 子图3 & 4: 决策边界 (用两个子区域)
    plot_decision_boundary(axes[2], best_ada, X_test, y_test,
                           "AdaBoost (n=100)")
    axes[2].text(0.02, 0.02, f"Acc={accuracy_score(y_test, best_ada.predict(X_test)):.4f}",
                 transform=axes[2].transAxes, fontsize=9,
                 bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    plt.tight_layout()
    plt.savefig("q18_adaboost_xgboost.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 额外绘制XGBoost决策边界
    fig2, ax2 = plt.subplots(1, 1, figsize=(6, 5))
    plot_decision_boundary(ax2, best_xgb, X_test, y_test, "XGBoost (n=100)")
    ax2.text(0.02, 0.02, f"Acc={accuracy_score(y_test, best_xgb.predict(X_test)):.4f}",
             transform=ax2.transAxes, fontsize=9,
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    plt.tight_layout()
    plt.savefig("q18_xgboost_boundary.png", dpi=150, bbox_inches="tight")
    plt.close()

    print("\n图片已保存: q18_adaboost_xgboost.png, q18_xgboost_boundary.png")


if __name__ == "__main__":
    solve()

```
