# 上下文词嵌入

> 来源模块: module1_preprocessing
> 原始文件: q12_word2vec.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】Word2Vec：使用PyTorch实现Skip-gram模型
【模块】数据预处理
【难度】5
【知识点】Word2Vec、Skip-gram、词向量、负采样、PyTorch nn.Module
【描述】
Word2Vec是经典的词向量表示学习方法，通过将词映射到低维稠密向量空间，
捕捉词之间的语义关系。Skip-gram模型根据中心词预测上下文词。

本题要求使用PyTorch实现一个简化版Skip-gram模型（含负采样），
在小规模语料上训练词向量。

【要求】
1. 构建词汇表和训练数据（中心词-上下文词对）
2. 使用PyTorch实现Skip-gram模型（nn.Module）
3. 实现负采样策略
4. 训练模型并提取词向量
5. 使用余弦相似度验证词向量质量（找相似词）

【提示】
- Skip-gram的目标：最大化 P(context | center)
- 负采样将多分类简化为二分类问题
- 词向量维度通常为50-300，这里用较小的维度
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import Counter


def prepare_corpus():
    """准备简单的中文语料（已分词）。"""
    corpus = [
        "机器 学习 是 人工智能 的 核心 技术",
        "深度 学习 是 机器 学习 的 分支",
        "自然 语言 处理 是 人工智能 的 方向",
        "计算机 视觉 是 人工智能 的 方向",
        "机器 学习 包括 监督 学习 无监督 学习",
        "深度 学习 使用 神经 网络",
        "神经网络 有 卷积 网络 循环 网络",
        "自然 语言 处理 使用 深度 学习 技术",
        "计算机 视觉 使用 卷积 神经 网络",
        "人工智能 发展 迅速 技术 进步 很快",
    ]
    return corpus


def build_vocab(corpus, min_count=1):
    """
    构建词汇表。

    返回:
        word2idx: 词到索引的映射
        idx2word: 索引到词的映射
        word_counts: 词频统计
    """
    all_words = []
    for sent in corpus:
        all_words.extend(sent.split())

    word_counts = Counter(all_words)
    # 过滤低频词
    vocab = {w for w, c in word_counts.items() if c >= min_count}

    word2idx = {w: i for i, w in enumerate(sorted(vocab))}
    idx2word = {i: w for w, i in word2idx.items()}

    return word2idx, idx2word, word_counts


def generate_training_data(corpus, word2idx, window_size=2):
    """
    生成Skip-gram训练数据（中心词-上下文词对）。

    参数:
        corpus: 语料列表
        word2idx: 词索引映射
        window_size: 上下文窗口大小

    返回:
        pairs: [(center_idx, context_idx), ...]
    """
    pairs = []
    for sent in corpus:
        words = sent.split()
        indices = [word2idx[w] for w in words if w in word2idx]

        for i, center in enumerate(indices):
            left = max(0, i - window_size)
            right = min(len(indices), i + window_size + 1)
            for j in range(left, right):
                if i != j:
                    pairs.append((center, indices[j]))

    return pairs


class SkipGramModel(nn.Module):
    """Skip-gram模型 with 负采样。"""

    def __init__(self, vocab_size, embedding_dim):
        super(SkipGramModel, self).__init__()
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim

        # 中心词嵌入
        self.center_embeddings = nn.Embedding(vocab_size, embedding_dim)
        # 上下文词嵌入
        self.context_embeddings = nn.Embedding(vocab_size, embedding_dim)

        # 初始化
        init_range = 0.5 / embedding_dim
        self.center_embeddings.weight.data.uniform_(-init_range, init_range)
        self.context_embeddings.weight.data.uniform_(-init_range, init_range)

    def forward(self, center, context, neg_context):
        """
        前向传播（负采样）。

        参数:
            center: 中心词索引 (batch_size,)
            context: 正样本上下文词索引 (batch_size,)
            neg_context: 负样本上下文词索引 (batch_size, n_neg)

        返回:
            loss: 损失值
        """
        # 中心词向量 (batch, dim)
        center_emb = self.center_embeddings(center)
        # 正样本上下文向量 (batch, dim)
        context_emb = self.context_embeddings(context)

        # 正样本得分 (batch,)
        pos_score = torch.sum(center_emb * context_emb, dim=1)
        pos_loss = -torch.nn.functional.logsigmoid(pos_score)

        # 负样本
        # 负样本上下文向量 (batch, n_neg, dim)
        neg_emb = self.context_embeddings(neg_context)
        # 负样本得分 (batch, n_neg)
        neg_score = torch.bmm(neg_emb, center_emb.unsqueeze(2)).squeeze(2)
        neg_loss = -torch.nn.functional.logsigmoid(-neg_score).sum(dim=1)

        return (pos_loss + neg_loss).mean()


