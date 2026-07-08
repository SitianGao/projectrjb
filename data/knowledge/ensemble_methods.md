# Ensemble Methods

## Ensemble Learning Concept

**Ensemble methods** combine multiple base learners (weak learners) to produce a stronger predictor. The fundamental principle is the **wisdom of the crowd**: aggregating diverse opinions reduces error. For ensembles to work, individual models must be:
- **Accurate** (better than random guessing)
- **Diverse** (make different errors)

Mathematically, if models have uncorrelated errors, averaging reduces variance by a factor of $1/M$ (where $M$ is the number of models). In practice, errors are never fully uncorrelated, but even partial decorrelation yields significant gains.

### Why Ensembles Work

The expected error of a model can be decomposed into three components (bias-variance-noise decomposition):

$$\text{Error} = \text{Bias}^2 + \text{Variance} + \text{Irreducible Noise}$$

Different ensemble strategies target different components:
- **Bagging** reduces variance
- **Boosting** reduces bias (and to some extent, variance)
- **Stacking** leverages the strengths of diverse models

## Bagging (Bootstrap Aggregating)

**Bagging** trains $M$ base models on $M$ different bootstrap samples of the training data. A bootstrap sample is created by randomly sampling $N$ instances **with replacement** from the original $N$ samples. This means each bootstrap sample contains approximately 63.2% of unique instances (the rest are duplicates).

### Bagging Algorithm

1. For $m = 1$ to $M$:
   - Draw bootstrap sample $D_m$ from training data $D$
   - Train base model $h_m$ on $D_m$
2. Aggregate predictions:
   - **Classification**: majority vote
   - **Regression**: average

### Why Bagging Works

Each base model sees slightly different data, inducing diversity. Averaging cancels out the high variance of individual models (like decision trees). The bias of the ensemble is roughly the bias of a single model, but variance is substantially reduced.

### Out-of-Bag (OOB) Error

For each bootstrap sample, approximately 36.8% of original instances are left out. These OOB samples can be used as a validation set — no need for a separate holdout set. For each data point, aggregate predictions from only the models for which it was OOB and compare to its true label. OOB error is an unbiased estimate of generalization error.

## Random Forest

**Random Forest** extends bagging with an additional source of randomness: at each tree split, only a random subset of $d$ features is considered (typically $d = \sqrt{n\_features}$ for classification, $d = n\_features/3$ for regression). This **feature randomness** decorrelates the trees further, reducing variance.

### Key Characteristics

- Base learner: **decision trees** (typically unpruned, deep trees)
- Combines bagging (sample randomness) with random subspace (feature randomness)
- Hyperparameters: `n_estimators` (number of trees), `max_features` (features per split)
- OOB error provides built-in validation
- Feature importance via mean decrease in impurity (MDI) or permutation importance
- Handles high-dimensional data well; no feature scaling required

### Random Forest vs Single Decision Tree

| Aspect | Decision Tree | Random Forest |
|--------|---------------|---------------|
| Variance | High | Low (averaged) |
| Interpretability | High (single tree) | Low (black box of trees) |
| Overfitting | Prone | Resistant |
| Training speed | Fast | Slower ($M$ trees) |
| Feature importance | Yes | Yes (more robust) |

## Boosting

**Boosting** sequentially trains weak learners, where each subsequent model focuses on the errors of its predecessors. Unlike bagging (parallel), boosting is inherently **sequential**.

### AdaBoost (Adaptive Boosting)

AdaBoost adjusts sample weights: misclassified samples get higher weights, forcing the next weak learner to focus on hard cases.

1. Initialize sample weights $w_i = 1/N$
2. For $m = 1$ to $M$:
   - Train weak learner $h_m$ on weighted data
   - Compute weighted error $\epsilon_m$
   - Compute model weight: $\alpha_m = \frac{1}{2} \ln\frac{1 - \epsilon_m}{\epsilon_m}$
   - Update sample weights: $w_i \leftarrow w_i \cdot \exp(-\alpha_m y_i h_m(x_i))$, then normalize
3. Final prediction: $\hat{y} = \text{sign}\left( \sum_m \alpha_m h_m(x) \right)$

AdaBoost is sensitive to noisy data and outliers (they get exponentially high weights).

### Gradient Boosting

Gradient Boosting generalizes the boosting idea: instead of reweighting samples, each new tree fits the **negative gradient** (residuals) of the loss function.

