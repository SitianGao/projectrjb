# Python 编程基础

## 1. 数据类型与变量

Python 是动态类型语言，变量无需声明类型：

```python
x = 42          # int
y = 3.14        # float
name = "Alice"  # str
is_valid = True # bool
```

**核心数据类型**：
- `int` — 整数（任意精度）
- `float` — 浮点数（双精度 IEEE 754）
- `str` — 字符串（不可变 Unicode 序列）
- `bool` — 布尔值 (`True` / `False`)
- `list` — 列表（可变有序集合）
- `tuple` — 元组（不可变有序集合）
- `dict` — 字典（键值对映射）
- `set` — 集合（无序不重复元素）

## 2. 控制流

### 条件判断
```python
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
else:
    grade = "C"
```

### 循环
```python
# for 循环——遍历可迭代对象
for i in range(10):          # 0 到 9
    print(i)

for item in my_list:         # 遍历列表
    print(item)

# while 循环
count = 0
while count < 5:
    print(count)
    count += 1
```

## 3. 函数定义

```python
def add(a: int, b: int) -> int:
    """返回两个整数的和"""
    return a + b

# 默认参数
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"

# 可变参数
def sum_all(*args) -> int:
    return sum(args)
```

## 4. 面向对象

```python
class Student:
    def __init__(self, name: str, student_id: str):
        self.name = name
        self.student_id = student_id
        self.courses = []

    def enroll(self, course: str) -> None:
        """选修课程"""
        self.courses.append(course)

    def __str__(self) -> str:
        return f"Student({self.name}, {self.student_id})"
```

## 5. 常用内置函数

| 函数 | 用途 |
|------|------|
| `len(x)` | 返回序列长度 |
| `range(start, stop, step)` | 生成整数序列 |
| `enumerate(seq)` | 返回 (index, item) 迭代器 |
| `zip(a, b)` | 并行迭代多个序列 |
| `map(fn, seq)` | 对每个元素应用函数 |
| `filter(fn, seq)` | 按条件筛选元素 |
| `sorted(seq, key=...)` | 返回排序后的新序列 |
| `type(x)` | 查看对象类型 |

## 6. 列表推导式

```python
# 传统方式
squares = []
for i in range(10):
    if i % 2 == 0:
        squares.append(i ** 2)

# 列表推导
squares = [i ** 2 for i in range(10) if i % 2 == 0]

# 字典推导
word_lengths = {word: len(word) for word in ["apple", "banana", "cherry"]}
```

## 7. 文件操作

```python
# 读取文件
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()         # 一次性读取全部
    # lines = f.readlines()    # 按行读取

# 写入文件
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Hello, World!\n")
```

## 8. 异常处理

```python
try:
    result = 10 / divisor
except ZeroDivisionError:
    print("除数不能为零")
except Exception as e:
    print(f"未知错误: {e}")
finally:
    print("清理资源")
```

## 9. 常用标准库

- `os` / `os.path` — 操作系统接口与路径操作
- `sys` — 系统参数和函数
- `json` — JSON 编解码
- `re` — 正则表达式
- `datetime` — 日期时间处理
- `collections` — 高级容器（`Counter`, `defaultdict`, `deque`）
- `itertools` — 高效迭代器工具
- `functools` — 高阶函数工具（`reduce`, `partial`, `lru_cache`）

## 10. NumPy 基础

```python
import numpy as np

# 创建数组
a = np.array([1, 2, 3, 4, 5])
b = np.zeros((3, 4))          # 全零矩阵
c = np.ones((2, 3))           # 全一矩阵
d = np.eye(3)                 # 单位矩阵
e = np.arange(0, 10, 0.5)    # 等间距序列
f = np.random.randn(100, 5)  # 随机数矩阵

# 矩阵运算
g = a.T                       # 转置
h = a @ b                     # 矩阵乘法
i = np.linalg.inv(matrix)    # 矩阵求逆
```

> **建议核实**: 具体 API 参数和返回值类型请以 Python 官方文档和 NumPy 文档为准。
