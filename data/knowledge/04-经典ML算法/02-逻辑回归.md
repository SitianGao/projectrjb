# Logistic Regression

## Basic Concept

**Logistic Regression** is a supervised learning algorithm for binary classification. Despite its name, it is a classification model, not a regression model. It estimates the probability that a given sample belongs to a particular class using the **sigmoid function**.

Given input features $x$ and learned weights $w$, the model computes:

$$z = w^T x + b$$

The sigmoid function maps any real-valued $z$ to the interval $(0, 1)$:

$$\sigma(z) = \frac{1}{1 + e^{-z}}$$

The output $\hat{y} = \sigma(z)$ is interpreted as $P(y=1 \mid x)$, the probability that the sample belongs to the positive class.

### Properties of Sigmoid

- $\sigma(0) = 0.5$ — the default decision threshold
- $\sigma(z) \to 1$ as $z \to +\infty$
- $\sigma(z) \to 0$ as $z \to -\infty$
- Symmetric: $\sigma(-z) = 1 - \sigma(z)$
- Derivative: $\sigma'(z) = \sigma(z)(1 - \sigma(z))$ (useful for gradient computation)

## Decision Boundary

The decision boundary is the set of points where $\hat{y} = 0.5$, i.e., $w^T x + b = 0$. This is a **linear** hyperplane. Logistic regression is therefore a linear classifier — it can only separate classes that are linearly separable.

Classification rule (with default threshold 0.5):

$$\hat{y} = \begin{cases} 1 & \text{if } \sigma(w^T x + b) \geq 0.5 \\ 0 & \text{otherwise} \end{cases}$$

The threshold can be adjusted for different precision/recall trade-offs.

## Cross-Entropy Loss

Logistic regression is trained by minimizing the **binary cross-entropy (log-loss)**:

$$\mathcal{L}(w, b) = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \log(\hat{y}_i) + (1 - y_i) \log(1 - \hat{y}_i) \right]$$

where:
- $N$ is the number of training samples
- $y_i \in \{0, 1\}$ is the true label
- $\hat{y}_i = \sigma(w^T x_i + b)$ is the predicted probability

### Why Cross-Entropy?

Cross-entropy is the negative log-likelihood under the Bernoulli distribution assumption. It is convex (for linear models), ensuring gradient descent converges to the global optimum. Unlike MSE, cross-entropy produces strong gradients even when predictions are far from targets, speeding up convergence.

### Loss Derivation Intuition

- When $y_i = 1$: loss is $-\log(\hat{y}_i)$, penalizes predictions close to 0 heavily
- When $y_i = 0$: loss is $-\log(1 - \hat{y}_i)$, penalizes predictions close to 1 heavily
- Correct confident predictions ($\hat{y}_i$ near $y_i$) incur near-zero loss

## Gradient Descent Optimization

The gradient of cross-entropy loss with respect to weights $w$ is:

$$\frac{\partial \mathcal{L}}{\partial w} = \frac{1}{N} \sum_{i=1}^{N} (\hat{y}_i - y_i) x_i$$

The update rule is:

$$w := w - \eta \frac{\partial \mathcal{L}}{\partial w}$$

where $\eta$ is the learning rate. The gradient has a remarkably simple form — the error $(\hat{y}_i - y_i)$ multiplied by the input.

### Optimization Variants

- **Batch GD**: uses all $N$ samples per update (exact gradient, slow for large N)
- **SGD**: uses one sample per update (fast, noisy)
- **Mini-batch GD**: uses $m \ll N$ samples per update (best balance)
- **Advanced optimizers**: Adam, RMSprop, Momentum (adapt learning rate per parameter)

## Regularization

Regularization penalizes large weights to reduce overfitting:

- **L2 (Ridge)**: $\lambda \sum_j w_j^2$ — shrinks all weights toward zero, no sparsity
- **L1 (Lasso)**: $\lambda \sum_j |w_j|$ — drives some weights exactly to zero (feature selection)
- **Elastic Net**: combines L1 and L2: $\lambda_1 \sum |w_j| + \lambda_2 \sum w_j^2$

In sklearn, regularization strength is controlled by the inverse parameter $C = 1/\lambda$. Lower $C$ means stronger regularization.

## Multi-Class Classification

Logistic regression is inherently binary, but can be extended to $K > 2$ classes:

### One-vs-Rest (OvR)

Train $K$ binary classifiers, each distinguishing one class from all others. Final prediction is the class with the highest confidence score. Requires $K$ models but each uses all data.

### One-vs-One (OvO)

Train $\binom{K}{2}$ binary classifiers, one for each pair of classes. Each classifier votes; the class with the most votes wins. More models but each trained on only two classes' data.

### Softmax Regression (Multinomial Logistic Regression)

Directly models $P(y=k \mid x)$ for all $K$ classes using the softmax function:

$$P(y=k \mid x) = \frac{e^{w_k^T x + b_k}}{\sum_{j=1}^{K} e^{w_j^T x + b_j}}$$

Loss: **categorical cross-entropy**. Softmax regression learns a joint decision boundary (not separate like OvR). sklearn uses `multi_class="multinomial"`.

## Comparison with Other Models

### vs. Linear Regression

| Aspect | Logistic Regression | Linear Regression |
|--------|--------------------|--------------------|
| Output | Probability (0 to 1) | Continuous value |
| Loss | Cross-entropy | MSE |
| Task | Classification | Regression |
| Outlier sensitivity | Low (sigmoid clips) | High |

### vs. SVM

- Logistic Regression outputs **calibrated probabilities** natively; SVM requires Platt scaling
- SVM finds the maximum-margin hyperplane; LR maximizes likelihood
- SVM is more robust to outliers (hinge loss)
- Logistic regression is generally faster to train and scales better to large datasets

## Pros and Cons

**Pros:**
- Probabilistic output with well-calibrated probabilities
- Highly interpretable (coefficients map to feature importance)
- Computationally efficient (linear in number of features)
- Works well when classes are linearly separable
- Regularization easily incorporated
- No hyperparameter tuning required beyond regularization strength

**Cons:**
- Assumes linear relationship between features and log-odds
- Struggles with non-linear decision boundaries (needs feature engineering)
- Sensitive to multicollinearity
- Can underfit complex patterns (high bias, low variance)
- Requires feature scaling for regularized variants
- Binary only in its native form

## Key Hyperparameters (sklearn)

| Parameter | Description |
|-----------|-------------|
| `C` | Inverse of regularization strength (positive float, default 1.0) |
| `penalty` | Type of regularization: `"l1"`, `"l2"`, `"elasticnet"`, or `None` |
| `solver` | Optimization algorithm: `"lbfgs"`, `"saga"`, `"liblinear"`, etc. |
| `max_iter` | Maximum iterations for solver convergence (default 100) |
| `multi_class` | `"ovr"` (one-vs-rest) or `"multinomial"` (softmax) |
| `class_weight` | `"balanced"` for imbalanced datasets |

## Python sklearn Example

```python
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix

# Load data
X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Feature scaling (important for regularized LR)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train logistic regression
lr = LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=200)
lr.fit(X_train, y_train)

# Probabilities and predictions
y_prob = lr.predict_proba(X_test)[:, 1]  # P(y=1)
y_pred = lr.predict(X_test)

print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")

# Feature importance (absolute coefficient magnitude)
for feat, coef in sorted(
    zip(["mean radius", "mean texture", "mean perimeter", "mean area",
         "mean smoothness", "mean compactness", "mean concavity",
         "mean concave points", "mean symmetry", "mean fractal dimension",
         "radius error", "texture error", "perimeter error", "area error",
         "smoothness error", "compactness error", "concavity error",
         "concave points error", "symmetry error", "fractal dimension error",
         "worst radius", "worst texture", "worst perimeter", "worst area",
         "worst smoothness", "worst compactness", "worst concavity",
         "worst concave points", "worst symmetry", "worst fractal dimension"],
        lr.coef_[0]),
    key=lambda x: abs(x[1]), reverse=True
)[:5]:
    print(f"  {feat}: {coef:.3f}")
```

## Evaluation Metrics for Classification

Beyond accuracy, key metrics for evaluating logistic regression:

- **Precision**: $TP / (TP + FP)$ — how many positive predictions are correct
- **Recall**: $TP / (TP + FN)$ — how many actual positives are found
- **F1 Score**: harmonic mean of precision and recall
- **ROC-AUC**: area under the ROC curve, measures ranking quality
- **Log-Loss**: the cross-entropy loss itself, penalizes confidence errors
