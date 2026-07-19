# K-Means 聚类

## 无监督学习概念

**无监督学习**在没有标注输出的情况下发现数据中隐藏的模式。与监督学习不同，这里没有真实标签——算法必须仅从输入特征中找到结构（分组、密度或低维流形）。

**聚类**是最常见的无监督任务：将 $N$ 个数据点划分为 $K$ 个组（簇），使得同一簇内的点彼此之间的相似度高于与其他簇中点的相似度。

## K-Means 算法

K-Means 是一种**基于质心**的聚类算法。给定 $K$（期望的簇数量），K-Means 迭代地优化簇分配。

### 算法步骤

1. **初始化**：选择 $K$ 个初始质心 $\mu_1, \mu_2, \dots, \mu_K$（随机选择或通过 K-Means++ 选择）。
2. **分配步骤**：将每个数据点 $x_i$ 分配给最近的质心：

$$c_i = \arg\min_{k \in \{1..K\}} \|x_i - \mu_k\|^2$$

其中 $\| \cdot \|$ 为欧几里得距离。

3. **更新步骤**：将每个质心重新计算为其所分配的所有点的均值：

$$\mu_k = \frac{1}{|C_k|} \sum_{x_i \in C_k} x_i$$

4. **重复**步骤 2-3 直到收敛（分配不再变化或质心移动小于容差）。

### 目标函数

K-Means 最小化**簇内平方和 (WCSS)**，也称为惯性：

$$\text{WCSS} = \sum_{k=1}^{K} \sum_{x_i \in C_k} \|x_i - \mu_k\|^2$$

这等价于最小化每个簇内的方差。K-Means 保证收敛到一个**局部**最小值，而非全局最小值。

### 收敛性

- K-Means 始终在有限次迭代内收敛（通常为 10-100 次）
- 收敛到局部最优（取决于初始化）
- 每次迭代严格减少或维持 WCSS

## 选择 K：肘部法

由于 K 必须预先指定，如何选择合适的簇数量呢？**肘部法**对一系列 $K$ 值运行 K-Means，并绘制 WCSS 与 $K$ 的关系图：

- WCSS 随 $K$ 增大而减小（当 $K=N$ 时，WCSS = 0）。
- 寻找"肘部"——即下降速率急剧减缓的点。
- 这代表了增加更多簇的边际收益递减点。

用于选择 $K$ 的替代指标：
- **轮廓系数**（见下文）
- **间隙统计量**：将 WCSS 与零参考分布进行比较
- **Davies-Bouldin 指数**：簇之间的平均相似度（越低越好）

## K-Means++ 初始化

标准 K-Means 以均匀随机方式初始化质心，这可能导致较差的局部最优。**K-Means++** 改进了初始化：

1. 从数据点中随机选择第一个质心。
2. 对于每个剩余质心，以正比于其到最近已选质心的平方距离的概率选择一个数据点：

$$P(x_i) = \frac{D(x_i)^2}{\sum_{j} D(x_j)^2}$$

其中 $D(x_i)$ 是 $x_i$ 到最近已有质心的距离。

3. 重复直到选出 $K$ 个质心，然后运行标准 K-Means。

**优势**：K-Means++ 提供了可证明的 $O(\log K)$ 近似最优聚类解、更快的收敛速度以及更一致的结果。sklearn 默认使用 K-Means++。

## 轮廓系数

轮廓系数在没有真实标签的情况下评估簇质量。对于数据点 $i$：

- $a_i$：$i$ 到其所在簇内所有其他点的平均距离（簇内不相似度）
- $b_i$：$i$ 到任何其他簇中所有点的最小平均距离（最近簇不相似度）

$$s_i = \frac{b_i - a_i}{\max(a_i, b_i)}$$

- $s_i$ 接近 $+1$：点被很好地聚类（靠近自己所在簇，远离其他簇）
- $s_i$ 接近 $0$：点位于两个簇之间的边界上
- $s_i$ 接近 $-1$：点可能被分配到错误的簇

总体轮廓系数是所有点 $s_i$ 的均值。取值范围为 $-1$ 到 $+1$，值越高表示簇的定义越清晰。

## K-Means 的局限性

