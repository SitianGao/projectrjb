# Scikit-Learn Basics

Scikit-learn is the standard Python library for machine learning. It is built on NumPy and SciPy, and follows a consistent API design pattern.

## Core API Design Pattern

Every model in scikit-learn follows these conventions:

| Method | Purpose | Used by |
|--------|---------|---------|
| `fit(X, y)` | Learn from data | Estimators, Classifiers, Regressors |
| `predict(X)` | Make predictions | Classifiers, Regressors |
| `transform(X)` | Apply a learned transformation | Preprocessors, PCA |
| `fit_transform(X)` | Learn and apply in one step | Preprocessors (more efficient) |
| `score(X, y)` | Evaluate model performance | Classifiers (accuracy), Regressors (R²) |

Three core concepts:
- **Estimator**: Any object that learns from data (has a `fit()` method).
- **Transformer**: An estimator that also transforms data (has `transform()`).
- **Predictor**: An estimator that makes predictions (has `predict()`).

```python
import sklearn
print(sklearn.__version__)  # Check version
```

## Data Splitting

```python
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y  # stratify preserves class ratios
)

# K-fold cross-validation
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy')
print(f'CV Accuracy: {cv_scores.mean():.3f} +/- {cv_scores.std():.3f}')
```

## Preprocessing

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder

# Standardization (mean=0, std=1) -- required for SVM, logistic regression, neural nets
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # Fit on train, transform train
X_test_scaled = scaler.transform(X_test)          # Only transform test (use train's params!)

# Min-Max scaling (values in [0, 1]) -- useful for neural networks, image data
minmax = MinMaxScaler(feature_range=(0, 1))
X_scaled = minmax.fit_transform(X)

# Label encoding (string → integer) -- for target variables
le = LabelEncoder()
y_encoded = le.fit_transform(['cat', 'dog', 'cat', 'bird'])
# → [0, 1, 0, 2]  (alphabetical order: bird=0, cat=1, dog=2)

# One-hot encoding (integer → binary columns) -- for categorical features
ohe = OneHotEncoder(sparse_output=False)
categorical_encoded = ohe.fit_transform(categorical_column.reshape(-1, 1))
# bird  → [1, 0, 0]
# cat   → [0, 1, 0]
# dog   → [0, 0, 1]
```

## Pipeline and ColumnTransformer

Pipelines chain preprocessing and modeling steps, preventing data leakage:

```python
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.compose import ColumnTransformer

# Simple pipeline
pipe = make_pipeline(StandardScaler(), LogisticRegression())
pipe.fit(X_train, y_train)
pipe.score(X_test, y_test)   # One object handles everything

# Mixed column types: numeric + categorical
numeric_features = ['age', 'income', 'credit_score']
categorical_features = ['city', 'education', 'gender']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
    ]
)

full_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])
full_pipeline.fit(X_train, y_train)
```

## Key Classification Models

```python
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier

# Logistic Regression: linear, probabilistic, fast. Good baseline for binary classification.
lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
lr.predict_proba(X_test)  # Returns probability for each class

# SVM: works well on high-dimensional data, can use kernels for non-linear separation
svm = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True)  # probability=True for predict_proba

# Random Forest: ensemble of decision trees, robust, handles non-linear relationships well
rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
# Feature importance
importances = rf.feature_importances_   # Which features matter most?

# K-Nearest Neighbors: simple, non-parametric, good when local patterns matter
knn = KNeighborsClassifier(n_neighbors=5, metric='euclidean')

# Quick comparison (model selection)
models = {'LR': lr, 'SVM': svm, 'RF': rf, 'KNN': knn}
for name, model in models.items():
    model.fit(X_train, y_train)
    print(f'{name}: Train={model.score(X_train, y_train):.3f}, Test={model.score(X_test, y_test):.3f}')
```

## Key Regression Models

```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR

# Linear: OLS (ordinary least squares), interpretable coefficients
lr = LinearRegression()
lr.fit(X_train, y_train)
print('Coefficients:', lr.coef_, 'Intercept:', lr.intercept_)

# Ridge: linear regression with L2 regularization (shrinks coefficients, prevents overfitting)
ridge = Ridge(alpha=1.0)

# Lasso: linear regression with L1 regularization (can zero out coefficients → feature selection)
lasso = Lasso(alpha=0.1)

