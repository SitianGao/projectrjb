# NumPy基础

## 什么是NumPy？

NumPy（Numerical Python）是Python数据科学生态系统的基础。它提供了高性能的多维数组对象（`ndarray`）以及用于操作该对象的工具。NumPy数组存储在连续内存中，支持以C语言速度运行的向量化操作——比Python列表快数个数量级。

| 操作         | Python列表   | NumPy数组   |
|-------------------|---------------|---------------|
| 100万元素求和    | ~100 ms       | ~1 ms         |
| 每元素内存占用   | ~28 bytes     | ~8 bytes      |
| 逐元素运算  | 需要循环 | `a + b` 直接可用 |

## 数组创建

```python
import numpy as np

# 从Python序列创建
a = np.array([1, 2, 3, 4, 5])              # 一维数组
b = np.array([[1, 2, 3], [4, 5, 6]])       # 二维数组

# 预填充数组
np.zeros((3, 4))        # 3x4 的全零数组
np.ones((2, 3))         # 2x3 的全一数组
np.eye(4)               # 4x4 单位矩阵
np.full((2, 2), 7)      # 2x2 填充为7的数组

# 序列生成
np.arange(0, 10, 2)     # [0, 2, 4, 6, 8] -- 类似于 range()
np.linspace(0, 1, 5)    # [0.0, 0.25, 0.5, 0.75, 1.0] -- 5个均匀分布的点

# 随机数组
np.random.seed(42)      # 设置随机种子以确保可复现性
np.random.rand(3, 2)    # [0, 1) 均匀分布
np.random.randn(3, 2)   # 标准正态分布（均值0，标准差1）
np.random.randint(1, 100, size=(2, 5))   # 随机整数
```

## 数组属性

```python
arr = np.array([[1, 2, 3], [4, 5, 6]])
arr.shape    # (2, 3)   -- 各轴大小的元组
arr.ndim     # 2        -- 维度数
arr.size     # 6        -- 总元素数
arr.dtype    # dtype('int64') -- 数据类型
arr.itemsize # 8        -- 每个元素的字节数
```

## 索引与切片

```python
arr = np.array([[1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]])

arr[0, 0]        # 1 -- 单个元素
arr[0, :]        # [1, 2, 3, 4] -- 第一行
arr[:, 1]        # [2, 6, 10] -- 第二列
arr[:2, 1:3]     # [[2, 3], [6, 7]] -- 子块

# 布尔索引（非常强大！）
arr[arr > 5]     # [6, 7, 8, 9, 10, 11, 12] -- 所有大于5的元素
arr[arr % 2 == 0]  # [2, 4, 6, 8, 10, 12] -- 所有偶数元素

# 花式索引
indices = [0, 2]
arr[indices]     # 第0行和第2行 → [[1,2,3,4], [9,10,11,12]]

# 组合使用
arr[(arr > 3) & (arr < 9)]  # [4, 5, 6, 7, 8] -- 使用 & 而非 'and'
```

## 重塑

```python
a = np.arange(12)          # [0 1 2 ... 11]
a.reshape(3, 4)            # 3x4 矩阵
a.reshape(-1, 1)           # 列向量 (12x1)。-1 表示"自动推断该维度"
a.flatten()                # 展平为一维（始终返回副本）
a.ravel()                  # 展平为一维（尽可能返回视图 -- 更快）
a.T                        # 转置（交换轴）
a.reshape(2, 6).T          # 6x2 -- 对重塑后的数组进行转置
```

## 通用函数（ufuncs）

ufuncs是向量化的逐元素操作——无需Python循环。它们以C语言速度对每个元素并行执行操作。

```python
a = np.array([1, 2, 3, 4])
b = np.array([5, 6, 7, 8])

a + b          # [6, 8, 10, 12] -- 向量化加法
a * b          # [5, 12, 21, 32]
np.sqrt(a)     # [1.0, 1.414, 1.732, 2.0]
np.exp(a)      # e^a
np.log(a)      # 自然对数
np.sin(a)      # 正弦
np.maximum(a, b)  # [5, 6, 7, 8] -- 逐元素取最大值
```

## 广播

当对不同形状的数组进行操作时，NumPy会将较小的数组广播到较大的数组上。规则：(1) 从右侧对齐形状，(2) 维度必须相等或其中之一为1。

```python
a = np.array([[1, 2, 3],
              [4, 5, 6]])     # 形状 (2, 3)

b = np.array([10, 20, 30])    # 形状 (3,) → 广播为 (2, 3)
a + b  # [[11, 22, 33], [14, 25, 36]]

c = np.array([[100], [200]])  # 形状 (2, 1) → 广播为 (2, 3)
a + c  # [[101, 102, 103], [204, 205, 206]]

# 常见模式：归一化列
mean = a.mean(axis=0)         # 形状 (3,)
normalized = a - mean         # 按行广播
```

## 关键数学运算

```python
a = np.array([[1, 2], [3, 4]])

np.sum(a)       # 10 -- 总和
np.sum(a, axis=0)  # [4, 6] -- 沿列方向求和
np.sum(a, axis=1)  # [3, 7] -- 沿行方向求和
np.mean(a, axis=0) # [2.0, 3.0]
np.std(a)       # 标准差
np.min(a), np.max(a), np.argmax(a)

# 矩阵运算
np.dot(a, a)    # 矩阵乘法（Python 3.5+ 中也可用 a @ a）
np.matmul(a, a) # 等同于 @ 运算符
```

## 线性代数

```python
A = np.array([[4, 2], [3, 1]])

np.linalg.inv(A)            # 逆矩阵
np.linalg.det(A)            # 行列式
eigenvalues, eigenvectors = np.linalg.eig(A)

# SVD（奇异值分解）-- PCA、推荐系统的基础
U, S, Vt = np.linalg.svd(A)

# 求解线性方程组 Ax = b
b = np.array([1, 2])
x = np.linalg.solve(A, b)   # Ax = b  →  x = A⁻¹b
```

## 拼接

```python
a = np.array([[1, 2], [3, 4]])
b = np.array([[5, 6]])

np.concatenate([a, b], axis=0)   # [[1,2],[3,4],[5,6]] -- 按行堆叠
np.concatenate([a, a], axis=1)   # [[1,2,1,2],[3,4,3,4]] -- 按列堆叠
np.vstack([a, b])                # 垂直堆叠的快捷方式 (axis=0)
np.hstack([a, a])                # 水平堆叠的快捷方式 (axis=1)
```

## 保存与加载

```python
arr = np.array([[1, 2], [3, 4]])

# 二进制 .npy 格式（速度快，保留dtype）
np.save('array.npy', arr)
loaded = np.load('array.npy')

# 文本格式（人类可读，但速度慢且有精度损失）
np.savetxt('array.csv', arr, delimiter=',')
loaded_txt = np.loadtxt('array.csv', delimiter=',')

# 多个数组：np.savez / np.savez_compressed
np.savez('multi.npz', a=arr, b=arr * 2)
data = np.load('multi.npz')
data['a'], data['b']
```

## 性能优化建议

1. 避免Python循环 -- 使用向量化的ufuncs和广播
2. 使用 `np.empty()` 预分配数组，而非逐步追加
3. 尽可能使用视图（`.ravel()`、切片）而非副本
4. 选择合适的数据类型：如果精度要求不高，用 `np.float32` 代替 `np.float64`
5. 使用 `np.einsum()` 处理复杂张量缩并（快速路径）
6. 在IPython/Jupyter中使用 `%timeit` 进行性能分析，对比不同方法
