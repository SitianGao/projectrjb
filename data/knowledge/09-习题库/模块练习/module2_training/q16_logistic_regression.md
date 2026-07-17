# 决策边界对比

> 来源模块: module2_training
> 原始文件: q16_logistic_regression.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】逻辑回归：手动实现与sklearn对比
【模块】模型训练与评估
【难度】3
【知识点】逻辑回归、梯度下降、Sigmoid函数、交叉熵损失、二分类
【描述】
逻辑回归是经典的二分类算法。本题要求手动使用梯度下降实现逻辑回归，
然后与scikit-learn的LogisticRegression进行对比。

数据集说明：
- 使用sklearn.datasets.make_classification生成二分类数据
- 200个样本，2个特征，便于可视化决策边界
- 比较手动实现与sklearn实现的准确率和决策边界

【要求】
1. 手动实现LogisticRegressionGD类，包含：
   - sigmoid函数
   - 损失函数（交叉熵）
   - 梯度计算与参数更新
   - predict和predict_proba方法
2. 使用sklearn的LogisticRegression作为基准
3. 对比两种实现的准确率（accuracy）
4. 绘制两种模型的决策边界对比图
5. 打印训练过程中损失的变化

【提示】
- Sigmoid: sigma(z) = 1 / (1 + exp(-z))
- 交叉熵损失: L = -1/n * sum(y*log(p) + (1-y)*log(1-p))
- 梯度: dW = 1/n * X^T * (sigma(XW+b) - y)
- 学习率建议0.1，迭代次数1000
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression as SklearnLR
from sklearn.metrics import accuracy_score


class LogisticRegressionGD:
    """手动实现的逻辑回归（梯度下降）"""

    def __init__(self, lr=0.1, n_iters=1000, verbose=False):
        self.lr = lr
        self.n_iters = n_iters
        self.verbose = verbose
        self.weights = None
        self.bias = None
        self.losses = []

    @staticmethod
    def _sigmoid(z):
        # 防止溢出
        z = np.clip(z, -500, 500)
        return 1.0 / (1.0 + np.exp(-z))

    def _compute_loss(self, y, y_pred):
        """计算交叉熵损失"""
        eps = 1e-15
        y_pred = np.clip(y_pred, eps, 1 - eps)
        return -np.mean(y * np.log(y_pred) + (1 - y) * np.log(1 - y_pred))

    def fit(self, X, y):
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        self.losses = []

        for i in range(self.n_iters):
            # 前向传播
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)

            # 计算梯度
            dw = (1 / n_samples) * np.dot(X.T, (y_pred - y))
            db = (1 / n_samples) * np.sum(y_pred - y)

            # 更新参数
            self.weights -= self.lr * dw
            self.bias -= self.lr * db

            # 记录损失
            loss = self._compute_loss(y, y_pred)
            self.losses.append(loss)

            if self.verbose and (i + 1) % 200 == 0:
                print(f"  Iteration {i+1}/{self.n_iters}, Loss: {loss:.4f}")

        return self

    def predict_proba(self, X):
        z = np.dot(X, self.weights) + self.bias
        return self._sigmoid(z)

    def predict(self, X):
        return (self.predict_proba(X) >= 0.5).astype(int)


def plot_decision_boundary(ax, model, X, y, title, is_sklearn=True):
    """绘制决策边界"""
    h = 0.02
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                         np.arange(y_min, y_max, h))
    grid = np.c_[xx.ravel(), yy.ravel()]

    if is_sklearn:
        Z = model.predict(grid)
        Z_proba = model.predict_proba(grid)[:, 1]
    else:
        Z = model.predict(grid)
        Z_proba = model.predict_proba(grid)

    Z = Z.reshape(xx.shape)
    ax.contourf(xx, yy, Z, alpha=0.3, cmap=plt.cm.RdBu)
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap=plt.cm.RdBu, edgecolors="k", s=30)
    ax.set_title(title)
    ax.set_xlabel("Feature 1")
    ax.set_ylabel("Feature 2")


def solve():
    # ---- 1. 生成数据 ----
    X, y = make_classification(
        n_samples=200, n_features=2, n_redundant=0,
        n_informative=2, random_state=42, n_clusters_per_class=1
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ---- 2. 手动实现逻辑回归 ----
    print("=" * 50)
    print("手动实现逻辑回归（梯度下降）")
    print("=" * 50)
    manual_lr = LogisticRegressionGD(lr=0.1, n_iters=1000, verbose=True)
    manual_lr.fit(X_train, y_train)
    y_pred_manual = manual_lr.predict(X_test)
    acc_manual = accuracy_score(y_test, y_pred_manual)
    print(f"\n手动实现准确率: {acc_manual:.4f}")

    # ---- 3. sklearn逻辑回归 ----
    print("\n" + "=" * 50)
    print("sklearn LogisticRegression")
    print("=" * 50)
    sk_lr = SklearnLR(max_iter=1000, random_state=42)
    sk_lr.fit(X_train, y_train)
    y_pred_sk = sk_lr.predict(X_test)
    acc_sk = accuracy_score(y_test, y_pred_sk)
    print(f"sklearn准确率: {acc_sk:.4f}")

    # ---- 4. 对比结果 ----
    print("\n" + "=" * 50)
    print("对比结果")
    print("=" * 50)
    print(f"手动实现准确率: {acc_manual:.4f}")
    print(f"sklearn准确率:  {acc_sk:.4f}")
    print(f"差异:           {abs(acc_manual - acc_sk):.4f}")

    # ---- 5. 绘图 ----
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 决策边界对比
    plot_decision_boundary(axes[0], manual_lr, X_test, y_test,
                           "Manual Logistic Regression", is_sklearn=False)
    plot_decision_boundary(axes[1], sk_lr, X_test, y_test,
                           "sklearn Logistic Regression", is_sklearn=True)

    # 损失曲线
    axes[2].plot(range(1, len(manual_lr.losses) + 1), manual_lr.losses, "b-", linewidth=1)
    axes[2].set_title("Training Loss (Cross-Entropy)")
    axes[2].set_xlabel("Iteration")
    axes[2].set_ylabel("Loss")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("q16_logistic_regression.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图片已保存: q16_logistic_regression.png")


if __name__ == "__main__":
    solve()

```
