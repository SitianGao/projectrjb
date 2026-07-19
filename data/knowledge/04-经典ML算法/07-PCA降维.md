# 主成分分析 (PCA)

## 动机：为什么需要降维？

高维数据面临**维度灾难**：随着维度的增加，数据点变得稀疏，距离变得缺乏意义，模型需要指数级更多的数据。降维通过以下方式解决这一问题：

- **可视化：** 将数据投影到 2D/3D 以供人工检查。
- **降噪：** 丢弃那些可能编码噪声而非信号的低方差维度。
- **特征压缩：** 在保留基本结构的同时，减少存储和计算需求。
- **缓解多重共线性：** PCA 生成不相关的特征，稳定线性模型。

---

## PCA 概念：寻找最大方差方向

PCA 找到按捕获方差大小排序的正交轴（主成分）。第一主成分指向方差最大的方向；第二主成分（与第一正交）捕获次大的方差；以此类推。

直观理解：如果你的数据大致位于 10D 空间中的 2D 平面上，PCA 可以找到那个平面。

---

## 数学推导

给定数据矩阵 $X \in \mathbb{R}^{n \times d}$（n 个样本，d 个特征），我们希望找到一个投影矩阵 $W \in \mathbb{R}^{d \times k}$（k < d），使得投影数据 $XW$ 的方差最大化。

### 目标函数

最大化投影到方向 $w$ 上的方差（满足 $\|w\| = 1$）：

$$\max_{\|w\|=1} \operatorname{Var}(Xw) = \max_{\|w\|=1} \frac{1}{n-1} w^T X^T X w = \max_{\|w\|=1} w^T \Sigma w$$

其中 $\Sigma = \frac{1}{n-1} X^T X$ 是协方差矩阵（假设 $X$ 已中心化）。

### 通过特征分解求解

使用拉格朗日乘子法，解满足：

$$\Sigma w = \lambda w$$

因此，最优的 $w$ 是 $\Sigma$ 的**特征向量**，对应最大的**特征值** $\lambda$。特征值等于沿该方向捕获的方差。

对于 $k$ 个成分，选择对应最大特征值的 $k$ 个特征向量：

$$W = [v_1 \mid v_2 \mid \dots \mid v_k]$$

---

## PCA 逐步算法

1. **数据中心化：** 减去每个特征的均值：$X_{\text{centered}} = X - \mu$。
2. **标准化（可选但推荐）：** 将每个特征缩放到单位方差，使数值范围较大的特征不会占据主导：$X_{ij} = (X_{ij} - \mu_j) / \sigma_j$。
3. **计算协方差矩阵：** $\Sigma = \frac{1}{n-1} X_{\text{centered}}^T X_{\text{centered}}$。
4. **特征分解：** 找到 $\Sigma$ 的特征值 $\lambda_i$ 和特征向量 $v_i$。
5. **排序：** 按特征值降序排列特征向量。
6. **选择前 $k$ 个：** 保留前 $k$ 个特征向量。
7. **投影：** $X_{\text{reduced}} = X_{\text{centered}} W_k$，其中 $W_k$ 是由前 $k$ 个特征向量组成的 $d \times k$ 矩阵。

---

## 解释方差比

第 $i$ 个成分捕获的总方差比例：

$$\text{EV}_i = \frac{\lambda_i}{\sum_{j=1}^d \lambda_j}$$

$k$ 个成分后的累积解释方差：

$$\text{CEV}(k) = \frac{\sum_{i=1}^k \lambda_i}{\sum_{j=1}^d \lambda_j}$$

**经验法则：** 选择 $k$ 使得 $\text{CEV}(k) > 0.95$（保留 95% 的方差）。或者，使用陡坡图中的"肘部"来确定。

---

## 与 SVD 的关系

PCA 等价于中心化数据矩阵的 SVD：

$$X_{\text{centered}} = U S V^T$$

- 右奇异向量 $V$ 是协方差矩阵的特征向量（即主成分）。
- 奇异值的平方 $S^2 / (n-1)$ 等于特征值 $\lambda$。
- 投影后的数据为 $U_k S_k$（或等价地 $X V_k$）。

SVD 在数值上通常更受青睐，因为它避免了显式计算协方差矩阵。

---

## sklearn 示例

```python
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_iris

# 加载数据并标准化
X, y = load_iris(return_X_y=True)
X_scaled = StandardScaler().fit_transform(X)

# 拟合 PCA
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

print(f"Explained variance ratio: {pca.explained_variance_ratio_}")
print(f"Total explained: {pca.explained_variance_ratio_.sum():.3f}")

# 陡坡图数据
print(f"All eigenvalues: {pca.explained_variance_}")
```

---

## 核 PCA

标准 PCA 寻找线性投影。核 PCA 使用核技巧来寻找非线性结构：

$$\text{KPCA: 计算核矩阵 } K_{ij} = \phi(x_i)^T \phi(x_j) \text{ 的特征向量}$$

常用核函数：RBF（高斯）、多项式、sigmoid。RBF 核 PCA 可以分离线性 PCA 无法分离的同心圆。

```python
from sklearn.decomposition import KernelPCA
kpca = KernelPCA(n_components=2, kernel='rbf', gamma=0.1)
X_kpca = kpca.fit_transform(X_scaled)
```

---

## t-SNE 与 UMAP：何时使用何种方法

| 方法 | 优势 | 劣势 | 最佳适用场景 |
|--------|-----------|------------|----------|
| **PCA** | 快速、确定性、成分可解释 | 仅线性，对复杂流形效果差 | 初步分析、预处理、线性数据 |
| **t-SNE** | 局部结构保持优秀 | 慢、非确定性、全局距离失真 | 可视化、聚类检查 |
| **UMAP** | 快速、同时保持局部和全局结构 | 较新、理论保证较少 | 现代可视化的首选 |

**实用工作流程：** 使用 PCA 在建模前进行降维，并作为合理性检查。使用 t-SNE 或 UMAP 进行聚类可视化。永远不要直接在原始 1000D 数据上运行 t-SNE——先用 PCA 降到约 50D。

---

## 应用场景

- **数据可视化：** 将高维嵌入或特征向量投影到 2D 以进行绘图。
- **特征压缩：** 在输入下游模型之前降低输入维度，以加速训练并减少过拟合。
- **噪声过滤：** 仅使用前 $k$ 个成分重建数据，丢弃低方差维度中的噪声。
- **异常检测：** 对于偏离主要方差结构的异常样本，重构误差（原始数据减去 PCA 重构数据）会很大。
- **基因表达分析：** 识别微阵列/RNA-seq 数据中的潜在因子。
