# Feature Engineering: Crafting Signals from Raw Data

Feature engineering is the process of transforming raw data into representations that make patterns more visible to machine learning algorithms. In practice, excellent features often beat fancier models — a well-engineered feature set on logistic regression can outperform a deep neural network on raw inputs.

---

## 1. Why Feature Engineering Matters

Good features:
- **Reduce model complexity:** Linear relationships become learnable without deep architectures
- **Improve generalization:** Domain-informed features are less prone to spurious correlations
- **Reduce data requirements:** Strong features mean less data needed for the same performance

A famous Kaggle adage: *"More data beats better algorithms, but better features beat more data."*

---

## 2. Feature Creation

### 2.1 Domain Knowledge Features

The most powerful features come from understanding the problem:
- **Finance:** Debt-to-income ratio, price-to-earnings, moving average convergence divergence (MACD)
- **Healthcare:** BMI ($\frac{weight}{height^2}$), eGFR, APACHE scores
- **E-commerce:** Cart abandonment rate, customer lifetime value, recency-frequency-monetary (RFM)

### 2.2 Polynomial and Interaction Features

Generate nonlinear combinations of existing features:

$$x^2, \quad x_1 x_2, \quad x_1^2 x_2$$

Degree-2 interactions capture multiplicative relationships. Degree-3 is rarely worth the explosion in dimensionality.

```python
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2, interaction_only=False, include_bias=False)
```

**Caution:** $n$ features become $\binom{n+d}{d}$ features. With 100 features and degree 2, that's 5151 features. Use feature selection afterward.

### 2.3 Ratio and Combination Features

Simple arithmetic on existing columns:
- $x_1 / (x_2 + \epsilon)$ — rates, densities, efficiencies
- $x_a - x_b$ — differences or deltas
- $\frac{x - \mu_{group}}{\sigma_{group}}$ — group-normalized features

### 2.4 Binning / Discretization

Convert continuous features into categorical bins:
| Method | How It Works | Use Case |
|--------|-------------|----------|
| **Equal-width** | Uniform bin intervals | Simple; sensitive to outliers |
| **Equal-frequency (quantile)** | Same number of samples per bin | Robust; equalizes information per bin |
| **Decision-tree based** | Bins optimized to split target | Best for predictive power; risk of overfitting |

```python
from sklearn.preprocessing import KBinsDiscretizer
kbins = KBinsDiscretizer(n_bins=5, encode='ordinal', strategy='quantile')
```

### 2.5 Datetime Feature Extraction

Raw timestamps carry rich cyclical and categorical signals:

| Feature | Extraction | Encoding |
|---------|-----------|----------|
| Day of week | `dt.dayofweek` | 0–6 |
| Month | `dt.month` | 1–12 |
| Quarter | `dt.quarter` | 1–4 |
| Is weekend | `dt.dayofweek >= 5` | 0/1 |
| Hour (cyclical) | $\sin(2\pi \cdot \frac{hour}{24})$, $\cos(2\pi \cdot \frac{hour}{24})$ | Continuous, preserves "23:00 is close to 00:00" |

**Cyclical encoding** is critical for time features — it prevents the model from treating hour 23 and hour 0 as maximally distant. Apply it to hour, day of week, month, and wind direction.

```python
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
```

### 2.6 Text Features (Beyond Embeddings)

Simple aggregative features from text before or alongside vectorization:
- Character count, word count, sentence count
- Average word length, punctuation ratio, uppercase ratio
- Readability scores (Flesch-Kincaid, Gunning Fog)
- Sentiment score (VADER, TextBlob)
- Named entity count (persons, organizations, locations)

### 2.7 Geographic Features

- **Haversine distance:** Great-circle distance between two lat/lon pairs
- **Geohash:** Hierarchical spatial encoding; neighboring locations share prefixes
- **Distance to nearest landmark:** Airport, city center, hospital

---

## 3. Feature Selection

### 3.1 Filter Methods (Fast, Univariate)

Evaluate each feature independently against the target:

| Method | For | Statistic |
|--------|-----|-----------|
| **Variance Threshold** | All | Remove features with variance below threshold |
| **Pearson Correlation** | Regression | $r = \frac{\text{cov}(X, y)}{\sigma_X \sigma_y}$ |
| **Mutual Information** | Both | $I(X; y)$ — captures nonlinear dependencies |
| **Chi-Squared** | Classification | $\chi^2$ test of independence |
| **ANOVA F-test** | Classification | $F = \frac{\text{between-group variance}}{\text{within-group variance}}$ |

```python
from sklearn.feature_selection import SelectKBest, mutual_info_classif, f_classif
selector = SelectKBest(score_func=mutual_info_classif, k=20)
```

### 3.2 Wrapper Methods (Greedy Search)

| Method | Approach | Cost |
|--------|----------|------|
| **RFE (Recursive Feature Elimination)** | Train model, drop least important feature, repeat | Moderate; model-dependent |
| **Forward Selection** | Start empty, add best feature each iteration | $O(kp)$ model trainings |
| **Backward Elimination** | Start with all, remove worst each iteration | Expensive for large p |

```python
from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestClassifier
rfe = RFE(RandomForestClassifier(), n_features_to_select=30)
```

### 3.3 Embedded Methods (During Training)

| Method | How It Selects | Notes |
|--------|---------------|-------|
| **Lasso (L1)** | Drives coefficients to exactly zero | Built-in feature selection; $\lambda$ controls sparsity |
| **Ridge (L2)** | Shrinks coefficients but keeps all | Good when all features contribute |
| **ElasticNet** | Mix of L1 and L2 | Best of both worlds |
| **Tree Feature Importance** | Mean impurity decrease across splits | Fast; biased toward high-cardinality features |
| **Permutation Importance** | Drop in performance when feature is shuffled | Model-agnostic; more reliable than impurity-based |

**Permutation importance** is strongly recommended over built-in feature importance for tree models — it measures actual predictive contribution rather than split frequency.

```python
from sklearn.inspection import permutation_importance
result = permutation_importance(model, X_val, y_val, n_repeats=10, random_state=42)
```

### 3.4 Advanced Selection Methods

**Boruta:** Trains on shuffled copies of features (shadow features) and keeps only those that outperform their random counterparts. More conservative than RFE — retains all relevant features including redundant ones.

**Stability Selection:** Run Lasso on random subsamples many times; keep features selected with high frequency. Robust to perturbations and provides false-positive control.

---

## 4. Feature Transformation

| Method | When to Use | Effect |
|--------|-------------|--------|
| **Log $\log(x + c)$** | Right-skewed, positive data | Pulls in long tail |
| **Square Root $\sqrt{x}$** | Count data | Stabilizes variance (Poisson) |
| **Box-Cox** | Positive data | Optimizes normality via MLE |
| **Quantile Transformer** | Any continuous | Maps to uniform or normal distribution; fully rank-based |
| **Discretization** | Nonlinear relationships | Linear models learn piecewise patterns |

A common pattern: try `QuantileTransformer(output_distribution='normal')` as a preprocessing step before linear models — it often outperforms StandardScaler for skewed features.

---

## 5. Dimensionality Reduction

### 5.1 PCA (Principal Component Analysis)

Finds orthogonal directions of maximum variance. Linear, fast, and interpretable (loadings show which features contribute to each component).

```python
from sklearn.decomposition import PCA
pca = PCA(n_components=0.95)  # retain 95% of variance
```

**Use for:** Preprocessing before clustering, speeding up models, removing multicollinearity. **Always scale data first.**

### 5.2 Kernel PCA

Nonlinear extension of PCA via the kernel trick. Useful when data lies on a nonlinear manifold. Compute cost is $O(n^3)$ for full decomposition.

### 5.3 TruncatedSVD

Equivalent to PCA but works on sparse matrices without densifying. Essential for dimensionality reduction on TF-IDF or one-hot matrices.

```python
from sklearn.decomposition import TruncatedSVD
svd = TruncatedSVD(n_components=100)
```

### 5.4 t-SNE and UMAP (Visualization)

**t-SNE:** Preserves local structure excellently. Not suitable as preprocessing for downstream models — the embedding is non-parametric and doesn't generalize to new points.

