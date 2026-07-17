# 网格搜索参数

> 来源模块: module2_training
> 原始文件: q35_pipeline_gridsearch.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】sklearn Pipeline与GridSearchCV
【模块】模型训练与评估
【难度】4
【知识点】Pipeline、GridSearchCV、RandomizedSearchCV、超参数调优、交叉验证、预处理
【描述】
使用scikit-learn构建完整的机器学习Pipeline，包含预处理步骤和模型，使用
GridSearchCV和RandomizedSearchCV进行超参数调优，并进行交叉验证评估。

【要求】
1. 构建Pipeline，包含标准化、特征选择/降维和分类器
2. 使用GridSearchCV进行网格搜索调参
3. 使用RandomizedSearchCV进行随机搜索调参
4. 输出最佳参数、最佳分数和完整评估报告
5. 比较不同Pipeline配置的性能
6. 使用sklearn内置数据集（如乳腺癌数据集）

【提示】
- Pipeline步骤: ('scaler', StandardScaler) -> ('clf', SVC)
- GridSearchCV的param_grid使用双下划线访问步骤参数
- RandomizedSearchCV使用scipy分布进行采样
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import (
    train_test_split,
    GridSearchCV,
    RandomizedSearchCV,
    cross_val_score,
    StratifiedKFold,
)
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    confusion_matrix,
)
from scipy.stats import uniform, randint
import warnings
warnings.filterwarnings("ignore")


# ======================== 数据加载 ========================

def load_data():
    """加载乳腺癌数据集"""
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = data.target
    return X, y


# ======================== Pipeline 1: 标准化 + 逻辑回归 ========================

def pipeline_logistic(X_train, X_test, y_train, y_test):
    """Pipeline: 标准化 + 逻辑回归 + GridSearchCV"""
    print("\n" + "=" * 60)
    print("Pipeline 1: StandardScaler + LogisticRegression")
    print("=" * 60)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])

    # 网格搜索参数
    param_grid = {
        "scaler": [StandardScaler(), MinMaxScaler()],
        "clf__C": [0.01, 0.1, 1, 10, 100],
        "clf__penalty": ["l1", "l2"],
        "clf__solver": ["liblinear"],
    }

    grid_search = GridSearchCV(
        pipe,
        param_grid,
        cv=5,
        scoring="accuracy",
        n_jobs=-1,
        verbose=0,
        return_train_score=True,
    )

    grid_search.fit(X_train, y_train)

    print(f"最佳参数: {grid_search.best_params_}")
    print(f"最佳CV分数: {grid_search.best_score_:.4f}")

    y_pred = grid_search.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    print(f"测试集准确率: {test_acc:.4f}")

    return grid_search, test_acc


# ======================== Pipeline 2: 标准化 + PCA + SVM ========================

def pipeline_svm(X_train, X_test, y_train, y_test):
    """Pipeline: 标准化 + PCA + SVM + GridSearchCV"""
    print("\n" + "=" * 60)
    print("Pipeline 2: StandardScaler + PCA + SVC")
    print("=" * 60)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("pca", PCA()),
        ("clf", SVC(random_state=42)),
    ])

    param_grid = {
        "pca__n_components": [5, 10, 15, 20],
        "clf__C": [0.1, 1, 10],
        "clf__kernel": ["rbf", "linear"],
        "clf__gamma": ["scale", "auto"],
    }

    grid_search = GridSearchCV(
        pipe,
        param_grid,
        cv=5,
        scoring="accuracy",
        n_jobs=-1,
        verbose=0,
    )

    grid_search.fit(X_train, y_train)

    print(f"最佳参数: {grid_search.best_params_}")
    print(f"最佳CV分数: {grid_search.best_score_:.4f}")

    y_pred = grid_search.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    print(f"测试集准确率: {test_acc:.4f}")

    # PCA解释方差
    best_pca = grid_search.best_estimator_.named_steps["pca"]
    print(f"PCA保留方差比例: {sum(best_pca.explained_variance_ratio_):.4f}")

    return grid_search, test_acc


# ======================== Pipeline 3: 标准化 + SelectKBest + 随机森林 ========================

