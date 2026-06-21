# 数据结构基础

> 整理自 [shishujuan/data-structure-algorithms](https://github.com/shishujuan/data-structure-algorithms) 系列文章，涵盖链表、栈、二叉堆、二叉树、二分查找、排序算法等核心基础知识。

---

## 1. 链表 (Linked List)

### 1.1 概述
链表是一种基础数据结构，每个结点包含数据域和指向下一结点的指针。插入/删除仅需修改指针，时间为 O(1)；但访问第 k 个元素需 O(k) 遍历。广泛应用于 Linux 内核、Redis、Python 源码等。

### 1.2 结点定义

```c
// 单向链表结点
typedef struct ListNode {
    struct ListNode *next;
    int value;
} ListNode;
```

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
```

### 1.3 基本操作

| 操作 | 时间复杂度 | 说明 |
|------|-----------|------|
| 头插法 | O(1) | 新结点作为新的头结点 |
| 尾插法 | O(n) | 遍历到链尾再插入（若有尾指针则为 O(1)） |
| 删除结点 | O(n) | 需要找到前驱结点 |
| 反转链表 | O(n) | 遍历一次，修改指针方向 |
| 查找 | O(n) | 需遍历整个链表 |

```c
// 头插法
ListNode *listAddNodeHead(ListNode *head, int value) {
    ListNode *node = listNewNode(value);
    if (head) node->next = head;
    return node;
}

// 尾插法
ListNode *listAddNodeTail(ListNode *head, int value) {
    ListNode *node = listNewNode(value);
    if (!head) return node;
    ListNode *cur = head;
    while (cur->next) cur = cur->next;
    cur->next = node;
    return head;
}

// 反转链表（迭代法）
ListNode *listReverse(ListNode *head) {
    ListNode *prev = NULL, *cur = head, *next;
    while (cur) {
        next = cur->next;
        cur->next = prev;
        prev = cur;
        cur = next;
    }
    return prev;
}
```

### 1.4 经典面试题

- **链表反转**：迭代法（三指针法）和递归法
- **判断链表是否有环**：快慢指针法，快指针每次走两步，慢指针每次走一步，相遇则有环
- **找到环的入口点**：快慢指针相遇后，慢指针回到起点，两指针同步单步走，再次相遇即为入口
- **删除倒数第 N 个结点**：快指针先走 N 步，再同步走，快指针到末尾时慢指针指向待删除结点的前驱
- **合并两个有序链表**：递归或迭代，每次取较小结点

---

## 2. 栈 (Stack)

### 2.1 概述
栈是一种 **LIFO（后进先出）** 的基础数据结构，广泛用于函数调用栈、表达式求值、括号匹配、DFS 等场景。

### 2.2 定义（C 数组实现）

```c
typedef struct Stack {
    int capacity;
    int top;
    int items[];   // 柔性数组
} Stack;

#define SIZE(stack)  (stack->top + 1)
#define IS_EMPTY(stack) (stack->top == -1)
#define IS_FULL(stack)  (stack->top == stack->capacity - 1)
```

### 2.3 三种基本操作

```c
// 压入元素
void push(Stack *stack, int v) {
    if (IS_FULL(stack)) exit(E_FULL);
    stack->items[++stack->top] = v;
}

// 弹出栈顶元素
int pop(Stack *stack) {
    if (IS_EMPTY(stack)) exit(E_EMPTY);
    return stack->items[stack->top--];
}

// 查看栈顶元素（不弹出）
int peek(Stack *stack) {
    if (IS_EMPTY(stack)) exit(E_EMPTY);
    return stack->items[stack->top];
}
```

Python 中可直接用列表模拟栈：

```python
stack = []
stack.append(1)   # push
stack.append(2)
top = stack.pop() # pop → 2
peek = stack[-1]  # peek → 1
```

### 2.4 经典应用

**后缀表达式（逆波兰表达式）求值**：

给定后缀表达式 `6 5 2 3 + 8 * + 3 + *`，求值过程：
```
读入数字 → 压栈 → 遇到运算符 → 弹出两个操作数 → 计算结果 → 压回栈
```
遍历一遍即可得结果，时间复杂度 O(n)。

**中缀表达式转后缀**：
- 数字直接输出
- 运算符与栈顶比较优先级；当前优先级 ≤ 栈顶时弹出栈顶，否则压栈
- 左括号直接压栈，遇到右括号则弹出直到左括号弹出

### 2.5 经典面试题

- 后缀表达式求值（栈辅助存储）
- 中缀转后缀表达式
- 括号匹配检查
- 最长有效括号子串
- 用两个栈实现队列
- 用两个队列实现栈
- 设计一个能在 O(1) 获取最小值的栈（最小栈/辅助栈法）

---

## 3. 队列 (Queue)

### 3.1 概述
队列是一种 **FIFO（先进先出）** 的数据结构，应用于任务调度、BFS、消息队列等。

### 3.2 基本操作

```python
from collections import deque

q = deque()
q.append(1)        # enqueue (入队)
q.append(2)
first = q.popleft() # dequeue (出队) → 1
```

### 3.3 变种

| 类型 | 特点 | 应用 |
|------|------|------|
| 循环队列 | 数组实现，head/tail 指针循环使用，避免假溢出 | 缓冲区、调度器 |
| 双端队列 (Deque) | 两端均可插入/删除 | 滑动窗口问题 |
| 优先队列 | 每次出队的是优先级最高的元素（底层用堆实现） | 任务调度、Dijkstra |

---

## 4. 二叉堆 (Binary Heap)

### 4.1 概述
二叉堆是一种特殊的完全二叉树，用数组存储，可以用于实现堆排序和优先队列。分为**最大堆**（父结点 ≥ 子结点）和**最小堆**（父结点 ≤ 子结点）。

### 4.2 数组表示

对于下标为 `i` 的结点（从 0 开始计数）：

```c
#define PARENT(i) ((i-1) / 2)
#define LEFT(i)   (2 * i + 1)
#define RIGHT(i)  (2 * i + 2)
```

高度为 `h` 的堆：元素数范围 `[2^h, 2^(h+1)-1]`，即高度 `h = ⌊log₂ n⌋`。

### 4.3 保持堆性质 — `maxHeapify`

使以 `i` 为根的子树成为最大堆。选出 `i, left, right` 中最大值，如果不为 `i` 则交换并递归向下调整。时间复杂度 O(log n)。

```c
void maxHeapify(int A[], int i, int heapSize) {
    int l = LEFT(i), r = RIGHT(i), largest = i;
    if (l < heapSize && A[l] > A[i])    largest = l;
    if (r < heapSize && A[r] > A[largest]) largest = r;
    if (largest != i) {
        swap(A, i, largest);
        maxHeapify(A, largest, heapSize);
    }
}
```

### 4.4 建堆 — `buildMaxHeap`

从最后一个非叶结点 `n/2-1` 开始，向前依次调用 `maxHeapify`。时间复杂度 O(n)（而非直觉上的 O(n log n)）。

```c
void buildMaxHeap(int A[], int n) {
    for (int i = n/2 - 1; i >= 0; i--)
        maxHeapify(A, i, n);
}
```

### 4.5 堆排序

1. 建最大堆 → 最大值在 A[0]
2. 交换 A[0] 与 A[n-1]，堆大小减一
3. 调用 `maxHeapify(A, 0, heapSize)` 恢复堆性质
4. 重复直到堆大小为 1

时间复杂度 O(n log n)，**不稳定**，空间复杂度 O(1)。

```python
import heapq

# 最小堆（Python heapq 默认为最小堆）
heap = []
heapq.heappush(heap, 5)
heapq.heappush(heap, 2)
min_val = heapq.heappop(heap)  # 2

# 最大堆（取反实现）
heapq.heappush(heap, -5)
max_val = -heapq.heappop(heap)  # 5
```

### 4.6 经典面试题

- Top-K 问题：维护大小为 K 的最小堆，遍历数据流
- 合并 K 个有序链表：用最小堆每次取最小元素
- 数据流中位数：用最大堆存较小一半 + 最小堆存较大一半

---

## 5. 二叉树 (Binary Tree)

### 5.1 基本概念

- **树**：结点和分支组成的层次结构，根结点在最上，叶结点为无子结点的结点
- **二叉树**：每个结点最多两个子结点
- **二叉搜索树 (BST)**：左子树所有值 < 根 < 右子树所有值
- **满二叉树**：除叶结点外每个结点都有两个子结点
- **完全二叉树**：除最后一层外每层都填满，最后一层从左到右填充

### 5.2 结点定义

```c
typedef struct BTNode {
    int value;
    struct BTNode *left;
    struct BTNode *right;
} BTNode;
```

### 5.3 BST 基本操作

```c
// 查找结点
BTNode *bstSearch(BTNode *root, int value) {
    if (!root) return NULL;
    if (root->value == value) return root;
    if (root->value > value) return bstSearch(root->left, value);
    return bstSearch(root->right, value);
}

// 插入结点（递归）
BTNode *bstInsert(BTNode *root, int value) {
    if (!root) return newNode(value);
    if (root->value > value)
        root->left = bstInsert(root->left, value);
    else
        root->right = bstInsert(root->right, value);
    return root;
}

// 查找最小值（最左边结点）
BTNode *bstMin(BTNode *root) {
    if (!root) return NULL;
    while (root->left) root = root->left;
    return root;
}
```

### 5.4 BST 删除结点

**三种情况**：
1. **叶结点**：直接删除
2. **只有一个子结点**：用子结点替换
3. **有两个子结点**：用右子树最小结点（中序后继）替换删除结点

### 5.5 二叉树遍历

| 遍历方式 | 顺序 | 应用 |
|----------|------|------|
| 前序遍历 | 根 → 左 → 右 | 复制树、前缀表达式 |
| 中序遍历 | 左 → 根 → 右 | **BST 中序得到有序序列** |
| 后序遍历 | 左 → 右 → 根 | 删除树（先删子结点） |
| 层序遍历 | 按层逐层 | BFS，求树的宽度 |

```python
# 递归遍历示例
def preorder(root):
    if not root: return
    print(root.val)
    preorder(root.left)
    preorder(root.right)

# 层序遍历（BFS）
def level_order(root):
    from collections import deque
    q = deque([root])
    while q:
        node = q.popleft()
        print(node.val)
        if node.left: q.append(node.left)
        if node.right: q.append(node.right)
```

### 5.6 经典面试题

- 判断二叉树是否对称/是否为镜像
- 二叉树的最大深度和最小深度
- 判断是否为平衡二叉树（AVL 条件）
- 最近公共祖先 (LCA)
- 重建二叉树（从前序 + 中序，或后序 + 中序）
- 二叉树的序列化与反序列化
- 求二叉树的宽度（层序遍历 + 计数）

---

## 6. 二分查找 (Binary Search)

### 6.1 基本算法

从有序数组中间开始，每次排除一半数据。时间复杂度 O(log n)。

```c
int binarySearch(int a[], int n, int t) {
    int l = 0, u = n - 1;
    while (l <= u) {
        int m = l + (u - l) / 2;  // 防溢出写法
        if (t > a[m])      l = m + 1;
        else if (t < a[m]) u = m - 1;
        else               return m;
    }
    return -(l + 1);  // 不存在时返回-(插入位置+1)
}
```

返回值说明：当 `t` 不存在时返回 `-(l+1)`（而非 `-1`），因为此时 `l` 恰好是 `t` 应该插入的位置，这在 DHT 一致性哈希等场景中有用。

### 6.2 变种问题

| 变种 | 循环不变式关键 | 说明 |
|------|---------------|------|
| 查找第一次出现位置 | `a[l] < t ≤ a[u]` 且 `l < u` | 维护开区间 (l, u] |
| 查找最后一次出现位置 | `a[l] ≤ t < a[u]` 且 `l < u` | 维护开区间 [l, u) |
| 旋转数组查找 | 先判断哪边有序 | 每次排除一半 |
| 旋转数组找最小值 | 与右端点比较 | 无重复值时简单 |

### 6.3 相关面试题

- 在旋转有序数组中查找目标值
- 查找旋转有序数组中的最小值
- 求一个数的平方根（二分逼近）
- 在只有两个不同元素的有序数组中查找两个元素的边界

---

## 7. 排序算法

### 7.1 算法总览

| 算法 | 平均时间 | 最坏时间 | 空间 | 稳定性 |
|------|---------|---------|------|--------|
| 插入排序 | O(n²) | O(n²) | O(1) | ✅ 稳定 |
| 希尔排序 | O(n¹·³) | O(n²) | O(1) | ❌ 不稳定 |
| 选择排序 | O(n²) | O(n²) | O(1) | ❌ 不稳定 |
| 冒泡排序 | O(n²) | O(n²) | O(1) | ✅ 稳定 |
| 归并排序 | O(n log n) | O(n log n) | O(n) | ✅ 稳定 |
| 快速排序 | O(n log n) | O(n²) | O(log n) | ❌ 不稳定 |
| 堆排序 | O(n log n) | O(n log n) | O(1) | ❌ 不稳定 |
| 计数排序 | O(n+k) | O(n+k) | O(n+k) | ✅ 稳定 |

### 7.2 插入排序

核心思想：将未排序元素逐个插入到已排序部分的正确位置。**数据基本有序时性能很高，最好 O(n)**。

```c
void insertSort(int a[], int n) {
    for (int i = 1; i < n; i++) {
        int key = a[i], j;
        for (j = i; j > 0 && a[j-1] > key; j--)
            a[j] = a[j-1];
        a[j] = key;
    }
}
```

### 7.3 希尔排序

对间隔为 `N/2, N/4, ..., 1` 的子序列分别执行插入排序，最终得到整体有序。在数据量中等且基本无序时比插入排序快。

### 7.4 选择排序

第 `i` 次选取第 `i` 小的元素放在位置 `i`。不论数据是否有序，比较次数恒为 `n(n-1)/2`。

### 7.5 归并排序

分治思想：将数组分为两半，分别递归排序，然后合并两个有序子数组。时间复杂度稳定 O(n log n)，但需要 O(n) 额外空间。

### 7.6 快速排序

- 选取 **基准值 (pivot)**，将数组分为 ≤ pivot 和 ≥ pivot 两部分
- 递归地对两部分排序
- 平均 O(n log n)，但**最坏 O(n²)**（如数组已有序且 pivot 选端点）
- 优化：**三数取中**法选 pivot、小数组改用插入排序、尾递归优化

### 7.7 计数排序

适用于元素范围有限的场景（如 0~k 的整数）。统计每个值出现次数，然后按序回填。时间复杂度 O(n+k)，**是稳定排序**。

---

## 8. 哈希表 (Hash Table)

- 通过哈希函数将键映射到桶，平均 O(1) 查找/插入/删除
- 哈希冲突解决：
  - **链地址法**：每个桶存一个链表
  - **开放地址法**：冲突时线性探测、二次探测或双重哈希找下一个空位
- 负载因子 = 元素数 / 桶数，过高时需 rehash（扩容并重新哈希所有元素）
- Python 的 `dict` 和 `set` 基于哈希表实现

---

## 9. 图 (Graph)

### 9.1 表示方式

| 方式 | 空间 | 适用场景 |
|------|------|----------|
| 邻接矩阵 | O(V²) | 稠密图、需要 O(1) 判断边 |
| 邻接表 | O(V+E) | 稀疏图、大规模图 |

### 9.2 遍历

- **DFS（深度优先）**：栈/递归实现，适合路径搜索、连通性判断、拓扑排序
- **BFS（广度优先）**：队列实现，适合最短路径（无权图）、层级遍历

### 9.3 最短路径 & 拓扑

- **Dijkstra**：带权图单源最短路径，贪心 + 优先队列，O((V+E) log V)
- **拓扑排序**：DAG 的线性排序，Kahn 算法（BFS + 入度表）或 DFS 后序遍历

---

## 10. 时间复杂度速查

| 复杂度 | 典型算法 |
|--------|---------|
| O(1) | 数组随机访问、哈希表查找 |
| O(log n) | 二分查找、平衡 BST 操作、堆操作 |
| O(n) | 线性查找、遍历、建堆 |
| O(n log n) | 归并排序、快速排序(平均)、堆排序 |
| O(n²) | 冒泡排序、插入排序、选择排序 |
| O(2ⁿ) | 子集枚举（指数级） |
| O(n!) | 全排列枚举 |

---

> **参考来源**：[shishujuan/data-structure-algorithms](https://github.com/shishujuan/data-structure-algorithms) — 涵盖链表、栈、二叉堆、二叉树(BST)、二分查找、排序算法、字符串、递归、背包问题、数字题、随机算法等 14 个专题的完整实现与面试题解析。
>
> **建议核实**：具体算法的边界条件和优化细节请以教材（如《算法导论》《编程珠玑》）为准。
