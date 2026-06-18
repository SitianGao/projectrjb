# sklearn使用的平滑IDF公式

> 来源模块: module1_preprocessing
> 原始文件: q11_tfidf_feature.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】TF-IDF特征提取
【模块】数据预处理
【难度】3
【知识点】TF-IDF原理、词频计算、逆文档频率、文本特征提取、sklearn TfidfVectorizer
【描述】
TF-IDF（Term Frequency-Inverse Document Frequency）是信息检索和文本挖掘中
常用的特征提取方法，它衡量一个词对文档的重要程度。

TF（词频）= 词在文档中出现的次数 / 文档总词数
IDF（逆文档频率）= log(文档总数 / 包含该词的文档数)
TF-IDF = TF * IDF

【要求】
1. 给定一组中文文本（已分词），手动实现TF计算
2. 手动实现IDF计算
3. 手动实现TF-IDF计算
4. 与sklearn的TfidfVectorizer结果对比
5. 分析TF-IDF矩阵的稀疏性

【提示】
- sklearn的TfidfVectorizer默认使用L2归一化
- sklearn的IDF计算使用 log((1+n)/(1+df)) + 1（平滑处理）
- 注意手动实现时是否需要归一化，以便与sklearn对比
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import math
from sklearn.feature_extraction.text import TfidfVectorizer


def tokenize(text):
    """简单分词：按空格分割。"""
    return text.split()


def build_vocab(documents):
    """
    构建词汇表。

    参数:
        documents: 文档列表（已分词，空格分隔）

    返回:
        vocab: 词到索引的映射
        vocab_list: 索引到词的映射
    """
    word_set = set()
    for doc in documents:
        word_set.update(tokenize(doc))

    vocab_list = sorted(word_set)
    vocab = {word: idx for idx, word in enumerate(vocab_list)}
    return vocab, vocab_list


def compute_tf(documents, vocab):
    """
    计算TF（词频）矩阵。
    TF(t, d) = 词t在文档d中出现的次数 / 文档d的总词数

    参数:
        documents: 文档列表
        vocab: 词汇表映射

    返回:
        tf_matrix: numpy数组，形状(文档数, 词汇数)
    """
    n_docs = len(documents)
    n_words = len(vocab)
    tf_matrix = np.zeros((n_docs, n_words))

    for i, doc in enumerate(documents):
        words = tokenize(doc)
        n_total = len(words)
        for word in words:
            if word in vocab:
                tf_matrix[i, vocab[word]] += 1
        if n_total > 0:
            tf_matrix[i] /= n_total

    return tf_matrix


def compute_idf(documents, vocab):
    """
    计算IDF（逆文档频率）向量。
    IDF(t) = log((1 + N) / (1 + df(t))) + 1  （sklearn平滑版本）

    参数:
        documents: 文档列表
        vocab: 词汇表映射

    返回:
        idf_vector: numpy数组，形状(词汇数,)
    """
    n_docs = len(documents)
    n_words = len(vocab)
    df = np.zeros(n_words)  # 文档频率

    for doc in documents:
        words = set(tokenize(doc))
        for word in words:
            if word in vocab:
                df[vocab[word]] += 1

    # sklearn使用的平滑IDF公式
    idf_vector = np.log((1 + n_docs) / (1 + df)) + 1
    return idf_vector


def compute_tfidf(tf_matrix, idf_vector):
    """
    计算TF-IDF矩阵并L2归一化。

    参数:
        tf_matrix: TF矩阵
        idf_vector: IDF向量

    返回:
        tfidf_matrix: 归一化后的TF-IDF矩阵
    """
    tfidf = tf_matrix * idf_vector

    # L2归一化（按行）
    norms = np.sqrt(np.sum(tfidf ** 2, axis=1, keepdims=True))
    norms[norms == 0] = 1.0
    tfidf_normalized = tfidf / norms

    return tfidf_normalized


