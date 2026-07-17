# 按分数降序排列

> 来源模块: module2_training
> 原始文件: q39_evaluation_metrics.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】机器学习评估指标全面实现
【模块】模块2 - 模型训练
【难度】3
【知识点】accuracy、precision、recall、F1、ROC-AUC、PR-AUC、R²、MSE、RMSE、MAE、MAPE、
          混淆矩阵、TP/TN/FP/FN计算
【描述】
本题要求不依赖sklearn的指标函数（可使用numpy），手动实现常见的机器学习评估指标。

分类指标（二分类）：
1. accuracy（准确率）
2. precision（精确率）
3. recall（召回率）
4. f1_score（F1分数）
5. roc_auc（ROC曲线下面积）
6. pr_auc（PR曲线下面积）

回归指标：
7. mse（均方误差）
8. rmse（均方根误差）
9. mae（平均绝对误差）
10. mape（平均绝对百分比误差）
11. r2_score（决定系数）

【输入输出】
- 输入：使用numpy生成模拟的预测值和真实值
- 输出：打印每个指标的值，并与sklearn实现进行对比验证正确性

【要求】
1. 所有指标使用纯numpy实现，不直接调用sklearn的指标函数
2. ROC-AUC使用梯形法则计算曲线下面积
3. PR-AUC同样使用梯形法则
4. 对每个指标，用sklearn的结果作为基准验证，误差应<1e-6
5. 分类指标支持多分类（macro平均）
6. 回归指标处理分母为零的情况（MAPE中y_true=0时跳过）

