# Scikit-Learn基础

Scikit-learn是Python机器学习领域的标准库。它构建在NumPy和SciPy之上，并遵循一致的API设计模式。

## 核心API设计模式

scikit-learn中的每个模型都遵循以下约定：

| 方法 | 用途 | 使用者 |
|--------|---------|---------|
| `fit(X, y)` | 从数据中学习 | Estimator、分类器、回归器 |
| `predict(X)` | 进行预测 | 分类器、回归器 |
| `transform(X)` | 应用已学习的变换 | 预处理器、PCA |
| `fit_transform(X)` | 一步完成学习并应用 | 预处理器（更高效） |
| `score(X, y)` | 评估模型性能 | 分类器（准确率）、回归器（R²） |

三个核心概念：
- **Estimator（估计器）**：任何从数据中学习的对象（具有 `fit()` 方法）。
- **Transformer（变换器）**：同时也能变换数据的估计器（具有 `transform()`）。
- **Predictor（预测器）**：能进行预测的估计器（具有 `predict()`）。

```python
import sklearn
print(sklearn.__version__)  # 检查版本
```

## 数据划分

```python
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y  # stratify保持类别比例
)

# K折交叉验证
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy')
print(f'CV Accuracy: {cv_scores.mean():.3f} +/- {cv_scores.std():.3f}')
```

## 预处理

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder

# 标准化（均值=0，标准差=1）-- SVM、逻辑回归、神经网络所必需
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # 在训练集上拟合，然后变换训练集
X_test_scaled = scaler.transform(X_test)          # 仅变换测试集（使用训练集的参数！）

# Min-Max缩放（值映射到 [0, 1]）-- 适用于神经网络、图像数据
minmax = MinMaxScaler(feature_range=(0, 1))
X_scaled = minmax.fit_transform(X)

# 标签编码（字符串 → 整数）-- 用于目标变量
le = LabelEncoder()
y_encoded = le.fit_transform(['cat', 'dog', 'cat', 'bird'])
# → [0, 1, 0, 2]  （按字母顺序：bird=0, cat=1, dog=2）

# 独热编码（整数 → 二进制列）-- 用于分类特征
ohe = OneHotEncoder(sparse_output=False)
categorical_encoded = ohe.fit_transform(categorical_column.reshape(-1, 1))
# bird  → [1, 0, 0]
# cat   → [0, 1, 0]
# dog   → [0, 0, 1]
```

## 流水线与ColumnTransformer

流水线将预处理和建模步骤串联起来，防止数据泄露：

```python
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.compose import ColumnTransformer

# 简单流水线
pipe = make_pipeline(StandardScaler(), LogisticRegression())
pipe.fit(X_train, y_train)
pipe.score(X_test, y_test)   # 一个对象处理所有事情

# 混合列类型：数值型 + 分类型
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

## 关键分类模型

```python
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier

# 逻辑回归：线性、概率型、速度快。是二分类任务的良好基线模型。
lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
lr.predict_proba(X_test)  # 返回每个类别的概率

# SVM：在高维数据上表现良好，可使用核函数进行非线性分离
svm = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True)  # probability=True启用predict_proba

# 随机森林：决策树的集成，鲁棒性强，能很好地处理非线性关系
rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
# 特征重要性
importances = rf.feature_importances_   # 哪些特征最重要？

# K近邻：简单、非参数化，适用于局部模式重要的场景
knn = KNeighborsClassifier(n_neighbors=5, metric='euclidean')

# 快速模型对比（模型选择）
models = {'LR': lr, 'SVM': svm, 'RF': rf, 'KNN': knn}
for name, model in models.items():
    model.fit(X_train, y_train)
    print(f'{name}: Train={model.score(X_train, y_train):.3f}, Test={model.score(X_test, y_test):.3f}')
```

## 关键回归模型

