# 创建临时目录保存模型

> 来源模块: module2_training
> 原始文件: q36_model_persistence.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】模型持久化与特征选择
【模块】模型训练与评估
【难度】4
【知识点】模型保存与加载、joblib、pickle、SelectKBest、RFE、特征重要性、sklearn
【描述】
学习如何使用joblib和pickle保存/加载训练好的模型，以及使用sklearn的SelectKBest
和RFE（递归特征消除）进行特征选择。

【要求】
1. 使用joblib保存和加载sklearn模型
2. 使用pickle保存和加载模型
3. 使用SelectKBest进行基于统计检验的特征选择
4. 使用RFE进行递归特征消除
5. 对比不同特征选择方法的效果
6. 验证加载后的模型预测结果与原始模型一致

【提示】
- joblib对于大型numpy数组更高效
- SelectKBest使用f_classif/chi2等统计检验
- RFE递归地移除最不重要的特征
- 保存模型时同时保存预处理参数
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import pandas as pd
import os
import pickle
import joblib
import tempfile
from sklearn.datasets import load_breast_cancer, make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import (
    SelectKBest,
    f_classif,
    mutual_info_classif,
    RFE,
    SelectFromModel,
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings("ignore")


# ======================== 模型持久化 ========================

def demonstrate_model_persistence(X_train, X_test, y_train, y_test):
    """演示模型保存和加载"""
    print("=" * 60)
    print("一、模型持久化演示")
    print("=" * 60)

    # ---- 训练模型 ----
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
    model.fit(X_train_scaled, y_train)

    # 原始预测
    original_pred = model.predict(X_test_scaled)
    original_acc = accuracy_score(y_test, original_pred)
    print(f"\n原始模型准确率: {original_acc:.4f}")

    # 创建临时目录保存模型
    save_dir = tempfile.mkdtemp()

    # ---- 1. 使用joblib保存 ----
    print("\n--- 使用 joblib 保存模型 ---")
    model_path_jl = os.path.join(save_dir, "model.joblib")
    scaler_path_jl = os.path.join(save_dir, "scaler.joblib")

    joblib.dump(model, model_path_jl)
    joblib.dump(scaler, scaler_path_jl)

    print(f"模型保存路径: {model_path_jl}")
    print(f"模型文件大小: {os.path.getsize(model_path_jl) / 1024:.1f} KB")

    # 加载模型
    loaded_model_jl = joblib.load(model_path_jl)
    loaded_scaler_jl = joblib.load(scaler_path_jl)

    # 验证加载后的模型
    X_test_scaled_jl = loaded_scaler_jl.transform(X_test)
    loaded_pred_jl = loaded_model_jl.predict(X_test_scaled_jl)
    loaded_acc_jl = accuracy_score(y_test, loaded_pred_jl)

    print(f"joblib加载模型准确率: {loaded_acc_jl:.4f}")
    print(f"预测结果一致性: {np.array_equal(original_pred, loaded_pred_jl)}")

    # ---- 2. 使用pickle保存 ----
    print("\n--- 使用 pickle 保存模型 ---")
    model_path_pk = os.path.join(save_dir, "model.pkl")
    scaler_path_pk = os.path.join(save_dir, "scaler.pkl")

    with open(model_path_pk, "wb") as f:
        pickle.dump(model, f)
    with open(scaler_path_pk, "wb") as f:
        pickle.dump(scaler, f)

    print(f"模型保存路径: {model_path_pk}")
    print(f"模型文件大小: {os.path.getsize(model_path_pk) / 1024:.1f} KB")

    # 加载模型
    with open(model_path_pk, "rb") as f:
        loaded_model_pk = pickle.load(f)
    with open(scaler_path_pk, "rb") as f:
        loaded_scaler_pk = pickle.load(f)

    X_test_scaled_pk = loaded_scaler_pk.transform(X_test)
    loaded_pred_pk = loaded_model_pk.predict(X_test_scaled_pk)
    loaded_acc_pk = accuracy_score(y_test, loaded_pred_pk)

    print(f"pickle加载模型准确率: {loaded_acc_pk:.4f}")
    print(f"预测结果一致性: {np.array_equal(original_pred, loaded_pred_pk)}")

    # ---- 3. 保存完整Pipeline ----
    print("\n--- 保存完整Pipeline ---")
    from sklearn.pipeline import Pipeline

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)),
    ])
    pipe.fit(X_train, y_train)

    pipe_path = os.path.join(save_dir, "pipeline.joblib")
    joblib.dump(pipe, pipe_path)

    loaded_pipe = joblib.load(pipe_path)
    pipe_pred = loaded_pipe.predict(X_test)
    pipe_acc = accuracy_score(y_test, pipe_pred)

    print(f"Pipeline保存路径: {pipe_path}")
    print(f"Pipeline加载后准确率: {pipe_acc:.4f}")

    # 清理临时文件
    for f_path in [model_path_jl, scaler_path_jl, model_path_pk, scaler_path_pk, pipe_path]:
        if os.path.exists(f_path):
            os.remove(f_path)
    os.rmdir(save_dir)

    return model, scaler


# ======================== 特征选择 ========================

