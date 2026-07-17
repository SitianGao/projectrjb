# 编程题 11：区间和查询

## 题目描述

给定一个长度为 `n` 的整数数组 `nums`，以及 `q` 次查询。每次查询给出区间 `[l, r]`，要求返回数组下标从 `l` 到 `r` 的元素和。下标从 0 开始。

## 输入输出

输入：

```text
nums = [1, 3, 5, 7, 9]
queries = [(0, 2), (1, 3), (2, 4)]
```

输出：

```text
[9, 15, 21]
```

## 知识点

- 前缀和
- 数组
- 区间查询

## 解题思路

构造前缀和数组 `prefix`，其中 `prefix[i]` 表示前 `i` 个元素之和。区间 `[l, r]` 的和为：

```text
prefix[r + 1] - prefix[l]
```

预处理时间复杂度为 O(n)，每次查询为 O(1)。

## 参考实现

```python
def range_sum(nums, queries):
    prefix = [0]
    for x in nums:
        prefix.append(prefix[-1] + x)

    ans = []
    for l, r in queries:
        ans.append(prefix[r + 1] - prefix[l])
    return ans
```

## 常见错误

- 忘记给 `prefix` 开头补 0，导致区间边界难处理。
- 混淆 `[l, r]` 闭区间和 Python 切片的左闭右开规则。
- 查询很多时仍逐段遍历，导致总复杂度过高。
