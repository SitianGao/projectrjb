# Model Evaluation: Measuring What Matters

Evaluation determines whether your model is good enough to deploy. The right metric depends on the problem — accuracy alone is often insufficient and sometimes dangerously misleading.

---

## 1. Train / Validation / Test Split

| Split | Purpose | Typical Ratio |
|-------|---------|---------------|
| **Training** | Fit model parameters | 70-80% |
| **Validation** | Tune hyperparameters, detect overfitting, select models | 10-15% |
| **Test** | Final unbiased estimate of generalization error | 10-15% |

**Key rule:** Touch the test set exactly once, at the very end. Repeatedly checking test performance leaks information and invalidates the estimate.

For small datasets (< 1000 samples), prefer cross-validation over a fixed holdout.

---

## 2. Cross-Validation

| Method | Description | Best For |
|--------|-------------|----------|
| **K-Fold** | Split into K folds; train on K-1, validate on the held-out fold. Repeat K times. | General purpose; K=5 or 10 |
| **Stratified K-Fold** | Preserves class distribution in each fold | Imbalanced classification — **always prefer over plain K-Fold** |
| **Leave-One-Out (LOO)** | K = N; each sample serves as validation once | Very small datasets; high variance, expensive |
| **Time Series Split** | Rolling-origin, forward-chaining; never validate on the past | Time series forecasting |

```python
from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
tscv = TimeSeriesSplit(n_splits=5)
```

---

## 3. Classification Metrics

### 3.1 Confusion Matrix

The foundation of all classification metrics:

|  | Predicted Positive | Predicted Negative |
|--|-------------------|-------------------|
| **Actual Positive** | TP (True Positive) | FN (False Negative) |
| **Actual Negative** | FP (False Positive) | TN (True Negative) |

### 3.2 Core Metrics

**Accuracy:**
$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

Simple but **misleading for imbalanced datasets.** A model that predicts "no disease" on a 99% healthy population achieves 99% accuracy and is useless.

**Precision (Positive Predictive Value):**
$$\text{Precision} = \frac{TP}{TP + FP}$$

"When I say positive, how often am I right?" **Use when FP is costly** — spam detection, recommendation systems where irrelevant recommendations hurt user trust.

**Recall (Sensitivity, True Positive Rate):**
$$\text{Recall} = \frac{TP}{TP + FN}$$

"How many actual positives did I catch?" **Use when FN is costly** — cancer screening, fraud detection, where missing a case is catastrophic.

**Specificity (True Negative Rate):**
$$\text{Specificity} = \frac{TN}{TN + FP}$$

"How many actual negatives did I correctly dismiss?" Pairs with recall for a full picture.

### 3.3 Combined Metrics

**F1-Score (Harmonic Mean of P and R):**
$$F_1 = 2 \times \frac{P \times R}{P + R}$$

Balances precision and recall. The harmonic mean penalizes extreme values more than the arithmetic mean — you can't cheat F1 by having P=1.0 and R=0.0.

**F-beta Score:** Generalizes F1 with a beta parameter. $F_\beta = (1 + \beta^2) \times \frac{P \times R}{(\beta^2 \times P) + R}$. $\beta > 1$ weights recall more (medical); $\beta < 1$ weights precision more (spam).

### 3.4 ROC Curve and AUC

The ROC curve plots **TPR (Recall)** vs **FPR (1 - Specificity)** at every classification threshold.

- AUC = 1.0: perfect classifier
- AUC > 0.9: excellent
- AUC 0.7–0.8: acceptable
- AUC < 0.7: poor
- AUC = 0.5: random guessing

**When to prefer PR Curve over ROC:** For highly imbalanced data, ROC-AUC can be deceptively optimistic. The Precision-Recall curve focuses on the minority class and gives a more honest picture.

**Log Loss (Cross-Entropy):**
$$-\frac{1}{N}\sum_{i=1}^{N} [y_i \log(\hat{p}_i) + (1 - y_i) \log(1 - \hat{p}_i)]$$

Measures the quality of predicted *probabilities*, not just hard labels. Heavily penalizes confident wrong predictions. Use when calibrated probabilities matter (risk assessment, bidding).

### 3.5 Advanced Metrics

**Matthews Correlation Coefficient (MCC):**
$$\text{MCC} = \frac{TP \times TN - FP \times FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}}$$

The only metric that gives a high score only when the model performs well on *all four* confusion matrix categories. Ranges from -1 to +1. Often the single best threshold metric for imbalanced binary classification.

**Cohen's Kappa:**
$$\kappa = \frac{p_o - p_e}{1 - p_e}$$

Measures agreement correcting for chance. $p_o$ = observed agreement, $p_e$ = expected agreement by chance.

---

## 4. Regression Metrics