def get_negative_samples(vocab_size, n_neg, batch_size, word_probs=None):
    """
    生成负采样索引。

    参数:
        vocab_size: 词汇表大小
        n_neg: 每个正样本对应的负样本数
        batch_size: 批大小
        word_probs: 词频率概率分布（用于按频率采样）

    返回:
        neg_indices: 负样本索引 (batch_size, n_neg)
    """
    if word_probs is not None:
        neg_indices = np.random.choice(
            vocab_size, size=(batch_size, n_neg), p=word_probs
        )
    else:
        neg_indices = np.random.randint(
            0, vocab_size, size=(batch_size, n_neg)
        )
    return torch.LongTensor(neg_indices)


def cosine_similarity(v1, v2):
    """计算两个向量的余弦相似度。"""
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def find_similar(word, embeddings, word2idx, idx2word, top_k=5):
    """找出与给定词最相似的词。"""
    if word not in word2idx:
        print(f"  '{word}' 不在词汇表中")
        return []

    idx = word2idx[word]
    vec = embeddings[idx]

    similarities = []
    for i in range(len(embeddings)):
        if i != idx:
            sim = cosine_similarity(vec, embeddings[i])
            similarities.append((idx2word[i], sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def solve():
    """主函数：训练Skip-gram词向量。"""
    # ========== 1. 准备数据 ==========
    print("=" * 60)
    print("1. 准备语料和词汇表")
    print("=" * 60)

    corpus = prepare_corpus()
    word2idx, idx2word, word_counts = build_vocab(corpus)
    vocab_size = len(word2idx)
    print(f"词汇表大小: {vocab_size}")
    print(f"词频统计: {dict(word_counts.most_common(10))}")

    # 生成训练数据
    pairs = generate_training_data(corpus, word2idx, window_size=2)
    print(f"训练样本数: {len(pairs)}")

    # 计算词频率概率（用于负采样）
    word_freqs = np.zeros(vocab_size)
    for word, idx in word2idx.items():
        word_freqs[idx] = word_counts[word]
    word_freqs = word_freqs ** 0.75  # 平滑
    word_probs = word_freqs / word_freqs.sum()

    # ========== 2. 训练模型 ==========
    print("\n" + "=" * 60)
    print("2. 训练Skip-gram模型")
    print("=" * 60)

    EMBEDDING_DIM = 20
    N_NEG = 5
    BATCH_SIZE = 32
    N_EPOCHS = 100
    LEARNING_RATE = 0.01

    model = SkipGramModel(vocab_size, EMBEDDING_DIM)
    optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE)

    # 转换为numpy数组
    pairs_array = np.array(pairs)

    for epoch in range(N_EPOCHS):
        # 打乱数据
        np.random.shuffle(pairs_array)

        total_loss = 0.0
        n_batches = 0

        for i in range(0, len(pairs_array), BATCH_SIZE):
            batch = pairs_array[i:i + BATCH_SIZE]
            if len(batch) < 2:
                continue

            center = torch.LongTensor(batch[:, 0])
            context = torch.LongTensor(batch[:, 1])
            neg = get_negative_samples(vocab_size, N_NEG, len(batch), word_probs)

            optimizer.zero_grad()
            loss = model(center, context, neg)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        if (epoch + 1) % 20 == 0:
            avg_loss = total_loss / n_batches
            print(f"  Epoch {epoch + 1:3d}/{N_EPOCHS}, Loss: {avg_loss:.4f}")

    print("  训练完成!")

    # ========== 3. 提取词向量 ==========
    print("\n" + "=" * 60)
    print("3. 提取词向量")
    print("=" * 60)

    embeddings = model.center_embeddings.weight.data.numpy()
    print(f"词向量矩阵形状: {embeddings.shape}")

    for word in ["学习", "人工智能", "深度", "神经网络"]:
        if word in word2idx:
            idx = word2idx[word]
            print(f"  {word}: {embeddings[idx][:5]}... (前5维)")

    # ========== 4. 相似词查询 ==========
    print("\n" + "=" * 60)
    print("4. 相似词查询（余弦相似度）")
    print("=" * 60)

    query_words = ["学习", "人工智能", "神经网络", "技术"]
    for word in query_words:
        similar = find_similar(word, embeddings, word2idx, idx2word, top_k=5)
        if similar:
            sim_str = ", ".join(f"{w}({s:.3f})" for w, s in similar)
            print(f"  与 '{word}' 最相似的词: {sim_str}")

    # ========== 5. 词向量质量评估 ==========
    print("\n" + "=" * 60)
    print("5. 词向量分析")
    print("=" * 60)

    # 计算所有词对的相似度矩阵
    words_to_show = ["学习", "深度", "人工智能", "神经网络", "技术", "自然"]
    available = [w for w in words_to_show if w in word2idx]

    print(f"\n相似度矩阵（部分词汇）:")
    header = "".join(f"{w:>8}" for w in available)
    print(f"{'':>8}{header}")

    for w1 in available:
        row = f"{w1:>8}"
        for w2 in available:
            if w1 == w2:
                row += f"{'1.000':>8}"
            else:
                sim = cosine_similarity(
                    embeddings[word2idx[w1]], embeddings[word2idx[w2]]
                )
                row += f"{sim:8.3f}"
        print(row)


if __name__ == "__main__":
    solve()

```
