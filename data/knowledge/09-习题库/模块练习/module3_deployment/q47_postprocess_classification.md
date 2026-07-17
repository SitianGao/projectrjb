# 数值稳定：减去最大值

> 来源模块: module3_deployment
> 原始文件: q47_postprocess_classification.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】分类/回归后处理方法实现
【模块】模块3 - 模型部署
【难度】3
【知识点】Softmax归一化、Top-K提取、类别映射、反归一化、
          模型融合（加权平均/Stacking/Voting）
【描述】
本题要求实现模型推理后的常见后处理方法，涵盖分类和回归两个场景。

分类后处理：
1. Softmax归一化：将logits转为概率分布
2. Top-K提取：获取概率最高的K个类别
3. 类别映射：将数字标签映射为可读类别名

回归后处理：
4. 反归一化：将归一化的预测值还原为原始尺度

模型融合：
5. 加权平均融合：多个模型的预测加权平均
6. Stacking融合：用元模型组合多个基模型的预测
7. Voting融合：多数投票（硬投票）和概率平均（软投票）

【输入输出】
- 输入：模拟的模型输出（logits、概率、预测值）
- 输出：打印各种后处理的结果

【要求】
1. 手动实现Softmax（数值稳定版本）
2. Top-K返回类别索引和对应概率
3. 类别映射支持自定义映射字典
4. 反归一化支持Min-Max和Z-Score两种方式
5. 加权平均融合支持任意数量的模型
6. Stacking使用sklearn的元模型（如LogisticRegression）
7. Voting实现硬投票和软投票
8. 每个函数需有清晰的文档字符串

