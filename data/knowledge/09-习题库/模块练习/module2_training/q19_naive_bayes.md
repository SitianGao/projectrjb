# 计算先验概率

> 来源模块: module2_training
> 原始文件: q19_naive_bayes.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】朴素贝叶斯文本分类：手动实现与sklearn对比
【模块】模型训练与评估
【难度】5
【知识点】朴素贝叶斯、多项式朴素贝叶斯、文本分类、词袋模型、拉普拉斯平滑
【描述】
朴素贝叶斯是一种基于贝叶斯定理的概率分类器，广泛用于文本分类。
本题要求手动实现多项式朴素贝叶斯(Multinomial Naive Bayes)分类器，
并与sklearn的MultinomialNB进行对比。

数据集说明：
- 使用sklearn.datasets.fetch_20newsgroups加载新闻分类数据
- 选择4个类别：sci.space, rec.sport.baseball, comp.graphics, talk.politics.guns
- 使用词袋模型(CountVectorizer)进行文本向量化
- 比较手动实现与sklearn的分类精度

【要求】
1. 手动实现MultinomialNB类，包含：
   - fit: 计算先验概率和条件概率（带拉普拉斯平滑）
   - predict: 使用对数概率进行预测
   - predict_proba: 返回概率估计
2. 使用sklearn的MultinomialNB作为基准
3. 在测试集上对比分类精度和F1分数
4. 打印分类报告
5. 展示拉普拉斯平滑参数alpha对精度的影响

【提示】
- 先验概率: P(c) = count(c) / N
- 条件概率(拉普拉斯平滑): P(w|c) = (count(w,c) + alpha) / (count_all_words_in_c + alpha * |V|)
- 使用对数概率避免数值下溢: log P(c|d) = log P(c) + sum(log P(w|c))
- alpha=1.0为标准拉普拉斯平滑
=============================
"""

# ========== 参考答案 ==========

import numpy as np
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB as SklearnMNB
from sklearn.metrics import accuracy_score, f1_score, classification_report


class MultinomialNBManual:
    """手动实现的多项式朴素贝叶斯"""

    def __init__(self, alpha=1.0):
        self.alpha = alpha  # 拉普拉斯平滑参数
        self.class_log_prior_ = None
        self.feature_log_prob_ = None
        self.classes_ = None

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_features = X.shape[1]
        n_samples = X.shape[0]

        # 计算先验概率
        self.class_log_prior_ = np.zeros(n_classes)
        self.feature_log_prob_ = np.zeros((n_classes, n_features))

        for i, c in enumerate(self.classes_):
            X_c = X[y == c]
            # log P(c) = log(样本数/总样本数)
            self.class_log_prior_[i] = np.log(X_c.shape[0] / n_samples)
            # 每个特征在该类中的总出现次数
            feature_count = X_c.sum(axis=0)
            # 防止matrix返回，确保是1d array
            if hasattr(feature_count, "A1"):
                feature_count = feature_count.A1
            feature_count = np.asarray(feature_count).ravel()
            # 拉普拉斯平滑后的条件概率
            smoothed = feature_count + self.alpha
            total = smoothed.sum()
            self.feature_log_prob_[i] = np.log(smoothed / total)

        return self

    def _predict_log_proba(self, X):
        """计算对数概率"""
        # log P(c|d) = log P(c) + sum(x_i * log P(w_i|c))
        log_proba = np.dot(X, self.feature_log_prob_.T) + self.class_log_prior_
        # Log-sum-exp 归一化
        log_sum = np.array([self._log_sum_exp(row) for row in log_proba]).reshape(-1, 1)
        return log_proba - log_sum

    @staticmethod
    def _log_sum_exp(arr):
        """数值稳定的log-sum-exp"""
        max_val = np.max(arr)
        return max_val + np.log(np.sum(np.exp(arr - max_val)))

    def predict_proba(self, X):
        log_proba = self._predict_log_proba(X)
        return np.exp(log_proba)

    def predict(self, X):
        log_proba = np.dot(X, self.feature_log_prob_.T) + self.class_log_prior_
        return self.classes_[np.argmax(log_proba, axis=1)]


def solve():
    # ---- 1. 加载数据 ----
    categories = [
        "sci.space",
        "rec.sport.baseball",
        "comp.graphics",
        "talk.politics.guns"
    ]
    print("加载20 Newsgroups数据集...")
    data = fetch_20newsgroups(
        subset="all", categories=categories,
        shuffle=True, random_state=42,
        remove=("headers", "footers", "quotes")
    )
    print(f"总样本数: {len(data.data)}, 类别数: {len(categories)}")

    # ---- 2. 文本向量化 ----
    vectorizer = CountVectorizer(max_features=5000, stop_words="english")
    X = vectorizer.fit_transform(data.data)
    y = data.target
    feature_names = vectorizer.get_feature_names_out()
    print(f"特征维度: {X.shape}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # ---- 3. 手动实现 ----
    print("\n" + "=" * 60)
    print("手动实现 Multinomial Naive Bayes")
    print("=" * 60)
    manual_nb = MultinomialNBManual(alpha=1.0)
    manual_nb.fit(X_train, y_train)
    y_pred_manual = manual_nb.predict(X_test)
    acc_manual = accuracy_score(y_test, y_pred_manual)
    f1_manual = f1_score(y_test, y_pred_manual, average="weighted")
    print(f"准确率: {acc_manual:.4f}")
    print(f"F1分数: {f1_manual:.4f}")

    # ---- 4. sklearn实现 ----
    print("\n" + "=" * 60)
    print("sklearn MultinomialNB")
    print("=" * 60)
    sk_nb = SklearnMNB(alpha=1.0)
    sk_nb.fit(X_train, y_train)
    y_pred_sk = sk_nb.predict(X_test)
    acc_sk = accuracy_score(y_test, y_pred_sk)
    f1_sk = f1_score(y_test, y_pred_sk, average="weighted")
    print(f"准确率: {acc_sk:.4f}")
    print(f"F1分数: {f1_sk:.4f}")

    # ---- 5. 分类报告 ----
    print("\n" + "=" * 60)
    print("手动实现 - 分类报告")
    print("=" * 60)
    print(classification_report(y_test, y_pred_manual, target_names=categories))

    # ---- 6. 拉普拉斯平滑参数影响 ----
    print("=" * 60)
    print("alpha参数对精度的影响")
    print("=" * 60)
    alphas = [0.01, 0.1, 0.5, 1.0, 2.0, 5.0]
    print(f"{'alpha':<10} {'手动实现精度':>12} {'sklearn精度':>12}")
    print("-" * 36)
    for a in alphas:
        m_nb = MultinomialNBManual(alpha=a)
        m_nb.fit(X_train, y_train)
        m_acc = accuracy_score(y_test, m_nb.predict(X_test))

        s_nb = SklearnMNB(alpha=a)
        s_nb.fit(X_train, y_train)
        s_acc = accuracy_score(y_test, s_nb.predict(X_test))

        print(f"{a:<10.2f} {m_acc:>12.4f} {s_acc:>12.4f}")

    # ---- 7. 预测对比 ----
    print("\n" + "=" * 60)
    print("预测结果一致性检查")
    print("=" * 60)
    agree = np.sum(y_pred_manual == y_pred_sk)
    total = len(y_pred_manual)
    print(f"预测一致的样本: {agree}/{total} ({agree/total*100:.1f}%)")


if __name__ == "__main__":
    solve()

```