1. **K 必须预先指定**：需要领域知识或启发式选择。
2. **对初始化敏感**：不同的随机种子会产生不同的结果；可通过 K-Means++ 和多次重启来缓解。
3. **假设簇为球形**：K-Means 使用欧几里得距离，因此它找到的是凸的、各向同性的簇。非球形或拉长的簇很难被正确捕获。
4. **对尺度敏感**：量级较大的特征会主导距离计算；聚类前**务必进行标准化/归一化**。
5. **对异常值敏感**：质心（均值）会被异常值拉偏。替代方案：K-Medoids（使用类中位数代表点）。
6. **硬分配**：每个点只属于一个簇。模糊 C-Means 提供软分配。
7. **维度灾难**：在非常高维的空间中，欧几里得距离的意义减弱；通常先应用降维（PCA）。

## 与其他聚类算法的比较

| 方法 | 优势 | 劣势 | 需要指定 K？ |
|--------|-----------|------------|-----------|
| **K-Means** | 快速、可扩展、简单 | 球形簇，需要 K | 是 |
| **DBSCAN** | 任意形状、找出异常值、无需 K | 难以处理密度差异大的簇，需要 $\epsilon$ 和 `min_samples` | 否 |
| **层次聚类** | 树状图可视化、无需 K | $O(n^2)$ 内存，不可扩展 | 否 |
| **高斯混合模型** | 软分配、椭圆簇 | 假设高斯分布，速度较慢 | 是 |
| **均值漂移** | 无需 K，任意形状 | 速度慢，需要选择带宽 | 否 |

### DBSCAN（基于密度的空间聚类与噪声识别）

- 基于密度对点进行分组：核心点（在 $\epsilon$ 半径内至少有 `min_samples` 个点）、边界点和噪声/异常点
- 可以发现任意形状的簇
- 对异常值具有鲁棒性（将其标记为噪声）
- 不需要预先指定 K
- 当簇具有非常不同的密度时效果不佳

### 层次聚类

- 构建簇的树状结构（树状图）
- **凝聚式**（自底向上）：每个点从自己的簇开始；合并最接近的对
- **分裂式**（自顶向下）：所有点在一个簇中；递归分裂
- 链接准则：单链接（最小距离）、全链接（最大距离）、平均链接、Ward 方法
- 树状图允许在事后选择 K

## 实际应用

- **客户细分**：按购买行为对客户进行分组，以便进行定向营销
- **图像压缩**：将每个像素的颜色替换为其簇质心（颜色量化）
- **文档聚类**：对相似文档进行分组以发现主题
- **异常检测**：距离所有质心都很远的点可能是异常点
- **购物篮分析**：作为预处理步骤，对相似产品或用户进行分组
- **基因组学**：对基因表达模式进行聚类

## Python sklearn 示例

```python
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# 生成包含 4 个簇的合成数据
X, y_true = make_blobs(n_samples=500, centers=4, cluster_std=0.8,
                       random_state=42)

# 标准化特征
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 肘部法：寻找最优 K
inertias = []
silhouette_scores = []
K_range = range(2, 10)

for k in K_range:
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    silhouette_scores.append(silhouette_score(X_scaled, labels))

# 通过轮廓系数找到最佳 K
best_k = list(K_range)[np.argmax(silhouette_scores)]
print(f"Best K by silhouette score: {best_k}")

# 训练最终的 K-Means
kmeans = KMeans(n_clusters=best_k, init="k-means++", n_init=10,
                random_state=42)
y_pred = kmeans.fit_predict(X_scaled)

print(f"Inertia (WCSS): {kmeans.inertia_:.2f}")
print(f"Silhouette Score: {silhouette_score(X_scaled, y_pred):.3f}")

# 簇质心（在缩放后的空间中）
print("Centroids:", kmeans.cluster_centers_)

# 预测新数据
new_points = np.array([[0, 0], [5, 5], [-3, 3]])
new_clusters = kmeans.predict(scaler.transform(new_points))
print(f"New point clusters: {new_clusters}")
```

## 关键超参数 (sklearn)

| 参数 | 描述 |
|-----------|-------------|
| `n_clusters` | 簇的数量 $K$（必填） |
| `init` | 初始化方式：`"k-means++"`（默认）或 `"random"` |
| `n_init` | 使用不同种子重启的次数；保留最优结果（默认 10） |
| `max_iter` | 每次运行的最大迭代次数（默认 300） |
| `tol` | 基于质心移动的收敛容差（默认 1e-4） |
| `random_state` | 随机种子，用于可重复的结果 |

## 数据预处理注意事项

- 在 K-Means 之前务必对特征进行**标准化**（零均值、单位方差）或**归一化**（最小-最大）
- 对于高维数据（如超过 100 个特征），先应用 PCA 以降低噪声
- 在聚类之前移除或处理异常值，因为质心对异常值敏感
- 对分类特征进行独热编码；对于混合数据类型，考虑 Gower 距离