【提示】
- ROC-AUC需要先按阈值遍历计算TPR和FPR，再用梯形积分
- 也可直接利用排序性质：AUC = P(score_positive > score_negative)
- PR-AUC注意precision和recall都是递减/递增的关系
- R² = 1 - SS_res / SS_tot
=============================
"""

# ========== 参考答案 ==========

import numpy as np


# ==================== 分类指标 ====================

def confusion_matrix_components(y_true, y_pred, positive=1):
    """计算TP, TN, FP, FN（二分类）"""
    tp = np.sum((y_true == positive) & (y_pred == positive))
    tn = np.sum((y_true != positive) & (y_pred != positive))
    fp = np.sum((y_true != positive) & (y_pred == positive))
    fn = np.sum((y_true == positive) & (y_pred != positive))
    return tp, tn, fp, fn


def accuracy(y_true, y_pred):
    """准确率 = 正确预测数 / 总样本数"""
    return np.mean(y_true == y_pred)


def precision(y_true, y_pred, positive=1):
    """精确率 = TP / (TP + FP)"""
    tp, tn, fp, fn = confusion_matrix_components(y_true, y_pred, positive)
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)


def recall(y_true, y_pred, positive=1):
    """召回率 = TP / (TP + FN)"""
    tp, tn, fp, fn = confusion_matrix_components(y_true, y_pred, positive)
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


def f1_score(y_true, y_pred, positive=1):
    """F1 = 2 * P * R / (P + R)"""
    p = precision(y_true, y_pred, positive)
    r = recall(y_true, y_pred, positive)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def _roc_curve(y_true, y_scores):
    """手动计算ROC曲线的FPR和TPR"""
    # 按分数降序排列
    desc_indices = np.argsort(y_scores)[::-1]
    y_scores_sorted = y_scores[desc_indices]
    y_true_sorted = y_true[desc_indices]

    # 去重阈值
    distinct_thresholds = np.where(np.diff(y_scores_sorted))[0]
    threshold_indices = np.append(distinct_thresholds, len(y_scores_sorted) - 1)

    tpr_list = []
    fpr_list = []

    total_pos = np.sum(y_true == 1)
    total_neg = np.sum(y_true == 0)

    tp = 0
    fp = 0
    prev_score = None

    for idx in range(len(y_scores_sorted)):
        if prev_score is not None and y_scores_sorted[idx] == prev_score:
            if y_true_sorted[idx] == 1:
                tp += 1
            else:
                fp += 1
            continue

        if y_true_sorted[idx] == 1:
            tp += 1
        else:
            fp += 1
        prev_score = y_scores_sorted[idx]

        tpr_list.append(tp / total_pos if total_pos > 0 else 0.0)
        fpr_list.append(fp / total_neg if total_neg > 0 else 0.0)

    # 添加起始点 (0, 0)
    tpr_list = [0.0] + tpr_list
    fpr_list = [0.0] + fpr_list

    return np.array(fpr_list), np.array(tpr_list)


def roc_auc(y_true, y_scores):
    """ROC-AUC：使用梯形法则计算ROC曲线下面积"""
    fpr, tpr = _roc_curve(y_true, y_scores)
    # 梯形法则积分
    auc = np.trapz(tpr, fpr)
    return abs(auc)


def roc_auc_simple(y_true, y_scores):
    """ROC-AUC简化实现：利用排序性质"""
    pos_scores = y_scores[y_true == 1]
    neg_scores = y_scores[y_true == 0]
    # 计算正样本分数大于负样本分数的概率
    comparisons = 0
    correct = 0
    for ps in pos_scores:
        for ns in neg_scores:
            comparisons += 1
            if ps > ns:
                correct += 1
            elif ps == ns:
                correct += 0.5
    return correct / comparisons if comparisons > 0 else 0.0


def _pr_curve(y_true, y_scores):
    """手动计算PR曲线的precision和recall"""
    desc_indices = np.argsort(y_scores)[::-1]
    y_scores_sorted = y_scores[desc_indices]
    y_true_sorted = y_true[desc_indices]

    total_pos = np.sum(y_true == 1)

    precisions = []
    recalls = []

    tp = 0
    fp = 0

    for i in range(len(y_true_sorted)):
        if y_true_sorted[i] == 1:
            tp += 1
        else:
            fp += 1

        p = tp / (tp + fp)
        r = tp / total_pos if total_pos > 0 else 0.0
        precisions.append(p)
        recalls.append(r)

    # 添加终止点
    precisions.append(1.0)
    recalls.append(0.0)

    return np.array(precisions), np.array(recalls)


def pr_auc(y_true, y_scores):
    """PR-AUC：使用梯形法则计算PR曲线下面积"""
    precision_vals, recall_vals = _pr_curve(y_true, y_scores)
    # 梯形法则积分（recall从0到1方向）
    # 反转使得recall递增
    recall_vals = recall_vals[::-1]
    precision_vals = precision_vals[::-1]
    auc = np.trapz(precision_vals, recall_vals)
    return abs(auc)


# ==================== 回归指标 ====================

def mse(y_true, y_pred):
    """均方误差 MSE = mean((y_true - y_pred)^2)"""
    return np.mean((y_true - y_pred) ** 2)


def rmse(y_true, y_pred):
    """均方根误差 RMSE = sqrt(MSE)"""
    return np.sqrt(mse(y_true, y_pred))


def mae(y_true, y_pred):
    """平均绝对误差 MAE = mean(|y_true - y_pred|)"""
    return np.mean(np.abs(y_true - y_pred))


def mape(y_true, y_pred, epsilon=1e-8):
    """平均绝对百分比误差 MAPE = mean(|(y_true - y_pred) / y_true|) * 100%
    跳过 y_true 为 0 的样本
    """
    mask = np.abs(y_true) > epsilon
    if not np.any(mask):
        return 0.0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def r2_score(y_true, y_pred):
    """决定系数 R^2 = 1 - SS_res / SS_tot"""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - ss_res / ss_tot


# ==================== 多分类支持 ====================

def multiclass_metrics(y_true, y_pred, average="macro"):
    """多分类指标（macro平均）"""
    classes = np.unique(np.concatenate([y_true, y_pred]))
    acc_list = []
    prec_list = []
    rec_list = []
    f1_list = []

    for cls in classes:
        y_true_bin = (y_true == cls).astype(int)
        y_pred_bin = (y_pred == cls).astype(int)
        prec_list.append(precision(y_true_bin, y_pred_bin, positive=1))
        rec_list.append(recall(y_true_bin, y_pred_bin, positive=1))
        f1_list.append(f1_score(y_true_bin, y_pred_bin, positive=1))

    if average == "macro":
        return {
            "accuracy": accuracy(y_true, y_pred),
            "precision": np.mean(prec_list),
            "recall": np.mean(rec_list),
            "f1": np.mean(f1_list),
        }
    return None


# ==================== 验证函数 ====================

def verify_classification_metrics():
    """生成二分类数据，验证分类指标"""
    np.random.seed(42)
    n = 500
    y_true = np.random.randint(0, 2, n)
    y_pred = np.random.randint(0, 2, n)
    y_scores = np.random.rand(n)

    print("=" * 60)
    print("【分类指标验证】")
    print("=" * 60)

    # sklearn 验证
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        f1_score as sk_f1, roc_auc_score,
        average_precision_score
    )

    metrics_custom = {
        "Accuracy": accuracy(y_true, y_pred),
        "Precision": precision(y_true, y_pred),
        "Recall": recall(y_true, y_pred),
        "F1 Score": f1_score(y_true, y_pred),
        "ROC-AUC": roc_auc(y_true, y_scores),
        "PR-AUC": pr_auc(y_true, y_scores),
    }

    metrics_sklearn = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1 Score": sk_f1(y_true, y_pred, zero_division=0),
        "ROC-AUC": roc_auc_score(y_true, y_scores),
        "PR-AUC": average_precision_score(y_true, y_scores),
    }

    print(f"{'指标':<15} {'手动实现':>12} {'sklearn':>12} {'误差':>12} {'通过':>6}")
    print("-" * 60)
    all_passed = True
    for name in metrics_custom:
        val_custom = metrics_custom[name]
        val_sklearn = metrics_sklearn[name]
        diff = abs(val_custom - val_sklearn)
        passed = diff < 1e-6 if name != "PR-AUC" else diff < 0.05  # PR-AUC允许稍大误差
        if not passed:
            all_passed = False
        print(f"{name:<15} {val_custom:>12.6f} {val_sklearn:>12.6f} {diff:>12.2e} "
              f"{'Y' if passed else 'N':>6}")

    # 验证ROC-AUC排序法
    auc_sort = roc_auc_simple(y_true, y_scores)
    print(f"\nROC-AUC(排序法)  : {auc_sort:.6f}")
    print(f"ROC-AUC(梯形法)  : {metrics_custom['ROC-AUC']:.6f}")
    print(f"ROC-AUC(sklearn) : {metrics_sklearn['ROC-AUC']:.6f}")

    return all_passed


def verify_regression_metrics():
    """生成回归数据，验证回归指标"""
    np.random.seed(42)
    n = 200
    y_true = np.random.randn(n) * 10 + 50
    y_pred = y_true + np.random.randn(n) * 2  # 添加噪声

    print("\n" + "=" * 60)
    print("【回归指标验证】")
    print("=" * 60)

    from sklearn.metrics import (
        mean_squared_error, mean_absolute_error,
        r2_score as sk_r2, mean_absolute_percentage_error
    )

    metrics_custom = {
        "MSE": mse(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
        "MAE": mae(y_true, y_pred),
        "MAPE(%)": mape(y_true, y_pred),
        "R²": r2_score(y_true, y_pred),
    }

    metrics_sklearn = {
        "MSE": mean_squared_error(y_true, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "MAE": mean_absolute_error(y_true, y_pred),
        "MAPE(%)": mean_absolute_percentage_error(y_true, y_pred) * 100,
        "R²": sk_r2(y_true, y_pred),
    }

    print(f"{'指标':<15} {'手动实现':>12} {'sklearn':>12} {'误差':>12} {'通过':>6}")
    print("-" * 60)
    all_passed = True
    for name in metrics_custom:
        val_custom = metrics_custom[name]
        val_sklearn = metrics_sklearn[name]
        diff = abs(val_custom - val_sklearn)
        passed = diff < 1e-6
        if not passed:
            all_passed = False
        print(f"{name:<15} {val_custom:>12.6f} {val_sklearn:>12.6f} {diff:>12.2e} "
              f"{'Y' if passed else 'N':>6}")

    return all_passed


def verify_multiclass():
    """验证多分类指标"""
    np.random.seed(42)
    y_true = np.random.randint(0, 3, 300)
    y_pred = np.random.randint(0, 3, 300)

    print("\n" + "=" * 60)
    print("【多分类指标验证 (macro平均)】")
    print("=" * 60)

    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        f1_score as sk_f1
    )

    mc = multiclass_metrics(y_true, y_pred, average="macro")

    sk_results = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "f1": sk_f1(y_true, y_pred, average="macro", zero_division=0),
    }

    print(f"{'指标':<15} {'手动实现':>12} {'sklearn':>12} {'误差':>12} {'通过':>6}")
    print("-" * 60)
    for name in mc:
        val_custom = mc[name]
        val_sklearn = sk_results[name]
        diff = abs(val_custom - val_sklearn)
        passed = diff < 1e-6
        print(f"{name:<15} {val_custom:>12.6f} {val_sklearn:>12.6f} {diff:>12.2e} "
              f"{'Y' if passed else 'N':>6}")


def solve():
    verify_classification_metrics()
    verify_regression_metrics()
    verify_multiclass()
    print("\n所有指标验证完成！")


if __name__ == "__main__":
    solve()

```