1. Initialize with a constant prediction $F_0(x) = \arg\min_\gamma \sum_i L(y_i, \gamma)$
2. For $m = 1$ to $M$:
   - Compute pseudo-residuals: $r_{im} = -\left[ \frac{\partial L(y_i, F(x_i))}{\partial F(x_i)} \right]_{F = F_{m-1}}$
   - Fit tree $h_m$ to residuals $r_{im}$
   - Compute step size $\gamma_m$ via line search
   - Update: $F_m(x) = F_{m-1}(x) + \eta \cdot \gamma_m \cdot h_m(x)$

where $\eta$ (learning rate, or shrinkage) controls contribution of each tree. Smaller $\eta$ requires more trees but generalizes better.

### XGBoost (eXtreme Gradient Boosting)

XGBoost is a highly optimized gradient boosting implementation with several innovations:

- **Regularization**: adds L1 and L2 penalty to leaf weights, reducing overfitting
- **Tree Pruning**: grows trees depth-first and prunes backward (using `gamma`, the minimum loss reduction for a split)
- **Handling Missing Values**: learns the best direction for missing values at each split
- **Weighted Quantile Sketch**: efficient approximate split finding for large data
- **Column Block Structure**: parallelized tree construction
- **Cache-Aware Access**: optimized memory layout for hardware efficiency
- **Out-of-Core Computing**: handles data that doesn't fit in memory
- **Custom Loss Functions**: supports user-defined objectives and evaluation metrics

XGBoost dominates structured/tabular data competitions and is a state-of-the-art baseline.

### LightGBM

LightGBM focuses on training speed and memory efficiency for large datasets:

- **GOSS (Gradient-based One-Side Sampling)**: keeps instances with large gradients (hard to fit) and randomly samples instances with small gradients (already well-fit), dramatically reducing data size while preserving information
- **EFB (Exclusive Feature Bundling)**: bundles mutually exclusive features (rarely non-zero together) to reduce dimensionality
- **Leaf-wise (best-first) tree growth**: grows the leaf with maximum loss reduction, yielding deeper, more asymmetric trees. More accurate but can overfit on small data
- Native support for categorical features (no one-hot encoding needed)

### CatBoost

CatBoost is designed for datasets with many categorical features:

- **Ordered Target Encoding**: uses a permutation-based approach to encode categorical features, avoiding target leakage (a common pitfall of naive target encoding)
- **Symmetric Trees**: all splits at a given level use the same feature and split value, enabling extremely fast inference
- **Ordered Boosting**: uses permutations to obtain unbiased gradient estimates
- Works well **out of the box** with minimal hyperparameter tuning

## Stacking (Stacked Generalization)

**Stacking** combines multiple base models (often of different types) via a **meta-learner**:

1. **Level 0**: Train diverse base models (e.g., Random Forest, SVM, Logistic Regression, XGBoost) on training data
2. **Level 1**: Train a meta-learner on the outputs (predictions) of the base models

The meta-learner learns the optimal way to combine base model predictions, leveraging each model's strengths. Cross-validation is used to generate "clean" out-of-fold predictions as training data for the meta-learner, preventing overfitting.

Common meta-learners: Logistic Regression, Ridge Regression, or a simple weighted average.

## Voting

Voting is the simplest ensemble: combine predictions from multiple models without a meta-learner.

- **Hard Voting**: each model votes for a class; majority wins (for classification)
- **Soft Voting**: average predicted probabilities; highest average probability wins. Generally outperforms hard voting because it accounts for prediction confidence.

Soft voting requires models that output probabilities (e.g., Random Forest with `predict_proba`).

## Bias-Variance Tradeoff in Ensembles

| Ensemble | Primary Effect | Mechanism |
|----------|---------------|-----------|
| Bagging | Reduces **variance** | Averaging de-correlated high-variance models |
| Random Forest | Reduces **variance** further | Adds feature randomness to decorrelate trees more |
| Boosting | Reduces **bias** (and variance) | Sequentially corrects errors; can reduce both |
| Stacking | Reduces both | Combines complementary strengths |

### Bias-Variance Intuition

- **High bias, low variance** (underfitting): model is too simple. Boosting helps, bagging does not.
- **Low bias, high variance** (overfitting): model is too complex. Bagging helps, boosting may overfit.
- Understanding this tradeoff is essential to choosing the right ensemble method.

