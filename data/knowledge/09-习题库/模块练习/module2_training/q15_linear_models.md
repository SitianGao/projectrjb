# 真实关系: y = 2 + 3*X - 0.5*X^2 + noise

> 来源模块: module2_training
> 原始文件: q15_linear_models.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】线性模型全家桶：回归模型对比
【模块】模型训练与评估
【难度】3
【知识点】线性回归、Ridge回归、Lasso回归、多项式回归、MSE、R²
【描述】
在机器学习中，线性模型是最基础也最重要的模型族。本题要求使用scikit-learn
实现四种回归模型：普通最小二乘回归(OLS)、Ridge回归、Lasso回归和多项式回归，
并在生成的非线性数据集上对比它们的性能。

数据集说明：
- 生成一个特征X（100个样本），真实关系为 y = 2 + 3*X - 0.5*X^2 + noise
- 将数据划分为训练集(80%)和测试集(20%)
- 对比各模型在测试集上的MSE和R²指标

【要求】
1. 使用numpy生成带噪声的二次关系数据
2. 实现OLS线性回归（LinearRegression）
3. 实现Ridge回归，测试alpha=[0.1, 1.0, 10.0]三个参数
4. 实现Lasso回归，测试alpha=[0.1, 1.0, 10.0]三个参数
5. 实现多项式回归（degree=2），结合LinearRegression
6. 打印所有模型的MSE和R²对比表格
7. 使用matplotlib绘制数据点和各模型拟合曲线的对比图

【提示】
- 使用sklearn.preprocessing.PolynomialFeatures进行多项式特征变换
- Ridge和Lasso的正则化参数alpha越大，正则化强度越大
- R²越接近1表示拟合越好，MSE越小表示误差越小
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score


def solve():
    # ---- 1. 生成数据 ----
    np.random.seed(42)
    n_samples = 100
    X = np.random.uniform(-3, 3, size=n_samples).reshape(-1, 1)
    # 真实关系: y = 2 + 3*X - 0.5*X^2 + noise
    y_true = 2 + 3 * X.ravel() - 0.5 * X.ravel() ** 2
    y = y_true + np.random.normal(0, 1.5, size=n_samples)

    # ---- 2. 划分训练集和测试集 ----
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ---- 3. 定义模型 ----
    models = {}

    # (a) 普通最小二乘回归
    models["OLS"] = LinearRegression()

    # (b) Ridge回归，不同alpha
    for alpha in [0.1, 1.0, 10.0]:
        models[f"Ridge(alpha={alpha})"] = Ridge(alpha=alpha)

    # (c) Lasso回归，不同alpha
    for alpha in [0.1, 1.0, 10.0]:
        models[f"Lasso(alpha={alpha})"] = Lasso(alpha=alpha, max_iter=10000)

    # (d) 多项式回归 (degree=2)
    models["PolyRegression(d=2)"] = Pipeline([
        ("poly", PolynomialFeatures(degree=2, include_bias=False)),
        ("lr", LinearRegression()),
    ])

    # ---- 4. 训练与评估 ----
    print("=" * 60)
    print(f"{'模型':<25} {'MSE':>10} {'R²':>10}")
    print("=" * 60)

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        results[name] = {"model": model, "mse": mse, "r2": r2, "y_pred": y_pred}
        print(f"{name:<25} {mse:>10.4f} {r2:>10.4f}")

    print("=" * 60)

    # ---- 5. 绘图 ----
    X_plot = np.linspace(-3, 3, 300).reshape(-1, 1)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("线性模型对比", fontsize=16)

    # 子图1: OLS vs 真实曲线
    ax = axes[0, 0]
    ax.scatter(X_test, y_test, c="blue", s=20, label="测试数据", alpha=0.7)
    ax.plot(X_plot, 2 + 3 * X_plot.ravel() - 0.5 * X_plot.ravel() ** 2,
            "g--", label="真实曲线", linewidth=2)
    ols = results["OLS"]["model"]
    ax.plot(X_plot, ols.predict(X_plot), "r-", label="OLS", linewidth=2)
    ax.set_title("OLS线性回归")
    ax.legend(fontsize=8)
    ax.set_xlabel("X")
    ax.set_ylabel("y")

    # 子图2: Ridge回归对比
    ax = axes[0, 1]
    ax.scatter(X_test, y_test, c="blue", s=20, alpha=0.7, label="测试数据")
    ax.plot(X_plot, 2 + 3 * X_plot.ravel() - 0.5 * X_plot.ravel() ** 2,
            "g--", label="真实曲线", linewidth=2)
    colors_ridge = ["red", "orange", "brown"]
    for idx, alpha in enumerate([0.1, 1.0, 10.0]):
        name = f"Ridge(alpha={alpha})"
        m = results[name]["model"]
        ax.plot(X_plot, m.predict(X_plot), c=colors_ridge[idx],
                label=f"Ridge a={alpha}", linewidth=1.5)
    ax.set_title("Ridge回归")
    ax.legend(fontsize=7)
    ax.set_xlabel("X")
    ax.set_ylabel("y")

    # 子图3: Lasso回归对比
    ax = axes[1, 0]
    ax.scatter(X_test, y_test, c="blue", s=20, alpha=0.7, label="测试数据")
    ax.plot(X_plot, 2 + 3 * X_plot.ravel() - 0.5 * X_plot.ravel() ** 2,
            "g--", label="真实曲线", linewidth=2)
    colors_lasso = ["red", "purple", "brown"]
    for idx, alpha in enumerate([0.1, 1.0, 10.0]):
        name = f"Lasso(alpha={alpha})"
        m = results[name]["model"]
        ax.plot(X_plot, m.predict(X_plot), c=colors_lasso[idx],
                label=f"Lasso a={alpha}", linewidth=1.5)
    ax.set_title("Lasso回归")
    ax.legend(fontsize=7)
    ax.set_xlabel("X")
    ax.set_ylabel("y")

    # 子图4: 多项式回归
    ax = axes[1, 1]
    ax.scatter(X_test, y_test, c="blue", s=20, alpha=0.7, label="测试数据")
    ax.plot(X_plot, 2 + 3 * X_plot.ravel() - 0.5 * X_plot.ravel() ** 2,
            "g--", label="真实曲线", linewidth=2)
    poly = results["PolyRegression(d=2)"]["model"]
    ax.plot(X_plot, poly.predict(X_plot), "r-", label="多项式(d=2)", linewidth=2)
    ax.set_title("多项式回归 (degree=2)")
    ax.legend(fontsize=8)
    ax.set_xlabel("X")
    ax.set_ylabel("y")

    plt.tight_layout()
    plt.savefig("q15_linear_models_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图片已保存: q15_linear_models_comparison.png")


if __name__ == "__main__":
    solve()

```