# SVR: Support Vector Regression, good for non-linear relationships
svr = SVR(kernel='rbf', C=1.0, epsilon=0.1)
```

## Clustering

```python
from sklearn.cluster import KMeans, DBSCAN

# KMeans: partition into k groups, fast and scalable
km = KMeans(n_clusters=3, random_state=42, n_init=10)
labels = km.fit_predict(X)        # Returns cluster labels (0, 1, 2, ...)
centroids = km.cluster_centers_   # Center of each cluster
inertia = km.inertia_             # Sum of squared distances (lower is tighter)

# DBSCAN: density-based, finds arbitrary shapes, handles noise (label=-1)
dbs = DBSCAN(eps=0.5, min_samples=5)
labels = dbs.fit_predict(X)
n_noise = (labels == -1).sum()    # Number of outlier points
```

## Dimensionality Reduction

```python
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# PCA: linear projection to maximize variance (good for feature reduction, visualization)
pca = PCA(n_components=2)     # Reduce to 2 dimensions
X_pca = pca.fit_transform(X_scaled)
print('Explained variance ratio:', pca.explained_variance_ratio_)
print('Total variance retained:', pca.explained_variance_ratio_.sum())

# t-SNE: non-linear, great for visualization, but stochastic and slow on large data
tsne = TSNE(n_components=2, random_state=42, perplexity=30)
X_tsne = tsne.fit_transform(X_scaled)
```

## Model Evaluation

```python
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, roc_curve, r2_score, mean_squared_error
)

# Classification metrics
y_pred = model.predict(X_test)
print('Accuracy:', accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))     # Precision, Recall, F1 per class
print('Confusion Matrix:\n', confusion_matrix(y_test, y_pred))

# ROC-AUC (for binary classification, needs probabilities)
y_prob = model.predict_proba(X_test)[:, 1]  # Probability of positive class
auc = roc_auc_score(y_test, y_prob)
fpr, tpr, thresholds = roc_curve(y_test, y_prob)

# Regression metrics
y_pred_reg = reg_model.predict(X_test)
print('R² Score:', r2_score(y_test, y_pred_reg))             # 1.0 = perfect
print('MSE:', mean_squared_error(y_test, y_pred_reg))        # Lower is better
print('RMSE:', np.sqrt(mean_squared_error(y_test, y_pred_reg)))
```

## Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

# Grid search: exhaustive search over specified values (slow on large grids)
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, None],
    'min_samples_split': [2, 5, 10]
}
grid = GridSearchCV(RandomForestClassifier(random_state=42),
                    param_grid, cv=5, scoring='accuracy', n_jobs=-1)
grid.fit(X_train, y_train)
print('Best params:', grid.best_params_)
print('Best CV score:', grid.best_score_)
best_model = grid.best_estimator_     # Already refitted on full training data

# Randomized search: sample from distributions (faster for large search spaces)
from scipy.stats import randint, uniform
param_dist = {
    'n_estimators': randint(50, 500),
    'max_depth': [5, 10, 15, None],
    'min_samples_split': randint(2, 20)
}
random_search = RandomizedSearchCV(RandomForestClassifier(random_state=42),
                                   param_dist, n_iter=20, cv=5, scoring='accuracy',
                                   random_state=42, n_jobs=-1)
random_search.fit(X_train, y_train)
```

## Model Persistence

```python
import joblib

# Save
joblib.dump(model, 'model.joblib')
joblib.dump(scaler, 'scaler.joblib')
joblib.dump(full_pipeline, 'pipeline.joblib')

# Load
model = joblib.load('model.joblib')
scaler = joblib.load('scaler.joblib')
predictions = model.predict(scaler.transform(X_new))
```

## Complete Mini-Workflow Example

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# 1. Load data
df = pd.read_csv('students.csv')
X = df.drop('pass_exam', axis=1)
y = df['pass_exam']

# 2. Identify column types
numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()

# 3. Build preprocessing + model pipeline
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_cols),
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols),
])
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

# 4. Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# 5. Train
pipeline.fit(X_train, y_train)

# 6. Evaluate
y_pred = pipeline.predict(X_test)
print('=== Classification Report ===')
print(classification_report(y_test, y_pred))
print('=== Confusion Matrix ===')
print(confusion_matrix(y_test, y_pred))

# 7. Cross-validation for robustness
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
print(f'5-Fold CV Accuracy: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}')

# 8. Save for deployment
joblib.dump(pipeline, 'student_exam_predictor.joblib')
print('Model saved to student_exam_predictor.joblib')
```