## Algorithm Comparison Table

| Algorithm | Training | Handling Noise | Scalability | Interpretability | Hyperparameter Sensitivity |
|-----------|----------|---------------|-------------|-----------------|---------------------------|
| **Random Forest** | Parallel | Robust (averaging) | Good (parallel) | Low (black box) | Low |
| **AdaBoost** | Sequential | Sensitive (outlier weights explode) | Moderate | Moderate | Moderate |
| **Gradient Boosting** | Sequential | Moderate (learning rate) | Moderate | Low | High |
| **XGBoost** | Parallel-ish (column blocks) | Robust (regularization) | Excellent | Low | High |
| **LightGBM** | Parallel-ish | Robust | Excellent (large data) | Low | Moderate |
| **CatBoost** | Sequential | Robust | Good | Low | Low |
| **Stacking** | Parallel then sequential | Robust (diverse models) | Poor (many models) | Low | High |
| **Voting** | Parallel | Robust | Good | Moderate | Low |

## sklearn Examples

### Random Forest

```python
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score

X, y = make_classification(n_samples=1000, n_features=20, n_informative=15,
                           n_redundant=3, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    max_features="sqrt",     # sqrt(n_features) per split
    min_samples_split=5,
    oob_score=True,          # enable OOB error
    random_state=42,
    n_jobs=-1                # use all CPU cores
)
rf.fit(X_train, y_train)

print(f"Test Accuracy: {accuracy_score(y_test, rf.predict(X_test)):.3f}")
print(f"OOB Score: {rf.oob_score_:.3f}")

# Feature importance (top 5)
importances = rf.feature_importances_
for idx in importances.argsort()[-5:][::-1]:
    print(f"  Feature {idx}: {importances[idx]:.4f}")
```

### XGBoost

```python
import xgboost as xgb
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

X, y = make_classification(n_samples=1000, n_features=20, n_informative=15,
                           random_state=42)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# XGBoost with key hyperparameters
xgb_clf = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,          # shrinkage (eta)
    subsample=0.8,              # row sampling per tree
    colsample_bytree=0.8,       # column sampling per tree
    reg_alpha=0.1,              # L1 regularization
    reg_lambda=1.0,             # L2 regularization
    gamma=0,                    # min loss reduction for split
    objective="binary:logistic",
    eval_metric="logloss",
    early_stopping_rounds=10,
    random_state=42,
    n_jobs=-1
)

# Use eval_set for early stopping
xgb_clf.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=False
)

y_pred = xgb_clf.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")

# Feature importance from XGBoost
importance = xgb_clf.get_booster().get_score(importance_type="gain")
top5 = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
for feat, score in top5:
    print(f"  {feat}: {score:.2f}")
```

## When to Use Ensemble Methods

| Scenario | Recommended Method | Rationale |
|----------|-------------------|-----------|
| Tabular data, need robust baseline | Random Forest | Low tuning, handles noise well |
| Tabular data, maximize accuracy | XGBoost / LightGBM | State-of-the-art for structured data |
| Many categorical features | CatBoost | Native categorical handling |
| Very large dataset | LightGBM | GOSS and EFB for speed |
| Need well-calibrated probabilities | Random Forest + Platt scaling | Averaging stabilizes probabilities |
| Diverse model types available | Stacking | Leverages complementary strengths |
| Simple, quick ensemble | Voting | Easy to implement and interpret |
| Streaming / incremental data | Online boosting variants | Gradient boosting with partial_fit |
| Interpretability required | Single Decision Tree or small Random Forest | Ensemble interpretability tools (SHAP, LIME) |

## Practical Tips

1. **Start with Random Forest** as a baseline — minimal tuning, robust performance.
2. **Tune learning rate first** in boosting methods: $\eta \in [0.01, 0.3]$.
3. **`n_estimators` vs learning rate**: more trees with a lower learning rate generally produce better generalization (at the cost of training time).
4. **Early stopping** is essential for boosting to prevent overfitting.
5. **Cross-validate hyperparameters** — ensembles have many knobs; RandomizedSearchCV is often better than GridSearchCV for efficiency.
6. **Ensemble diversity matters more than individual model accuracy** — combining models that make different types of errors is more valuable than combining the best models that all make similar errors.
7. **For production**, XGBoost or LightGBM models are fast, have small serialized sizes, and integrate well with serving infrastructure.