**UMAP:** Preserves more global structure than t-SNE. Faster, scales better. Also primarily a visualization tool, though the parametric variant (parametric UMAP) can learn a mapping.

### 5.5 Autoencoders

Neural networks trained to reconstruct their input through a bottleneck. The bottleneck layer provides a learned nonlinear dimensionality reduction. Useful when PCA fails to capture the data manifold.

---

## 6. Handling High-Cardinality Categorical Features

When a categorical feature has hundreds or thousands of unique values (zip codes, product IDs, user IDs):

| Method | How It Works | Pros/Cons |
|--------|-------------|-----------|
| **Target Encoding** | Replace with smoothed mean of target | Powerful but prone to overfitting; use CV |
| **Count Encoding** | Replace with frequency rank | No target leakage; lossy |
| **Entity Embeddings** | Learn dense vector per category via NN | State of the art; requires deep learning |
| **CatBoost Encoding** | Ordered target encoding | Reduces overfitting; CatBoost's default |

---

## 7. Feature Interaction Detection

After building a model, analyze which features interact:

- **Friedman's H-statistic:** Measures interaction strength between features. Computationally expensive ($O(n^2)$ pairs).
- **SHAP Interaction Values:** Decomposes predictions into main effects and pairwise interactions. Model-agnostic for tree models.

```python
import shap
explainer = shap.TreeExplainer(model)
shap_interaction = explainer.shap_interaction_values(X)
```

---

## 8. Automated Feature Engineering

| Tool | Approach | When |
|------|----------|------|
| **Featuretools (DFS)** | Deep Feature Synthesis: stacks primitives (sum, mean, time_since) across relational tables | Relational/temporal data with multiple tables |
| **auto-sklearn** | Bayesian optimization over preprocessing + model pipeline | Hands-off AutoML |
| **tsfresh** | Extracts 1000+ time series features (Fourier coefficients, entropy, change points) | Time series classification |

---

## 9. Pipeline Integration

Feature engineering must live inside the pipeline to prevent leakage:

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

def create_features(df):
    df = df.copy()
    df['ratio'] = df['a'] / (df['b'] + 1e-6)
    df['day_sin'] = np.sin(2 * np.pi * df['day'] / 7)
    return df

fe_pipe = Pipeline([
    ('features', FunctionTransformer(create_features, validate=False)),
    ('scaler', StandardScaler()),
    ('selector', SelectFromModel(LassoCV())),
    ('model', LogisticRegression())
])
```

---

## 10. Common Mistakes and Best Practices

1. **Data Leakage in Feature Creation:** Computing group means or target encodings on the full dataset before splitting leaks target information. Always fit feature engineering on the training split only.
2. **Too Many Features:** Adding features without selection leads to the curse of dimensionality, overfitting, and slow training. Always follow creation with selection.
3. **Ignoring Feature Distributions:** Applying PCA or linear models to heavily skewed features without transformation degrades results.
4. **One-Hot Explosion:** 1000+ categories become 1000+ sparse columns. Use target encoding or embeddings instead.
5. **Cyclical Features as Ordinal:** Encoding month as 1-12 makes January maximally distant from December. Always use sine/cosine pairs.
6. **Feature Drift in Production:** Features engineered from data distributions (standardization, target encoding) must be monitored — if the distribution shifts, the feature representation degrades.
7. **Premature Dimensionality Reduction:** Try models with raw features first. If performance is adequate, reduced interpretability isn't worth the dimensionality savings.

---

## 11. Real-World Case Study (Kaggle-Style)

**Problem:** Predict taxi fare from pickup/dropoff coordinates, timestamp, and passenger count.

*Baseline:* Linear regression on raw features — RMSE $8.50.

*Feature engineering applied:*
1. Haversine distance between pickup and dropoff (replaces raw coordinates)
2. Hour (cyclical sin/cos), day of week, is_weekend
3. Manhattan distance as a proxy for route complexity
4. Distance-to-airport (pickup within 2km of JFK/LGA/EWR)
5. Log-transform fare (target is right-skewed)

*Result:* Same linear regression — RMSE $3.20, a **62% reduction** in error, with no model change. This is the power of feature engineering.