def solve():
    """主函数：演示手动TF-IDF并与sklearn对比。"""
    # ========== 1. 准备文档 ==========
    documents = [
        "机器 学习 是 人工智能 的 核心 技术",
        "深度 学习 是 机器 学习 的 一个 分支",
        "自然 语言 处理 是 人工智能 的 重要 方向",
        "计算机 视觉 和 自然 语言 处理 是 AI 的 两大 方向",
        "机器 学习 包括 监督 学习 和 无监督 学习"
    ]

    print("=" * 60)
    print("1. 文档集合")
    print("=" * 60)
    for i, doc in enumerate(documents):
        print(f"  Doc{i}: {doc}")

    # ========== 2. 构建词汇表 ==========
    vocab, vocab_list = build_vocab(documents)
    print(f"\n词汇表大小: {len(vocab)}")
    print(f"词汇表: {vocab_list}")

    # ========== 3. 手动计算TF ==========
    print("\n" + "=" * 60)
    print("2. TF（词频）矩阵")
    print("=" * 60)

    tf_matrix = compute_tf(documents, vocab)
    print(f"TF矩阵形状: {tf_matrix.shape}")
    print(f"\n{'词汇':<10}", end="")
    for word in vocab_list[:8]:
        print(f"{word:<6}", end="")
    print("...")
    for i in range(len(documents)):
        print(f"Doc{i:<6}", end="")
        for j in range(min(8, len(vocab_list))):
            print(f"{tf_matrix[i, j]:<6.3f}", end="")
        print("...")

    # ========== 4. 手动计算IDF ==========
    print("\n" + "=" * 60)
    print("3. IDF（逆文档频率）向量")
    print("=" * 60)

    idf_vector = compute_idf(documents, vocab)
    for word, idx in sorted(vocab.items(), key=lambda x: x[1]):
        print(f"  {word}: {idf_vector[idx]:.4f}")

    # ========== 5. 手动计算TF-IDF ==========
    print("\n" + "=" * 60)
    print("4. 手动TF-IDF计算结果")
    print("=" * 60)

    tfidf_manual = compute_tfidf(tf_matrix, idf_vector)
    print(f"TF-IDF矩阵形状: {tfidf_manual.shape}")

    # 展示每个文档中TF-IDF值最高的3个词
    for i in range(len(documents)):
        top_indices = np.argsort(tfidf_manual[i])[::-1][:3]
        top_words = [(vocab_list[j], tfidf_manual[i, j]) for j in top_indices
                     if tfidf_manual[i, j] > 0]
        print(f"\n  Doc{i} 关键词: {', '.join(f'{w}({v:.3f})' for w, v in top_words)}")

    # ========== 6. sklearn TfidfVectorizer对比 ==========
    print("\n" + "=" * 60)
    print("5. 与sklearn TfidfVectorizer对比")
    print("=" * 60)

    # 使用相同的分词方式（按空格分割，token_pattern匹配中文和英文）
    vectorizer = TfidfVectorizer(norm='l2', use_idf=True, smooth_idf=True,
                                 sublinear_tf=False,
                                 token_pattern=r'(?u)\b\w+\b')
    tfidf_sklearn = vectorizer.fit_transform(documents).toarray()

    # 由于词汇可能不完全一致，逐词对齐比较
    sklearn_vocab = {word: idx for idx, word in enumerate(vectorizer.get_feature_names_out())}
    print(f"\n手动实现词汇数: {len(vocab)}")
    print(f"sklearn词汇数: {len(sklearn_vocab)}")

    # 对齐比较（只比较两者共有的词）
    max_aligned_diff = 0.0
    total_diff = 0.0
    count = 0
    for word, manual_idx in vocab.items():
        if word in sklearn_vocab:
            sklearn_idx = sklearn_vocab[word]
            col_diff = np.abs(tfidf_manual[:, manual_idx] - tfidf_sklearn[:, sklearn_idx])
            max_aligned_diff = max(max_aligned_diff, np.max(col_diff))
            total_diff += np.sum(col_diff)
            count += len(col_diff)

    print(f"共有词汇数: {sum(1 for w in vocab if w in sklearn_vocab)}")
    print(f"对齐后最大绝对误差: {max_aligned_diff:.6f}")
    if count > 0:
        print(f"对齐后平均绝对误差: {total_diff / count:.6f}")

    # ========== 7. 稀疏性分析 ==========
    print("\n" + "=" * 60)
    print("6. TF-IDF矩阵稀疏性分析")
    print("=" * 60)

    total = tfidf_manual.size
    zeros = np.sum(tfidf_manual == 0)
    sparsity = zeros / total

    print(f"矩阵大小: {tfidf_manual.shape}")
    print(f"总元素数: {total}")
    print(f"零元素数: {zeros}")
    print(f"稀疏率: {sparsity:.2%}")
    print(f"非零元素率: {1 - sparsity:.2%}")


if __name__ == "__main__":
    solve()

```
