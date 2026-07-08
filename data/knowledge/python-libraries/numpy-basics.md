# NumPy Basics

## What is NumPy?

NumPy (Numerical Python) is the foundation of Python's data science ecosystem. It provides a high-performance multidimensional array object (`ndarray`) and tools for working with it. NumPy arrays are stored in contiguous memory, enabling vectorized operations that run at C speed -- orders of magnitude faster than Python lists.

| Operation         | Python list   | NumPy array   |
|-------------------|---------------|---------------|
| 1M element sum    | ~100 ms       | ~1 ms         |
| Memory per elem   | ~28 bytes     | ~8 bytes      |
| Element-wise ops  | Loop required | `a + b` works |

## Array Creation

```python
import numpy as np

# From Python sequences
a = np.array([1, 2, 3, 4, 5])              # 1D array
b = np.array([[1, 2, 3], [4, 5, 6]])       # 2D array

# Pre-filled arrays
np.zeros((3, 4))        # 3x4 of 0.0
np.ones((2, 3))         # 2x3 of 1.0
np.eye(4)               # 4x4 identity matrix
np.full((2, 2), 7)      # 2x2 filled with 7

# Sequences
np.arange(0, 10, 2)     # [0, 2, 4, 6, 8] -- like range()
np.linspace(0, 1, 5)    # [0.0, 0.25, 0.5, 0.75, 1.0] -- 5 evenly spaced points

# Random arrays
np.random.seed(42)      # Reproducibility
np.random.rand(3, 2)    # Uniform [0, 1)
np.random.randn(3, 2)   # Standard normal (mean 0, std 1)
np.random.randint(1, 100, size=(2, 5))   # Random ints
```

## Array Attributes

```python
arr = np.array([[1, 2, 3], [4, 5, 6]])
arr.shape    # (2, 3)   -- tuple of axis sizes
arr.ndim     # 2        -- number of dimensions
arr.size     # 6        -- total elements
arr.dtype    # dtype('int64') -- data type
arr.itemsize # 8        -- bytes per element
```

## Indexing and Slicing

```python
arr = np.array([[1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12]])

arr[0, 0]        # 1 -- single element
arr[0, :]        # [1, 2, 3, 4] -- first row
arr[:, 1]        # [2, 6, 10] -- second column
arr[:2, 1:3]     # [[2, 3], [6, 7]] -- sub-block

# Boolean indexing (powerful!)
arr[arr > 5]     # [6, 7, 8, 9, 10, 11, 12] -- all elements greater than 5
arr[arr % 2 == 0]  # [2, 4, 6, 8, 10, 12] -- all even elements

# Fancy indexing
indices = [0, 2]
arr[indices]     # rows 0 and 2 → [[1,2,3,4], [9,10,11,12]]

# Combined
arr[(arr > 3) & (arr < 9)]  # [4, 5, 6, 7, 8] -- use & not 'and'
```

## Reshaping

```python
a = np.arange(12)          # [0 1 2 ... 11]
a.reshape(3, 4)            # 3x4 matrix
a.reshape(-1, 1)           # Column vector (12x1). -1 means "infer this dimension"
a.flatten()                # Flatten to 1D (always a copy)
a.ravel()                  # Flatten to 1D (returns view when possible -- faster)
a.T                        # Transpose (swap axes)
a.reshape(2, 6).T          # 6x2 -- transpose the reshaped array
```

## Universal Functions (ufuncs)

Ufuncs are vectorized element-wise operations -- no Python loop needed. They apply the operation to every element in parallel at C speed.

```python
a = np.array([1, 2, 3, 4])
b = np.array([5, 6, 7, 8])

a + b          # [6, 8, 10, 12] -- vectorized addition
a * b          # [5, 12, 21, 32]
np.sqrt(a)     # [1.0, 1.414, 1.732, 2.0]
np.exp(a)      # e^a
np.log(a)      # natural log
np.sin(a)      # sine
np.maximum(a, b)  # [5, 6, 7, 8] -- element-wise max
```

## Broadcasting

When operating on arrays with different shapes, NumPy broadcasts the smaller array across the larger one. Rules: (1) align shapes from the right, (2) dimensions must be equal OR one of them is 1.

```python
a = np.array([[1, 2, 3],
              [4, 5, 6]])     # shape (2, 3)

b = np.array([10, 20, 30])    # shape (3,) → broadcast to (2, 3)
a + b  # [[11, 22, 33], [14, 25, 36]]

c = np.array([[100], [200]])  # shape (2, 1) → broadcast to (2, 3)
a + c  # [[101, 102, 103], [204, 205, 206]]

# Common pattern: normalize columns
mean = a.mean(axis=0)         # shape (3,)
normalized = a - mean         # broadcast row-wise
```

## Key Math Operations

```python
a = np.array([[1, 2], [3, 4]])

np.sum(a)       # 10 -- total sum
np.sum(a, axis=0)  # [4, 6] -- sum down columns
np.sum(a, axis=1)  # [3, 7] -- sum across rows
np.mean(a, axis=0) # [2.0, 3.0]
np.std(a)       # Standard deviation
np.min(a), np.max(a), np.argmax(a)

# Matrix operations
np.dot(a, a)    # Matrix multiplication (also a @ a in Python 3.5+)
np.matmul(a, a) # Same as @ operator
```

## Linear Algebra

```python
A = np.array([[4, 2], [3, 1]])

np.linalg.inv(A)            # Inverse
np.linalg.det(A)            # Determinant
eigenvalues, eigenvectors = np.linalg.eig(A)

# SVD (Singular Value Decomposition) -- foundation of PCA, recommendation systems
U, S, Vt = np.linalg.svd(A)

# Solve linear system Ax = b
b = np.array([1, 2])
x = np.linalg.solve(A, b)   # Ax = b  →  x = A⁻¹b
```

## Concatenation

```python
a = np.array([[1, 2], [3, 4]])
b = np.array([[5, 6]])

np.concatenate([a, b], axis=0)   # [[1,2],[3,4],[5,6]] -- stack rows
np.concatenate([a, a], axis=1)   # [[1,2,1,2],[3,4,3,4]] -- stack columns
np.vstack([a, b])                # Shortcut for vertical stack (axis=0)
np.hstack([a, a])                # Shortcut for horizontal stack (axis=1)
```

## Saving and Loading

```python
arr = np.array([[1, 2], [3, 4]])

# Binary .npy format (fast, preserves dtype)
np.save('array.npy', arr)
loaded = np.load('array.npy')

# Text format (human-readable, but slow and lossy)
np.savetxt('array.csv', arr, delimiter=',')
loaded_txt = np.loadtxt('array.csv', delimiter=',')

# Multiple arrays: np.savez / np.savez_compressed
np.savez('multi.npz', a=arr, b=arr * 2)
data = np.load('multi.npz')
data['a'], data['b']
```

## Performance Tips

1. Avoid Python loops -- use vectorized ufuncs and broadcasting
2. Pre-allocate arrays with `np.empty()` instead of appending
3. Use views (`.ravel()`, slices) instead of copies when possible
4. Choose appropriate dtypes: `np.float32` over `np.float64` if precision isn't critical
5. Use `np.einsum()` for complex tensor contractions (fast path)
6. Profile with `%timeit` in IPython/Jupyter to compare approaches