def demonstrate_feature_selection(X_train, X_test, y_train, y_test, feature_names):
    """演示特征选择方法"""
    print("\n" + "=" * 60)
    print("二、特征选择演示")
    print("=" * 60)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    n_features = X_train.shape[1]
    results = {}

    # ---- 1. SelectKBest (f_classif) ----
    print("\n--- 1. SelectKBest (f_classif) ---")
    for k in [5, 10, 15, 20]:
        selector = SelectKBest(f_classif, k=k)
        X_train_sel = selector.fit_transform(X_train_scaled, y_train)
        X_test_sel = selector.transform(X_test_scaled)

        clf = LogisticRegression(max_iter=1000, random_state=42)
        clf.fit(X_train_sel, y_train)
        acc = accuracy_score(y_test, clf.predict(X_test_sel))

        selected_idx = selector.get_support(indices=True)
        print(f"  k={k:2d}: 准确率={acc:.4f}, 选择的特征: {list(feature_names[selected_idx][:5])}...")
        results[f"SelectKBest_k={k}"] = acc

    # ---- 2. SelectKBest (mutual_info) ----
    print("\n--- 2. SelectKBest (mutual_info_classif) ---")
    for k in [5, 10, 15]:
        selector = SelectKBest(mutual_info_classif, k=k)
        X_train_sel = selector.fit_transform(X_train_scaled, y_train)
        X_test_sel = selector.transform(X_test_scaled)

        clf = LogisticRegression(max_iter=1000, random_state=42)
        clf.fit(X_train_sel, y_train)
        acc = accuracy_score(y_test, clf.predict(X_test_sel))

        selected_idx = selector.get_support(indices=True)
        print(f"  k={k:2d}: 准确率={acc:.4f}")
        results[f"MutualInfo_k={k}"] = acc

    # ---- 3. RFE (递归特征消除) ----
    print("\n--- 3. RFE (递归特征消除) ---")
    estimator = LogisticRegression(max_iter=1000, random_state=42)
    for n_features_to_select in [5, 10, 15]:
        rfe = RFE(
            estimator=estimator,
            n_features_to_select=n_features_to_select,
            step=1,
        )
        X_train_rfe = rfe.fit_transform(X_train_scaled, y_train)
        X_test_rfe = rfe.transform(X_test_scaled)

        clf = LogisticRegression(max_iter=1000, random_state=42)
        clf.fit(X_train_rfe, y_train)
        acc = accuracy_score(y_test, clf.predict(X_test_rfe))

        selected_idx = rfe.get_support(indices=True)
        ranking = rfe.ranking_
        print(f"  n={n_features_to_select:2d}: 准确率={acc:.4f}")
        print(f"         选择的特征索引: {list(selected_idx)}")
        results[f"RFE_n={n_features_to_select}"] = acc

    # ---- 4. 基于树模型的特征选择 ----
    print("\n--- 4. 基于树模型的特征选择 (SelectFromModel) ---")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train_scaled, y_train)

    # 特征重要性排序
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    print("  特征重要性排名 (Top 10):")
    for rank, idx in enumerate(indices[:10]):
        print(f"    {rank + 1:2d}. {feature_names[idx]:<30s} 重要性: {importances[idx]:.4f}")

    # SelectFromModel
    for threshold in ["mean", "median", "1.5*mean"]:
        sfm = SelectFromModel(rf, threshold=threshold)
        X_train_sfm = sfm.fit_transform(X_train_scaled, y_train)
        X_test_sfm = sfm.transform(X_test_scaled)

        n_selected = X_train_sfm.shape[1]
        clf = LogisticRegression(max_iter=1000, random_state=42)
        clf.fit(X_train_sfm, y_train)
        acc = accuracy_score(y_test, clf.predict(X_test_sfm))

        print(f"  threshold={threshold:<10s}: 选择了{n_selected}个特征, 准确率={acc:.4f}")
        results[f"TreeBased_{threshold}"] = acc

    # ---- 5. 使用全部特征作为基线 ----
    print("\n--- 5. 基线 (全部特征) ---")
    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train_scaled, y_train)
    baseline_acc = accuracy_score(y_test, clf.predict(X_test_scaled))
    print(f"  全部{n_features}个特征: 准确率={baseline_acc:.4f}")
    results["Baseline_All"] = baseline_acc

    return results


def summarize_results(results):
    """汇总特征选择结果"""
    print("\n" + "=" * 60)
    print("三、特征选择结果汇总")
    print("=" * 60)

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    print(f"\n{'方法':<30s} {'准确率':<10s}")
    print("-" * 40)
    for name, acc in sorted_results:
        print(f"{name:<30s} {acc:.4f}")

    best_method = sorted_results[0]
    print(f"\n最佳方法: {best_method[0]}, 准确率: {best_method[1]:.4f}")


# ======================== 主函数 ========================

def solve():
    """模型持久化与特征选择完整演示"""
    print("=" * 60)
    print("模型持久化与特征选择")
    print("=" * 60)

    # ---- 加载数据 ----
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = data.target

    print(f"\n数据集: 乳腺癌数据集")
    print(f"样本数: {X.shape[0]}, 特征数: {X.shape[1]}")
    print(f"类别分布: {dict(zip(*np.unique(y, return_counts=True)))}")

    # ---- 划分数据 ----
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"训练集: {X_train.shape[0]}, 测试集: {X_test.shape[0]}")

    # ---- 模型持久化 ----
    model, scaler = demonstrate_model_persistence(X_train, X_test, y_train, y_test)

    # ---- 特征选择 ----
    results = demonstrate_feature_selection(
        X_train, X_test, y_train, y_test,
        feature_names=np.array(data.feature_names),
    )

    # ---- 结果汇总 ----
    summarize_results(results)

    print("\n模型持久化与特征选择演示完成。")


if __name__ == "__main__":
    solve()

```
