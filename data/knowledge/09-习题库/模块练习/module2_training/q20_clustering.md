# (n_samples, n_clusters)

> 来源模块: module2_training
> 原始文件: q20_clustering.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】聚类算法：K-Means手动实现与sklearn聚类对比
【模块】模型训练与评估
【难度】4
【知识点】K-Means、层次聚类、DBSCAN、轮廓系数、聚类评估
【描述】
聚类是无监督学习的重要任务。本题要求手动实现K-Means算法，然后使用
sklearn的AgglomerativeClustering和DBSCAN进行聚类对比，使用轮廓系数
评估聚类质量。

数据集说明：
- 使用sklearn生成三种数据：make_blobs(球形簇)、make_moons(月牙形)、
  带噪声的环形数据
- 在不同数据分布上对比三种聚类算法的表现

【要求】
1. 手动实现KMeansManual类，包含：
   - 初始化：随机选择初始中心点
   - 迭代：分配样本到最近中心，更新中心
   - 收敛条件：中心点不再变化或达到最大迭代次数
2. 使用sklearn的AgglomerativeClustering进行层次聚类
3. 使用sklearn的DBSCAN进行密度聚类
4. 计算并对比三种算法的轮廓系数
5. 在make_blobs数据上绘制聚类结果对比图
6. 在make_moons数据上展示不同算法的适应性差异

【提示】
- K-Means适合球形簇，DBSCAN适合任意形状的簇
- 轮廓系数范围[-1, 1]，越接近1表示聚类越好
- DBSCAN不需要指定簇数，通过eps和min_samples控制聚类
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs, make_moons, make_circles
from sklearn.cluster import AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score


class KMeansManual:
    """手动实现的K-Means聚类算法"""

    def __init__(self, n_clusters=3, max_iters=100, random_state=42, n_init=10):
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        self.random_state = random_state
        self.n_init = n_init
        self.centroids = None
        self.labels_ = None
        self.inertia_ = None

    def _init_centroids(self, X, rng):
        """随机初始化中心点"""
        indices = rng.choice(X.shape[0], self.n_clusters, replace=False)
        return X[indices].copy()

    def _compute_distances(self, X, centroids):
        """计算每个样本到各中心点的距离"""
        # (n_samples, n_clusters)
        dists = np.zeros((X.shape[0], self.n_clusters))
        for k in range(self.n_clusters):
            dists[:, k] = np.sqrt(np.sum((X - centroids[k]) ** 2, axis=1))
        return dists

    def _compute_inertia(self, X, labels, centroids):
        """计算惯性（SSE）"""
        inertia = 0.0
        for k in range(self.n_clusters):
            mask = labels == k
            if np.any(mask):
                inertia += np.sum((X[mask] - centroids[k]) ** 2)
        return inertia

    def fit(self, X):
        best_centroids = None
        best_labels = None
        best_inertia = float("inf")
        rng = np.random.RandomState(self.random_state)

        for _ in range(self.n_init):
            centroids = self._init_centroids(X, rng)

            for _ in range(self.max_iters):
                # 分配步骤：将每个样本分配到最近中心
                dists = self._compute_distances(X, centroids)
                labels = np.argmin(dists, axis=1)

                # 更新步骤：重新计算中心点
                new_centroids = np.zeros_like(centroids)
                for k in range(self.n_clusters):
                    mask = labels == k
                    if np.any(mask):
                        new_centroids[k] = X[mask].mean(axis=0)
                    else:
                        new_centroids[k] = centroids[k]

                # 检查收敛
                if np.allclose(centroids, new_centroids):
                    break
                centroids = new_centroids

            inertia = self._compute_inertia(X, labels, centroids)
            if inertia < best_inertia:
                best_inertia = inertia
                best_centroids = centroids.copy()
                best_labels = labels.copy()

        self.centroids = best_centroids
        self.labels_ = best_labels
        self.inertia_ = best_inertia
        return self

    def predict(self, X):
        dists = self._compute_distances(X, self.centroids)
        return np.argmin(dists, axis=1)


