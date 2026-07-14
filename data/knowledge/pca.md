# Principal Component Analysis (PCA)

## Motivation: Why Dimensionality Reduction?

High-dimensional data suffers from the **curse of dimensionality**: as dimensions increase, data points become sparse, distances become less meaningful, and models require exponentially more data. Dimensionality reduction addresses this by:

- **Visualization:** Projecting data to 2D/3D for human inspection.
- **Noise reduction:** Discarding low-variance dimensions that likely encode noise rather than signal.
- **Feature compression:** Reducing storage and compute requirements while preserving the essential structure.
- **Multicollinearity mitigation:** PCA produces uncorrelated features, stabilizing linear models.

---

## PCA Concept: Finding Directions of Maximum Variance

PCA finds orthogonal axes (principal components) ordered by the amount of variance they capture. The first principal component points in the direction of greatest variance; the second, orthogonal to the first, captures the next greatest variance; and so on.

Intuitively: if your data lies roughly on a 2D plane in a 10D space, PCA finds that plane.

---

## Mathematical Derivation

Given data matrix $X \in \mathbb{R}^{n \times d}$ (n samples, d features), we want a projection matrix $W \in \mathbb{R}^{d \times k}$ (k < d) that maximizes the variance of the projected data $XW$.

### Objective

Maximize the variance of the projection onto direction $w$ (subject to $\|w\| = 1$):

$$\max_{\|w\|=1} \operatorname{Var}(Xw) = \max_{\|w\|=1} \frac{1}{n-1} w^T X^T X w = \max_{\|w\|=1} w^T \Sigma w$$

where $\Sigma = \frac{1}{n-1} X^T X$ is the covariance matrix (assuming centered $X$).

### Solution via Eigendecomposition

Using Lagrange multipliers, the solution satisfies:

$$\Sigma w = \lambda w$$

So the optimal $w$ is the **eigenvector** of $\Sigma$ corresponding to the largest **eigenvalue** $\lambda$. The eigenvalue equals the variance captured along that direction.

For $k$ components, select the $k$ eigenvectors with the largest eigenvalues:

$$W = [v_1 \mid v_2 \mid \dots \mid v_k]$$

---

## PCA Step-by-Step Algorithm

1. **Center the data:** Subtract the mean of each feature: $X_{\text{centered}} = X - \mu$.
2. **Standardize (optional but recommended):** Scale each feature to unit variance so features with large numeric ranges don't dominate: $X_{ij} = (X_{ij} - \mu_j) / \sigma_j$.
3. **Compute covariance matrix:** $\Sigma = \frac{1}{n-1} X_{\text{centered}}^T X_{\text{centered}}$.
4. **Eigendecomposition:** Find eigenvalues $\lambda_i$ and eigenvectors $v_i$ of $\Sigma$.
5. **Sort:** Order eigenvectors by decreasing eigenvalue.
6. **Select top $k$:** Keep the first $k$ eigenvectors.
7. **Project:** $X_{\text{reduced}} = X_{\text{centered}} W_k$, where $W_k$ is the $d \times k$ matrix of top eigenvectors.

---

## Explained Variance Ratio

The proportion of total variance captured by component $i$:

$$\text{EV}_i = \frac{\lambda_i}{\sum_{j=1}^d \lambda_j}$$

The cumulative explained variance after $k$ components:

$$\text{CEV}(k) = \frac{\sum_{i=1}^k \lambda_i}{\sum_{j=1}^d \lambda_j}$$

**Rule of thumb:** Choose $k$ such that $\text{CEV}(k) > 0.95$ (retain 95% of the variance). Alternatively, use the "elbow" in the scree plot.

---

## Relationship with SVD

PCA is equivalent to the SVD of the centered data matrix:

$$X_{\text{centered}} = U S V^T$$

- The right singular vectors $V$ are the eigenvectors of the covariance matrix (the principal components).
- The singular values squared $S^2 / (n-1)$ equal the eigenvalues $\lambda$.
- The projected data is $U_k S_k$ (or equivalently $X V_k$).

SVD is often preferred numerically because it avoids explicitly computing the covariance matrix.

---

## sklearn Example

```python
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_iris

# Load data and standardize
X, y = load_iris(return_X_y=True)
X_scaled = StandardScaler().fit_transform(X)

# Fit PCA
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

print(f"Explained variance ratio: {pca.explained_variance_ratio_}")
print(f"Total explained: {pca.explained_variance_ratio_.sum():.3f}")

# Scree plot data
print(f"All eigenvalues: {pca.explained_variance_}")
```

---

## Kernel PCA

Standard PCA finds linear projections. Kernel PCA uses the kernel trick to find nonlinear structure:

$$\text{KPCA: compute eigenvectors of the kernel matrix } K_{ij} = \phi(x_i)^T \phi(x_j)$$

Common kernels: RBF (Gaussian), polynomial, sigmoid. RBF kernel PCA can separate concentric circles that linear PCA cannot.

```python
from sklearn.decomposition import KernelPCA
kpca = KernelPCA(n_components=2, kernel='rbf', gamma=0.1)
X_kpca = kpca.fit_transform(X_scaled)
```

---

## t-SNE and UMAP: When to Use What

| Method | Strengths | Weaknesses | Best For |
|--------|-----------|------------|----------|
| **PCA** | Fast, deterministic, interpretable components | Linear only, poor for complex manifolds | First pass, preprocessing, linear data |
| **t-SNE** | Excellent local structure preservation | Slow, non-deterministic, global distances distorted | Visualization, clustering inspection |
| **UMAP** | Fast, preserves both local and global structure | Newer, fewer theoretical guarantees | Modern go-to for visualization |

**Practical workflow:** Use PCA for dimensionality reduction before modeling and as a sanity check. Use t-SNE or UMAP for visualization of clusters. Never run t-SNE on raw 1000D data — reduce to ~50D with PCA first.

---

## Applications

- **Data visualization:** Project high-dimensional embeddings or feature vectors to 2D for plotting.
- **Feature compression:** Reduce input dimensionality before feeding into downstream models to speed up training and reduce overfitting.
- **Noise filtering:** Reconstruct data using only top $k$ components, discarding noise in low-variance dimensions.
- **Anomaly detection:** Reconstruction error (original minus PCA-reconstructed) is high for anomalous samples that deviate from the main variance structure.
- **Gene expression analysis:** Identifying latent factors in microarray/RNA-seq data.