```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR

# 线性回归：OLS（普通最小二乘法），系数可解释
lr = LinearRegression()
lr.fit(X_train, y_train)
print('Coefficients:', lr.coef_, 'Intercept:', lr.intercept_)

# Ridge回归：带L2正则化的线性回归（缩小系数，防止过拟合）
ridge = Ridge(alpha=1.0)

# Lasso回归：带L1正则化的线性回归（可将系数压缩为零 → 特征选择）
lasso = Lasso(alpha=0.1)

# SVR：支持向量回归，适用于非线性关系
svr = SVR(kernel='rbf', C=1.0, epsilon=0.1)
```

## 聚类

```python
from sklearn.cluster import KMeans, DBSCAN

# KMeans：将数据划分为k组，快速且可扩展
km = KMeans(n_clusters=3, random_state=42, n_init=10)
labels = km.fit_predict(X)        # 返回聚类标签 (0, 1, 2, ...)
centroids = km.cluster_centers_   # 每个聚类的中心
inertia = km.inertia_             # 平方距离之和（越小表示聚类越紧密）

# DBSCAN：基于密度，可发现任意形状的聚类，能够处理噪声（标签=-1）
dbs = DBSCAN(eps=0.5, min_samples=5)
labels = dbs.fit_predict(X)
n_noise = (labels == -1).sum()    # 离群点数量
```

## 降维

```python
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# PCA：线性投影以最大化方差（适用于特征缩减、可视化）
pca = PCA(n_components=2)     # 降维到2维
X_pca = pca.fit_transform(X_scaled)
print('Explained variance ratio:', pca.explained_variance_ratio_)
print('Total variance retained:', pca.explained_variance_ratio_.sum())

# t-SNE：非线性降维，非常适合可视化，但具有随机性且在大型数据上较慢
tsne = TSNE(n_components=2, random_state=42, perplexity=30)
X_tsne = tsne.fit_transform(X_scaled)
```

## 模型评估

```python
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, roc_curve, r2_score, mean_squared_error
)

# 分类指标
y_pred = model.predict(X_test)
print('Accuracy:', accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))     # 每个类别的精确率、召回率、F1值
print('Confusion Matrix:\n', confusion_matrix(y_test, y_pred))

# ROC-AUC（用于二分类，需要概率值）
y_prob = model.predict_proba(X_test)[:, 1]  # 正类的概率
auc = roc_auc_score(y_test, y_prob)
fpr, tpr, thresholds = roc_curve(y_test, y_prob)

# 回归指标
y_pred_reg = reg_model.predict(X_test)
print('R² Score:', r2_score(y_test, y_pred_reg))             # 1.0 = 完美
print('MSE:', mean_squared_error(y_test, y_pred_reg))        # 越小越好
print('RMSE:', np.sqrt(mean_squared_error(y_test, y_pred_reg)))
```

## 超参数调优

```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

# 网格搜索：对指定值进行穷举搜索（在大型网格上速度较慢）
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
best_model = grid.best_estimator_     # 已在整个训练数据上重新拟合

# 随机搜索：从分布中采样（对于大型搜索空间更快）
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

## 模型持久化

```python
import joblib

# 保存
joblib.dump(model, 'model.joblib')
joblib.dump(scaler, 'scaler.joblib')
joblib.dump(full_pipeline, 'pipeline.joblib')

# 加载
model = joblib.load('model.joblib')
scaler = joblib.load('scaler.joblib')
predictions = model.predict(scaler.transform(X_new))
```

## 完整小型工作流示例

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

# 1. 加载数据
df = pd.read_csv('students.csv')
X = df.drop('pass_exam', axis=1)
y = df['pass_exam']

# 2. 识别列类型
numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()

# 3. 构建预处理 + 模型流水线
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_cols),
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols),
])
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

# 4. 划分数据
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# 5. 训练
pipeline.fit(X_train, y_train)

# 6. 评估
y_pred = pipeline.predict(X_test)
print('=== Classification Report ===')
print(classification_report(y_test, y_pred))
print('=== Confusion Matrix ===')
print(confusion_matrix(y_test, y_pred))

# 7. 交叉验证以验证鲁棒性
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
print(f'5-Fold CV Accuracy: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}')

# 8. 保存模型以供部署
joblib.dump(pipeline, 'student_exam_predictor.joblib')
print('Model saved to student_exam_predictor.joblib')
```