def solve():
    # ---- 1. 生成数据 ----
    np.random.seed(42)

    # 数据集1: 球形簇
    X_blobs, y_blobs = make_blobs(n_samples=300, centers=4,
                                   cluster_std=0.6, random_state=42)

    # 数据集2: 月牙形
    X_moons, y_moons = make_moons(n_samples=300, noise=0.05, random_state=42)

    # 数据集3: 同心圆
    X_circles, y_circles = make_circles(n_samples=300, noise=0.05,
                                         factor=0.5, random_state=42)

    datasets = [
        ("Blobs (球形簇)", X_blobs, 4),
        ("Moons (月牙形)", X_moons, 2),
        ("Circles (同心圆)", X_circles, 2),
    ]

    # ---- 2. 聚类与评估 ----
    print("=" * 70)
    print(f"{'数据集':<20} {'K-Means':>12} {'层次聚类':>12} {'DBSCAN':>12}")
    print("=" * 70)

    fig, axes = plt.subplots(3, 3, figsize=(15, 13))

    for row, (name, X, n_clusters) in enumerate(datasets):
        # 手动K-Means
        km = KMeansManual(n_clusters=n_clusters, random_state=42)
        km.fit(X)

        # 层次聚类
        agg = AgglomerativeClustering(n_clusters=n_clusters)
        agg_labels = agg.fit_predict(X)

        # DBSCAN
        if "Moons" in name:
            db = DBSCAN(eps=0.2, min_samples=5)
        elif "Circles" in name:
            db = DBSCAN(eps=0.2, min_samples=5)
        else:
            db = DBSCAN(eps=0.5, min_samples=5)
        db_labels = db.fit_predict(X)

        # 轮廓系数（至少需要2个簇且无噪声点时计算）
        def safe_silhouette(X, labels):
            unique = set(labels)
            if -1 in unique:
                unique.discard(-1)
            if len(unique) < 2:
                return -1.0
            mask = labels != -1
            if mask.sum() < 2:
                return -1.0
            return silhouette_score(X[mask], labels[mask])

        s_km = safe_silhouette(X, km.labels_)
        s_agg = safe_silhouette(X, agg_labels)
        s_db = safe_silhouette(X, db_labels)

        print(f"{name:<20} {s_km:>12.4f} {s_agg:>12.4f} {s_db:>12.4f}")

        # 绘图
        # K-Means
        ax = axes[row, 0]
        ax.scatter(X[:, 0], X[:, 1], c=km.labels_, cmap="viridis", s=15, alpha=0.7)
        if km.centroids is not None:
            ax.scatter(km.centroids[:, 0], km.centroids[:, 1],
                       c="red", marker="X", s=100, edgecolors="k")
        ax.set_title(f"K-Means: {name}")
        ax.set_xticks([])
        ax.set_yticks([])

        # 层次聚类
        ax = axes[row, 1]
        ax.scatter(X[:, 0], X[:, 1], c=agg_labels, cmap="viridis", s=15, alpha=0.7)
        ax.set_title(f"层次聚类: {name}")
        ax.set_xticks([])
        ax.set_yticks([])

        # DBSCAN
        ax = axes[row, 2]
        ax.scatter(X[:, 0], X[:, 1], c=db_labels, cmap="viridis", s=15, alpha=0.7)
        ax.set_title(f"DBSCAN: {name}")
        ax.set_xticks([])
        ax.set_yticks([])

    print("=" * 70)

    plt.tight_layout()
    plt.savefig("q20_clustering.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图片已保存: q20_clustering.png")

    # ---- 3. K-Means肘部法则 ----
    print("\nK-Means肘部法则 (Blobs数据):")
    inertias = []
    K_range = range(2, 9)
    for k in K_range:
        km = KMeansManual(n_clusters=k, random_state=42)
        km.fit(X_blobs)
        inertias.append(km.inertia_)
        print(f"  K={k}: SSE={km.inertia_:.2f}")

    fig2, ax2 = plt.subplots(1, 1, figsize=(8, 5))
    ax2.plot(K_range, inertias, "bo-", linewidth=2)
    ax2.set_xlabel("簇数量 (K)")
    ax2.set_ylabel("SSE (惯性)")
    ax2.set_title("K-Means肘部法则")
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("q20_elbow.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("图片已保存: q20_elbow.png")


if __name__ == "__main__":
    solve()

```