def pipeline_random_forest(X_train, X_test, y_train, y_test):
    """Pipeline: 标准化 + SelectKBest + RandomForest + RandomizedSearchCV"""
    print("\n" + "=" * 60)
    print("Pipeline 3: StandardScaler + SelectKBest + RandomForest")
    print("=" * 60)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("select", SelectKBest(f_classif)),
        ("clf", RandomForestClassifier(random_state=42)),
    ])

    # 随机搜索参数分布
    param_dist = {
        "select__k": randint(5, 30),
        "clf__n_estimators": randint(50, 200),
        "clf__max_depth": randint(3, 20),
        "clf__min_samples_split": randint(2, 10),
        "clf__min_samples_leaf": randint(1, 5),
    }

    random_search = RandomizedSearchCV(
        pipe,
        param_distributions=param_dist,
        n_iter=50,
        cv=5,
        scoring="accuracy",
        n_jobs=-1,
        random_state=42,
        verbose=0,
    )

    random_search.fit(X_train, y_train)

    print(f"最佳参数: {random_search.best_params_}")
    print(f"最佳CV分数: {random_search.best_score_:.4f}")

    y_pred = random_search.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    print(f"测试集准确率: {test_acc:.4f}")

    # 特征重要性
    best_select = random_search.best_estimator_.named_steps["select"]
    selected_features = best_select.get_support(indices=True)
    print(f"选择的特征数量: {len(selected_features)}")
    print(f"选择的特征索引: {selected_features[:10]}...")

    return random_search, test_acc


# ======================== 综合对比 ========================

def compare_pipelines(results, X, y):
    """综合对比所有Pipeline"""
    print("\n" + "=" * 60)
    print("Pipeline 对比总结")
    print("=" * 60)

    print(f"\n{'Pipeline':<40} {'CV分数':<12} {'测试准确率':<12}")
    print("-" * 64)
    for name, cv_score, test_acc in results:
        print(f"{name:<40} {cv_score:<12.4f} {test_acc:<12.4f}")

    # 交叉验证对比
    print("\n5折交叉验证对比:")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)


# ======================== 主函数 ========================

def solve():
    """Pipeline与超参数调优完整演示"""
    print("=" * 60)
    print("sklearn Pipeline与GridSearchCV演示")
    print("=" * 60)

    # ---- 加载数据 ----
    X, y = load_data()
    print(f"\n数据集: 乳腺癌数据集 (Wisconsin)")
    print(f"样本数: {X.shape[0]}, 特征数: {X.shape[1]}")
    print(f"类别分布: {dict(zip(*np.unique(y, return_counts=True)))}")
    print(f"特征名称（前5个）: {list(X.columns[:5])}")

    # ---- 划分数据 ----
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n训练集: {X_train.shape[0]}, 测试集: {X_test.shape[0]}")

    # ---- 运行三个Pipeline ----
    results = []

    # Pipeline 1
    gs_lr, acc_lr = pipeline_logistic(X_train, X_test, y_train, y_test)
    results.append(("StandardScaler + LogisticRegression", gs_lr.best_score_, acc_lr))

    # Pipeline 2
    gs_svm, acc_svm = pipeline_svm(X_train, X_test, y_train, y_test)
    results.append(("StandardScaler + PCA + SVC", gs_svm.best_score_, acc_svm))

    # Pipeline 3
    rs_rf, acc_rf = pipeline_random_forest(X_train, X_test, y_train, y_test)
    results.append(("Scaler + SelectKBest + RandomForest", rs_rf.best_score_, acc_rf))

    # ---- 综合对比 ----
    compare_pipelines(results, X, y)

    # ---- 最佳模型的详细评估 ----
    print("\n" + "=" * 60)
    print("最佳模型详细评估报告")
    print("=" * 60)

    best_idx = np.argmax([r[2] for r in results])
    best_name = results[best_idx][0]
    print(f"最佳Pipeline: {best_name}")

    if best_idx == 0:
        best_model = gs_lr
    elif best_idx == 1:
        best_model = gs_svm
    else:
        best_model = rs_rf

    y_pred = best_model.predict(X_test)
    print("\n分类报告:")
    print(classification_report(y_test, y_pred, target_names=["恶性", "良性"]))

    print("混淆矩阵:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  真阴性(TN): {cm[0, 0]}, 假阳性(FP): {cm[0, 1]}")
    print(f"  假阴性(FN): {cm[1, 0]}, 真阳性(TP): {cm[1, 1]}")

    # ---- 交叉验证稳定性 ----
    print("\n" + "=" * 60)
    print("交叉验证稳定性分析")
    print("=" * 60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(best_model.best_estimator_, X, y, cv=cv, scoring="accuracy")
    print(f"5折CV准确率: {cv_scores}")
    print(f"平均: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

    print("\nPipeline与超参数调优演示完成。")


if __name__ == "__main__":
    solve()

```
