# K-Means Clustering

## Unsupervised Learning Concept

**Unsupervised learning** discovers hidden patterns in data without labeled outputs. Unlike supervised learning, there is no ground truth — the algorithm must find structure (groupings, densities, or low-dimensional manifolds) purely from the input features.

**Clustering** is the most common unsupervised task: partition $N$ data points into $K$ groups (clusters) such that points within a cluster are more similar to each other than to points in other clusters.

## K-Means Algorithm

K-Means is a **centroid-based** clustering algorithm. Given $K$ (the desired number of clusters), K-Means iteratively refines cluster assignments.

### Algorithm Steps

1. **Initialization**: Choose $K$ initial centroids $\mu_1, \mu_2, \dots, \mu_K$ (randomly or via K-Means++).
2. **Assignment Step**: Assign each data point $x_i$ to the nearest centroid:

$$c_i = \arg\min_{k \in \{1..K\}} \|x_i - \mu_k\|^2$$

where $\| \cdot \|$ is Euclidean distance.

3. **Update Step**: Recompute each centroid as the mean of all points assigned to it:

$$\mu_k = \frac{1}{|C_k|} \sum_{x_i \in C_k} x_i$$

4. **Repeat** steps 2-3 until convergence (no change in assignments or centroids move less than tolerance).

### Objective Function

K-Means minimizes the **within-cluster sum of squares (WCSS)**, also called inertia:

$$\text{WCSS} = \sum_{k=1}^{K} \sum_{x_i \in C_k} \|x_i - \mu_k\|^2$$

This is equivalent to minimizing the variance within each cluster. K-Means is guaranteed to converge to a **local** minimum, not the global minimum.

### Convergence

- K-Means always converges in finite iterations (typically 10-100)
- Convergence is to a local optimum (depends on initialization)
- Each iteration strictly decreases or maintains WCSS

## Choosing K: The Elbow Method

Since K must be specified, how do we choose the right number of clusters? The **elbow method** runs K-Means for a range of $K$ values and plots WCSS vs. $K$:

- WCSS decreases as $K$ increases (at $K=N$, WCSS = 0).
- Look for the "elbow" — the point where the rate of decrease sharply slows.
- This represents the diminishing return of adding more clusters.

Alternative metrics for selecting $K$:
- **Silhouette Score** (see below)
- **Gap Statistic**: compares WCSS to a null reference distribution
- **Davies-Bouldin Index**: average similarity between clusters (lower is better)

## K-Means++ Initialization

Standard K-Means initializes centroids uniformly at random, which can lead to poor local optima. **K-Means++** improves initialization:

1. Choose the first centroid randomly from the data points.
2. For each remaining centroid, choose a data point with probability proportional to its squared distance from the nearest already-chosen centroid:

$$P(x_i) = \frac{D(x_i)^2}{\sum_{j} D(x_j)^2}$$

where $D(x_i)$ is the distance from $x_i$ to the nearest existing centroid.

3. Repeat until $K$ centroids are chosen, then run standard K-Means.

**Benefits**: K-Means++ provides a provable $O(\log K)$ approximation to the optimal clustering, faster convergence, and more consistent results. sklearn uses K-Means++ by default.

## Silhouette Score

The silhouette score evaluates cluster quality without ground truth labels. For data point $i$:

- $a_i$: mean distance from $i$ to all other points in its own cluster (within-cluster dissimilarity)
- $b_i$: minimum mean distance from $i$ to points in any other cluster (nearest-cluster dissimilarity)

$$s_i = \frac{b_i - a_i}{\max(a_i, b_i)}$$

- $s_i$ near $+1$: point is well-clustered (close to own cluster, far from others)
- $s_i$ near $0$: point is on the boundary between two clusters
- $s_i$ near $-1$: point may be assigned to the wrong cluster

The overall silhouette score is the mean of $s_i$ across all points. It ranges from $-1$ to $+1$, with higher values indicating better-defined clusters.

## Limitations of K-Means

