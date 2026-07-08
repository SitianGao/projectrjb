# Decision Tree

## Basic Concept

A **Decision Tree** is a supervised learning algorithm used for both classification and regression. It recursively partitions the feature space into regions by asking a series of yes/no questions, represented as a tree structure. Each internal node tests a feature, each branch represents a test outcome, and each leaf node holds a class label (classification) or a continuous value (regression).

The goal is to build a tree that best separates classes by selecting the most informative features at each split.

## Splitting Criteria

The core of decision tree learning is choosing the optimal feature and threshold to split on at each node. Three primary impurity/quality measures are used.

### Entropy

Entropy measures the uncertainty or impurity of a dataset $D$. For a $K$-class problem:

$$H(D) = -\sum_{k=1}^{K} p_k \log_2 p_k$$

where $p_k$ is the proportion of samples belonging to class $k$. Entropy ranges from $0$ (pure, all same class) to $\log_2 K$ (maximally impure, uniform distribution).

### Information Gain

Information Gain measures the reduction in entropy after splitting on feature $A$:

$$IG(D, A) = H(D) - \sum_{v \in \text{Values}(A)} \frac{|D_v|}{|D|} H(D_v)$$

where $D_v$ is the subset of $D$ where feature $A$ takes value $v$. Higher IG means a more informative split. ID3 uses IG as its splitting criterion. IG biases toward features with many distinct values.

### Gain Ratio (C4.5)

C4.5 normalizes IG by the split's intrinsic information to reduce bias toward many-valued features:

$$GainRatio(D, A) = \frac{IG(D, A)}{-\sum_{v} \frac{|D_v|}{|D|} \log_2 \frac{|D_v|}{|D|}}$$

### Gini Index (CART)

Gini impurity is an alternative to entropy, used by CART:

$$Gini(D) = 1 - \sum_{k=1}^{K} p_k^2$$

Gini ranges from $0$ (pure) to $1 - 1/K$ (impure). It is computationally cheaper than entropy (no logarithms) and tends to isolate the most frequent class.

## Algorithm Comparison

### ID3 (Iterative Dichotomiser 3)

- Uses **Information Gain** as splitting criterion
- Handles only categorical features
- Does not handle missing values natively
- No pruning built in; tends to overfit
- Does not support regression

### C4.5

- Extension of ID3; uses **Gain Ratio**
- Handles both categorical and continuous features
- Can handle missing values
- Post-pruning via **reduced-error pruning**
- Supports rule post-processing (converting tree to rules)
- Slower than CART on large datasets

### CART (Classification and Regression Trees)

- Uses **Gini index** for classification, **MSE** for regression
- Produces only **binary** splits (binary tree)
- Handles categorical and continuous features
- Built-in **cost-complexity pruning**
- Computationally efficient
- Used by scikit-learn's `DecisionTreeClassifier` and `DecisionTreeRegressor`

## Pruning

Pruning reduces tree complexity to combat overfitting by removing branches that capture noise rather than signal.

### Pre-pruning (Early Stopping)

Stop growing the tree early based on constraints:
- `max_depth`: maximum tree depth
- `min_samples_split`: minimum samples required to split a node
- `min_samples_leaf`: minimum samples required at a leaf node
- `min_impurity_decrease`: minimum impurity decrease required for a split

**Advantage**: computationally efficient. **Disadvantage**: may underfit (stop too early).

### Post-pruning

Grow the full tree first, then prune back:
- **Cost-Complexity Pruning (CCP)**: penalizes tree complexity via parameter $\alpha$. Prunes the subtree that minimizes:

$$R_\alpha(T) = R(T) + \alpha |T|$$

where $R(T)$ is the misclassification error and $|T|$ is the number of leaf nodes.
- **Reduced-Error Pruning**: hold out a validation set; prune nodes whose removal does not degrade validation accuracy.

## Overfitting in Decision Trees

Decision trees are prone to overfitting because they can grow until each leaf contains a single sample (zero training error but poor generalization). Common fixes:
- Pruning (pre- or post-)
- Ensemble methods (Random Forest, Gradient Boosting)
- Set a minimum number of samples per leaf
- Limit tree depth

## Pros and Cons

**Pros:**
- Highly interpretable and visualizable
- Minimal data preprocessing (no scaling, no one-hot encoding required for CART)
- Handles both numerical and categorical data
- Feature importance is trivially available
- Robust to outliers and missing values (C4.5, CART)

**Cons:**
- Prone to overfitting without pruning
- Sensitive to small data variations (high variance)
- Greedy algorithm; does not guarantee global optimum
- Biased toward features with many levels (mitigated by gain ratio)
- Decision boundaries are axis-aligned (not smooth)

## Key Hyperparameters (sklearn)

| Parameter | Description |
|-----------|-------------|
| `criterion` | Splitting criterion: `"gini"` or `"entropy"` |
| `max_depth` | Maximum tree depth; `None` = unlimited |
| `min_samples_split` | Minimum samples to split a node (default 2) |
| `min_samples_leaf` | Minimum samples at a leaf node (default 1) |
| `max_features` | Number of features to consider for each split |
| `ccp_alpha` | Cost-complexity pruning parameter |
| `class_weight` | Class weights for imbalanced data |

## Python sklearn Example

```python
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Load data
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train decision tree with pre-pruning
dt = DecisionTreeClassifier(
    criterion="entropy",
    max_depth=4,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42
)
dt.fit(X_train, y_train)

# Evaluate
y_pred = dt.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")

# Feature importance
for name, imp in zip(["sepal_length", "sepal_width", "petal_length", "petal_width"],
                     dt.feature_importances_):
    print(f"  {name}: {imp:.3f}")
```

## Computational Complexity

- **Training**: $O(n \cdot m \log m)$ where $n$ is features and $m$ is samples (assuming balanced tree)
- **Prediction**: $O(\log m)$ per sample
- Decision trees are among the fastest models to train and predict