| Metric | Formula | Properties |
|--------|---------|------------|
| **MSE** | $\frac{1}{n}\sum(y_i - \hat{y}_i)^2$ | Squared errors; heavily penalizes large errors; differentiable |
| **RMSE** | $\sqrt{\text{MSE}}$ | Same units as target; interpretable |
| **MAE** | $\frac{1}{n}\sum\|y_i - \hat{y}_i\|$ | Linear penalty; robust to outliers; not differentiable at zero |
| **R²** | $1 - \frac{SS_{res}}{SS_{tot}}$ | Proportion of variance explained; can be negative for models worse than a constant mean |
| **MAPE** | $\frac{100\%}{n}\sum\|\frac{y_i - \hat{y}_i}{y_i}\|$ | Percentage error, intuitive for business; undefined when $y_i = 0$, biased for small values |
| **Explained Variance** | $1 - \frac{\text{Var}(y - \hat{y})}{\text{Var}(y)}$ | Similar to R² but doesn't penalize bias |

**Choosing:** Use MAE when outliers are real and meaningful. Use MSE/RMSE when large errors are disproportionately worse (safety-critical). Use MAPE for stakeholder communication.

---

## 5. Clustering Metrics

### Internal (No Ground Truth)

| Metric | Formula | Interpretation |
|--------|---------|---------------|
| **Silhouette Score** | $\frac{b-a}{\max(a,b)}$ | $a$ = mean intra-cluster distance, $b$ = nearest-cluster distance. Range $[-1, 1]$; higher is better. |
| **Davies-Bouldin Index** | Avg similarity between each cluster and its most similar one | Lower is better; penalizes overlapping clusters |
| **Calinski-Harabasz** | Ratio of between-cluster to within-cluster dispersion | Higher is better; assumes spherical clusters |

### External (With Ground Truth)

- **Adjusted Rand Index (ARI):** Pair-counting measure, corrected for chance. Range $[-1, 1]$.
- **Normalized Mutual Information (NMI):** Information-theoretic; measures shared information between true and predicted labels.

---

## 6. Overfitting Detection and Learning Curves

**Overfitting signature:** Training loss continues decreasing while validation loss starts increasing. The gap between them grows.

**Underfitting signature:** Both training and validation loss remain high; the model hasn't learned the underlying pattern.

**Learning curves** plot performance against training set size:
- **High bias:** Both curves plateau at a low score, small gap between them. Solution: more complex model, more features.
- **High variance:** Large gap between training and validation curves. Solution: more data, regularization, simpler model.

---

## 7. Error Analysis

Beyond aggregate metrics, dig into *which* errors the model makes:

1. **Per-class breakdown:** Compute precision/recall for each class. Are some classes systematically misclassified?
2. **Confidence calibration:** Plot predicted probability vs actual frequency (reliability diagram).
3. **Worst-offender analysis:** Examine the highest-loss examples. Patterns often emerge — certain data sources, edge cases, labeling noise.
4. **Slice-based evaluation:** Evaluate on meaningful subgroups (e.g., by geography, device type, demographic).

---

## 8. Statistical Testing for Model Comparison

### McNemar's Test
Compares two classifiers on the same test set by counting discordant predictions. $H_0$: both classifiers have the same error rate.

### Paired t-Test (5x2cv)
Run 5 iterations of 2-fold cross-validation; compare the difference in scores with a paired t-test.

### Wilcoxon Signed-Rank Test
Non-parametric alternative to the paired t-test. Use when score differences aren't normally distributed.

### A/B Testing for Deployed Models
- Determine sample size via power analysis (minimal detectable effect, significance level $\alpha = 0.05$, power $= 0.80$)
- Randomly assign users to model A (control) and model B (treatment)
- Track a business metric (conversion, click-through), not just the ML metric
- Distinguish **statistical significance** ($p < 0.05$) from **practical significance** (effect large enough to justify the change)

---

## 9. Model Selection Decision Framework

```
Start Here
    |
    v
Is it classification?
    |-- Yes --> Is the dataset imbalanced?
    |              |-- Yes --> Optimize for F1/MCC/PR-AUC, use Stratified K-Fold
    |              |-- No  --> ROC-AUC is a solid default
    |
    |-- No  --> Is it regression?
    |              |-- Outliers matter? --> MAE
    |              |-- Large errors are worse? --> RMSE
    |              |-- Stakeholder communication? --> MAPE or R²
    |
    |-- No  --> Is it clustering?
                   |-- No ground truth? --> Silhouette + Davies-Bouldin
                   |-- Has ground truth? --> ARI + NMI
```

```python
from sklearn.metrics import classification_report, roc_auc_score, f1_score
from sklearn.model_selection import cross_validate

scores = cross_validate(model, X, y, cv=StratifiedKFold(5),
                        scoring=['accuracy', 'f1', 'roc_auc'],
                        return_train_score=True)
```