1. **K must be pre-specified**: requires domain knowledge or heuristic selection.
2. **Sensitive to initialization**: different random seeds yield different results; mitigated by K-Means++ and multiple restarts.
3. **Assumes spherical clusters**: K-Means uses Euclidean distance, so it finds convex, isotropic clusters. Non-spherical or elongated clusters are poorly captured.
4. **Scale-sensitive**: features with larger magnitudes dominate distance calculations; **always standardize/normalize** before clustering.
5. **Sensitive to outliers**: centroids (means) are pulled toward outliers. Alternatives: K-Medoids (uses median-like representatives).
6. **Hard assignments**: each point belongs to exactly one cluster. Fuzzy C-Means provides soft assignments.
7. **Curse of dimensionality**: Euclidean distance becomes less meaningful in very high dimensions; dimensionality reduction (PCA) is often applied first.

## Comparison with Other Clustering Algorithms

| Method | Strengths | Weaknesses | K needed? |
|--------|-----------|------------|-----------|
| **K-Means** | Fast, scalable, simple | Spherical clusters, need K | Yes |
| **DBSCAN** | Arbitrary shapes, finds outliers, no K needed | Struggles with varying densities, needs $\epsilon$ and `min_samples` | No |
| **Hierarchical** | Dendrogram visualization, no K needed | $O(n^2)$ memory, not scalable | No |
| **Gaussian Mixture** | Soft assignments, elliptical clusters | Assumes Gaussian distributions, slower | Yes |
| **Mean Shift** | No K needed, arbitrary shapes | Slow, bandwidth selection | No |

### DBSCAN (Density-Based Spatial Clustering of Applications with Noise)

- Groups points based on density: core points (at least `min_samples` within $\epsilon$ radius), border points, and noise/outliers
- Finds arbitrarily shaped clusters
- Robust to outliers (marks them as noise)
- Does not require pre-specifying K
- Struggles when clusters have very different densities

### Hierarchical Clustering

- Builds a tree (dendrogram) of clusters
- **Agglomerative** (bottom-up): each point starts as its own cluster; merge closest pairs
- **Divisive** (top-down): all points in one cluster; recursively split
- Linkage criteria: single-link (min distance), complete-link (max distance), average-link, Ward's method
- Dendrogram allows choosing K after the fact

## Real Applications

- **Customer Segmentation**: Group customers by purchasing behavior for targeted marketing
- **Image Compression**: Replace each pixel's color with its cluster centroid (color quantization)
- **Document Clustering**: Group similar documents for topic discovery
- **Anomaly Detection**: Points far from all centroids are potential anomalies
- **Market Basket Analysis**: Preprocessing step to group similar products or users
- **Genomics**: Cluster gene expression patterns

## Python sklearn Example

```python
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# Generate synthetic data with 4 clusters
X, y_true = make_blobs(n_samples=500, centers=4, cluster_std=0.8,
                       random_state=42)

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Elbow method: find optimal K
inertias = []
silhouette_scores = []
K_range = range(2, 10)

for k in K_range:
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    silhouette_scores.append(silhouette_score(X_scaled, labels))

# Find the best K by silhouette score
best_k = list(K_range)[np.argmax(silhouette_scores)]
print(f"Best K by silhouette score: {best_k}")

# Train final K-Means
kmeans = KMeans(n_clusters=best_k, init="k-means++", n_init=10,
                random_state=42)
y_pred = kmeans.fit_predict(X_scaled)

print(f"Inertia (WCSS): {kmeans.inertia_:.2f}")
print(f"Silhouette Score: {silhouette_score(X_scaled, y_pred):.3f}")

# Cluster centroids (in scaled space)
print("Centroids:", kmeans.cluster_centers_)

# Predict new data
new_points = np.array([[0, 0], [5, 5], [-3, 3]])
new_clusters = kmeans.predict(scaler.transform(new_points))
print(f"New point clusters: {new_clusters}")
```

## Key Hyperparameters (sklearn)

| Parameter | Description |
|-----------|-------------|
| `n_clusters` | Number of clusters $K$ (required) |
| `init` | Initialization: `"k-means++"` (default) or `"random"` |
| `n_init` | Number of restarts with different seeds; best is kept (default 10) |
| `max_iter` | Maximum iterations per run (default 300) |
| `tol` | Convergence tolerance based on centroid shift (default 1e-4) |
| `random_state` | Seed for reproducible results |

## Data Preprocessing Notes

- Always **standardize** (zero mean, unit variance) or **normalize** (min-max) features before K-Means
- For high-dimensional data (e.g., >100 features), apply PCA first to reduce noise
- Remove or handle outliers before clustering, as centroids are sensitive to them
- One-hot encode categorical features; consider Gower distance for mixed data types
