# 1. 中心化

> 来源模块: module1_preprocessing
> 原始文件: q14_pca_lda_svd.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】降维与特征选择：PCA、LDA、SVD与卡方检验
【模块】数据预处理
【难度】5
【知识点】PCA主成分分析、LDA线性判别分析、SVD奇异值分解、卡方检验特征选择、sklearn降维
【描述】
高维数据在机器学习中常面临维度灾难问题，降维和特征选择是关键预处理步骤。
本题要求：
1. 手动实现PCA降维（基于特征值分解）
2. 使用sklearn的TruncatedSVD进行奇异值分解降维
3. 使用sklearn的LDA进行有监督降维
4. 使用卡方检验进行特征选择

【要求】
1. 生成一个高维模拟数据集（带标签）
2. 手动实现PCA：计算协方差矩阵 -> 特征值分解 -> 选择主成分 -> 投影
3. 与sklearn的PCA结果对比验证
4. 使用sklearn的TruncatedSVD降维
5. 使用sklearn的LDA降维（有监督）
6. 使用sklearn的chi2进行特征选择
7. 对比各方法降维后的效果

【提示】
- PCA通过特征值分解协方差矩阵找到最大方差方向
- LDA最大化类间方差、最小化类内方差（有监督）
- SVD可以用于稀疏矩阵的降维
- 卡方检验适用于非负特征，衡量特征与标签的独立性
=============================
"""

# ========== 参考答案 ==========

import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.datasets import make_classification
from sklearn.preprocessing import MinMaxScaler


def generate_data(n_samples=200, n_features=20, n_classes=3, n_informative=8, seed=42):
    """
    生成模拟高维数据集。

    返回:
        X: 特征矩阵
        y: 标签
    """
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_informative,
        n_redundant=5,
        n_classes=n_classes,
        n_clusters_per_class=1,
        random_state=seed
    )
    return X, y


def manual_pca(X, n_components=2):
    """
    手动实现PCA降维。

    步骤:
    1. 数据中心化（减去均值）
    2. 计算协方差矩阵
    3. 特征值分解
    4. 按特征值从大到小排序
    5. 选择前n_components个主成分
    6. 投影到主成分空间

    参数:
        X: 数据矩阵 (n_samples, n_features)
        n_components: 目标维度

    返回:
        X_pca: 降维后的数据
        components: 主成分 (n_components, n_features)
        explained_ratio: 各主成分的方差解释比例
        mean: 均值向量
    """
    # 1. 中心化
    mean = np.mean(X, axis=0)
    X_centered = X - mean

    # 2. 协方差矩阵
    n = X_centered.shape[0]
    cov_matrix = np.dot(X_centered.T, X_centered) / (n - 1)

    # 3. 特征值分解
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

    # 4. 按特征值从大到小排序
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sorted_indices]
    eigenvectors = eigenvectors[:, sorted_indices]

    # 5. 选择前n_components个主成分
    components = eigenvectors[:, :n_components].T  # (n_components, n_features)
    top_eigenvalues = eigenvalues[:n_components]

    # 6. 投影
    X_pca = np.dot(X_centered, components.T)

    # 方差解释比例
    total_var = np.sum(eigenvalues)
    explained_ratio = top_eigenvalues / total_var

    return X_pca, components, explained_ratio, mean


def solve():
    """主函数：演示PCA、SVD、LDA降维与卡方检验特征选择。"""
    # ========== 1. 生成数据 ==========
    print("=" * 60)
    print("1. 生成模拟数据")
    print("=" * 60)

    X, y = generate_data(n_samples=200, n_features=20, n_classes=3, n_informative=8)
    print(f"数据形状: {X.shape}")
    print(f"类别数: {len(np.unique(y))}")
    print(f"各类别样本数: {np.bincount(y)}")

    n_components = 2

    # ========== 2. 手动PCA ==========
    print("\n" + "=" * 60)
    print("2. 手动PCA降维")
    print("=" * 60)

    X_pca_manual, components_manual, explained_manual, mean_manual = manual_pca(
        X, n_components=n_components
    )

    print(f"降维后形状: {X_pca_manual.shape}")
    print(f"各主成分方差解释比例: {explained_manual}")
    print(f"累计方差解释比例: {np.cumsum(explained_manual)}")
    print(f"主成分向量形状: {components_manual.shape}")

    # ========== 3. sklearn PCA对比 ==========
    print("\n" + "=" * 60)
    print("3. sklearn PCA对比验证")
    print("=" * 60)

    pca_sklearn = PCA(n_components=n_components)
    X_pca_sklearn = pca_sklearn.fit_transform(X)

    print(f"sklearn方差解释比例: {pca_sklearn.explained_variance_ratio_}")
    print(f"sklearn累计方差解释比例: {np.cumsum(pca_sklearn.explained_variance_ratio_)}")

    # 比较方差解释比例
    var_diff = np.abs(explained_manual - pca_sklearn.explained_variance_ratio_)
    print(f"\n方差解释比例差异: {var_diff}")
    print(f"最大差异: {np.max(var_diff):.2e}")

    # 比较投影结果（注意符号可能相反）
    for i in range(n_components):
        corr = np.abs(np.corrcoef(X_pca_manual[:, i], X_pca_sklearn[:, i])[0, 1])
        print(f"  主成分{i+1} 投影结果相关系数: {corr:.6f}")

    # ========== 4. 各主成分方差解释比例可视化（文本版） ==========
    print("\n" + "=" * 60)
    print("4. PCA各主成分方差解释比例")
    print("=" * 60)

    pca_full = PCA()
    pca_full.fit(X)

    print(f"\n{'主成分':<8} {'方差解释比例':<15} {'累计比例':<15} {'可视化'}")
    print("-" * 60)
    cumulative = 0
    for i in range(min(10, len(pca_full.explained_variance_ratio_))):
        ratio = pca_full.explained_variance_ratio_[i]
        cumulative += ratio
        bar = '#' * int(ratio * 100)
        print(f"  PC{i+1:<5} {ratio:<15.4f} {cumulative:<15.4f} {bar}")

    # ========== 5. TruncatedSVD ==========
    print("\n" + "=" * 60)
    print("5. TruncatedSVD降维")
    print("=" * 60)

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    X_svd = svd.fit_transform(X)

    print(f"降维后形状: {X_svd.shape}")
    print(f"方差解释比例: {svd.explained_variance_ratio_}")
    print(f"累计方差解释比例: {np.cumsum(svd.explained_variance_ratio_)}")

    # SVD与PCA对比
    print(f"\n说明: TruncatedSVD不需要中心化，适合稀疏矩阵")

    # ========== 6. LDA（有监督降维） ==========
    print("\n" + "=" * 60)
    print("6. LDA线性判别分析（有监督降维）")
    print("=" * 60)

    # LDA最多降到 n_classes - 1 维
    n_lda_components = min(n_components, len(np.unique(y)) - 1)
    lda = LinearDiscriminantAnalysis(n_components=n_lda_components)
    X_lda = lda.fit_transform(X, y)

    print(f"LDA目标维度: {n_lda_components} (类别数-1)")
    print(f"降维后形状: {X_lda.shape}")
    print(f"说明: LDA利用标签信息，最大化类间距离，最小化类内距离")

    # 各类在LDA空间的分布
    for c in np.unique(y):
        class_data = X_lda[y == c]
        if X_lda.ndim == 1 or X_lda.shape[1] == 1:
            print(f"  类别{c}: 均值={class_data.mean():.3f}, 标准差={class_data.std():.3f}")
        else:
            print(f"  类别{c}: 均值={class_data.mean(axis=0)}, "
                  f"标准差={class_data.std(axis=0)}")

    # ========== 7. 卡方检验特征选择 ==========
    print("\n" + "=" * 60)
    print("7. 卡方检验特征选择")
    print("=" * 60)

    # 卡方检验要求非负特征，先归一化
    scaler = MinMaxScaler()
    X_nonneg = scaler.fit_transform(X)

    # 选择最好的8个特征
    k_best = 8
    selector = SelectKBest(score_func=chi2, k=k_best)
    X_selected = selector.fit_transform(X_nonneg, y)

    print(f"原始特征数: {X.shape[1]}")
    print(f"选择特征数: {k_best}")
    print(f"选择后形状: {X_selected.shape}")

    # 各特征的卡方分数
    chi2_scores = selector.scores_
    p_values = selector.pvalues_

    selected_indices = selector.get_support(indices=True)

    print(f"\n所有特征的卡方分数和p值:")
    print(f"{'特征':<8} {'卡方分数':<15} {'p值':<15} {'是否选中'}")
    print("-" * 55)

    sorted_indices = np.argsort(chi2_scores)[::-1]
    for idx in sorted_indices:
        selected = "Yes" if idx in selected_indices else "No"
        print(f"  F{idx:<5} {chi2_scores[idx]:<15.4f} {p_values[idx]:<15.6f} {selected}")

    # ========== 8. 方法总结 ==========
    print("\n" + "=" * 60)
    print("8. 降维方法总结")
    print("=" * 60)

    print("""
方法          类型     是否监督  最大目标维度      适用场景
───────────────────────────────────────────────────────
PCA          线性降维   无监督    min(n,p)         方差最大化，通用降维
TruncatedSVD 线性降维   无监督    n_components     稀疏矩阵降维
LDA          线性降维   有监督    n_classes-1      分类任务降维
卡方检验      特征选择   有监督    k(自定义)        非负特征，分类任务
""")


if __name__ == "__main__":
    solve()

```