【提示】
- Softmax数值稳定: exp(x - max(x)) / sum(exp(x - max(x)))
- Top-K可用np.argpartition高效实现
- Min-Max反归一化: x_original = x_normalized * (max - min) + min
- Z-Score反归一化: x_original = x_normalized * std + mean
=============================
"""

# ========== 参考答案 ==========

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict


# ==================== 1. Softmax归一化 ====================

def softmax(logits):
    """数值稳定的Softmax实现

    softmax(x_i) = exp(x_i - max(x)) / sum(exp(x_j - max(x)))

    Args:
        logits: numpy数组, shape (..., C) 或 (C,)

    Returns:
        numpy数组, 与输入同shape, 沿最后一维归一化
    """
    # 数值稳定：减去最大值
    max_logits = np.max(logits, axis=-1, keepdims=True)
    exp_logits = np.exp(logits - max_logits)
    return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)


def softmax_with_temperature(logits, temperature=1.0):
    """带温度参数的Softmax

    temperature > 1 使分布更平滑，< 1 使分布更尖锐

    Args:
        logits: numpy数组
        temperature: 温度参数

    Returns:
        numpy数组
    """
    scaled_logits = logits / temperature
    return softmax(scaled_logits)


# ==================== 2. Top-K提取 ====================

def top_k(probs, k=3, class_names=None):
    """提取概率最高的K个类别

    Args:
        probs: 概率数组, shape (C,) 或 (N, C)
        k: 返回前K个
        class_names: 可选的类别名称列表

    Returns:
        如果输入为一维:
            [(class_idx, prob), ...] 前 K 个
        如果输入为二维:
            [[(class_idx, prob), ...], ...] 每行的前 K 个
    """
    if probs.ndim == 1:
        # 单个样本
        top_indices = np.argsort(probs)[::-1][:k]
        results = []
        for idx in top_indices:
            name = class_names[idx] if class_names else idx
            results.append((name, float(probs[idx])))
        return results
    else:
        # 批量
        results = []
        for row in probs:
            results.append(top_k(row, k, class_names))
        return results


# ==================== 3. 类别映射 ====================

class ClassMapper:
    """类别映射器：数字标签 <-> 可读类别名"""

    def __init__(self, mapping=None):
        """
        Args:
            mapping: dict, {0: "cat", 1: "dog", 2: "bird"}
        """
        self.idx_to_name = mapping or {}
        self.name_to_idx = {v: k for k, v in self.idx_to_name.items()}

    def idx2name(self, idx):
        """数字标签 -> 类别名"""
        return self.idx_to_name.get(idx, f"class_{idx}")

    def name2idx(self, name):
        """类别名 -> 数字标签"""
        return self.name_to_idx.get(name, -1)

    def map_predictions(self, predictions):
        """批量映射预测标签"""
        return [self.idx2name(p) for p in predictions]


# ==================== 4. 反归一化 ====================

class Denormalizer:
    """反归一化器"""

    @staticmethod
    def min_max(x_normalized, feature_min, feature_max):
        """Min-Max反归一化

        x_original = x_normalized * (max - min) + min

        Args:
            x_normalized: 归一化后的值
            feature_min: 原始最小值
            feature_max: 原始最大值

        Returns:
            反归一化后的值
        """
        return x_normalized * (feature_max - feature_min) + feature_min

    @staticmethod
    def z_score(x_normalized, mean, std):
        """Z-Score反归一化

        x_original = x_normalized * std + mean

        Args:
            x_normalized: 归一化后的值
            mean: 原始均值
            std: 原始标准差

        Returns:
            反归一化后的值
        """
        return x_normalized * std + mean


# ==================== 5. 模型融合 ====================

def weighted_average_fusion(predictions_list, weights=None):
    """加权平均融合

    Args:
        predictions_list: list of numpy数组, 每个模型的预测概率 (N, C)
        weights: list, 每个模型的权重，默认等权

    Returns:
        numpy数组: 融合后的预测概率
    """
    n_models = len(predictions_list)
    if weights is None:
        weights = [1.0 / n_models] * n_models

    # 归一化权重
    weights = np.array(weights)
    weights = weights / weights.sum()

    result = np.zeros_like(predictions_list[0])
    for pred, w in zip(predictions_list, weights):
        result += w * pred

    return result


def hard_voting(predictions_list):
    """硬投票融合

    每个模型投一票，多数票决定最终类别。

    Args:
        predictions_list: list of numpy数组, 每个模型的类别预测 (N,)

    Returns:
        numpy数组: 投票结果 (N,)
    """
    predictions_array = np.array(predictions_list)  # (n_models, N)
    n_samples = predictions_array.shape[1]
    results = []

    for i in range(n_samples):
        votes = predictions_array[:, i]
        unique, counts = np.unique(votes, return_counts=True)
        winner = unique[np.argmax(counts)]
        results.append(winner)

    return np.array(results)


def soft_voting(probabilities_list):
    """软投票融合

    对多个模型的预测概率取平均，再取argmax。

    Args:
        probabilities_list: list of numpy数组, 每个模型的预测概率 (N, C)

    Returns:
        numpy数组: 融合后的类别预测 (N,)
    """
    avg_probs = np.mean(probabilities_list, axis=0)
    return np.argmax(avg_probs, axis=1)


def stacking_fusion(train_features_list, train_labels, test_features_list,
                    meta_model=None):
    """Stacking融合

    使用多个基模型的预测作为特征，训练一个元模型。

    Args:
        train_features_list: list, 每个基模型对训练集的预测概率 (N_train, C)
        train_labels: 训练集标签 (N_train,)
        test_features_list: list, 每个基模型对测试集的预测概率 (N_test, C)
        meta_model: 元模型，默认使用LogisticRegression

    Returns:
        numpy数组: 元模型对测试集的预测 (N_test,)
    """
    if meta_model is None:
        meta_model = LogisticRegression(max_iter=200)

    # 拼接基模型的预测作为新特征
    X_meta_train = np.concatenate(train_features_list, axis=1)
    X_meta_test = np.concatenate(test_features_list, axis=1)

    # 训练元模型
    meta_model.fit(X_meta_train, train_labels)

    # 预测
    predictions = meta_model.predict(X_meta_test)
    return predictions


# ==================== 验证与演示 ====================

def verify_softmax():
    """验证Softmax实现"""
    print("=" * 60)
    print("[1] Softmax归一化验证")
    print("=" * 60)

    logits = np.array([[2.0, 1.0, 0.1],
                       [0.5, 2.5, 0.3]])
    probs = softmax(logits)
    print(f"  Logits:\n{logits}")
    print(f"  Softmax概率:\n{probs}")
    print(f"  每行求和: {probs.sum(axis=1)} (应为1.0)")

    # 温度Softmax
    probs_high_t = softmax_with_temperature(logits, temperature=2.0)
    probs_low_t = softmax_with_temperature(logits, temperature=0.5)
    print(f"\n  温度=2.0 (更平滑):\n{probs_high_t}")
    print(f"  温度=0.5 (更尖锐):\n{probs_low_t}")

    # 与scipy对比
    from scipy.special import softmax as scipy_softmax
    scipy_probs = scipy_softmax(logits, axis=1)
    diff = np.max(np.abs(probs - scipy_probs))
    print(f"\n  与scipy.softmax最大误差: {diff:.2e}")
    print(f"  验证: {'通过' if diff < 1e-10 else '未通过'}")


def verify_top_k():
    """验证Top-K"""
    print("\n" + "=" * 60)
    print("[2] Top-K提取验证")
    print("=" * 60)

    probs = np.array([0.05, 0.15, 0.55, 0.20, 0.05])
    class_names = ["cat", "dog", "bird", "fish", "horse"]

    top3 = top_k(probs, k=3, class_names=class_names)
    print(f"  概率: {dict(zip(class_names, probs))}")
    print(f"  Top-3: {top3}")

    # 批量Top-K
    batch_probs = np.array([[0.1, 0.7, 0.2],
                            [0.5, 0.3, 0.2],
                            [0.1, 0.1, 0.8]])
    batch_top2 = top_k(batch_probs, k=2)
    print(f"\n  批量Top-2:")
    for i, t2 in enumerate(batch_top2):
        print(f"    样本{i}: {t2}")


def verify_class_mapping():
    """验证类别映射"""
    print("\n" + "=" * 60)
    print("[3] 类别映射验证")
    print("=" * 60)

    mapping = {0: "猫", 1: "狗", 2: "鸟", 3: "鱼"}
    mapper = ClassMapper(mapping)

    predictions = [0, 2, 1, 3, 0, 2]
    mapped = mapper.map_predictions(predictions)
    print(f"  数字标签: {predictions}")
    print(f"  映射结果: {mapped}")
    print(f"  反向查询 '狗' -> {mapper.name2idx('狗')}")


def verify_denormalization():
    """验证反归一化"""
    print("\n" + "=" * 60)
    print("[4] 反归一化验证")
    print("=" * 60)

    # Min-Max
    x_norm = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    x_orig = Denormalizer.min_max(x_norm, feature_min=10, feature_max=50)
    print(f"  Min-Max反归一化:")
    print(f"    归一化: {x_norm}")
    print(f"    原始值: {x_orig} (min=10, max=50)")

    # Z-Score
    x_znorm = np.array([-1.5, -0.5, 0.0, 0.5, 1.5])
    x_orig2 = Denormalizer.z_score(x_znorm, mean=100, std=15)
    print(f"\n  Z-Score反归一化:")
    print(f"    Z-Score: {x_znorm}")
    print(f"    原始值:  {x_orig2} (mean=100, std=15)")


def verify_fusion():
    """验证模型融合"""
    print("\n" + "=" * 60)
    print("[5] 模型融合验证")
    print("=" * 60)

    np.random.seed(42)
    n_samples = 100
    n_classes = 3

    # 模拟3个模型的预测概率
    probs1 = softmax(np.random.randn(n_samples, n_classes))
    probs2 = softmax(np.random.randn(n_samples, n_classes))
    probs3 = softmax(np.random.randn(n_samples, n_classes))

    # 加权平均融合
    fused_probs = weighted_average_fusion(
        [probs1, probs2, probs3], weights=[0.5, 0.3, 0.2]
    )
    fused_pred = np.argmax(fused_probs, axis=1)
    print(f"  加权平均融合 (权重=[0.5, 0.3, 0.2]):")
    print(f"    融合概率形状: {fused_probs.shape}")
    print(f"    前5个预测: {fused_pred[:5].tolist()}")

    # 硬投票
    pred1 = np.argmax(probs1, axis=1)
    pred2 = np.argmax(probs2, axis=1)
    pred3 = np.argmax(probs3, axis=1)
    hard_votes = hard_voting([pred1, pred2, pred3])
    print(f"\n  硬投票融合:")
    print(f"    模型1预测: {pred1[:5].tolist()}")
    print(f"    模型2预测: {pred2[:5].tolist()}")
    print(f"    模型3预测: {pred3[:5].tolist()}")
    print(f"    投票结果:  {hard_votes[:5].tolist()}")

    # 软投票
    soft_votes = soft_voting([probs1, probs2, probs3])
    print(f"\n  软投票融合:")
    print(f"    前5个预测: {soft_votes[:5].tolist()}")

    # Stacking
    y_train = np.random.randint(0, n_classes, n_samples)
    test_probs1 = softmax(np.random.randn(20, n_classes))
    test_probs2 = softmax(np.random.randn(20, n_classes))

    stacked_pred = stacking_fusion(
        [probs1, probs2], y_train,
        [test_probs1, test_probs2],
    )
    print(f"\n  Stacking融合:")
    print(f"    元模型预测: {stacked_pred[:5].tolist()}")


def solve():
    verify_softmax()
    verify_top_k()
    verify_class_mapping()
    verify_denormalization()
    verify_fusion()
    print("\n" + "=" * 60)
    print("分类/回归后处理验证完成！")
    print("=" * 60)


if __name__ == "__main__":
    solve()

```
