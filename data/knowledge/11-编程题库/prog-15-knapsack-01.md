# 编程题 15：01 背包

## 题目描述

有 `n` 个物品，每个物品有重量 `weights[i]` 和价值 `values[i]`。背包容量为 `capacity`，每个物品最多选一次，求能获得的最大总价值。

## 输入输出

输入：

```text
weights = [2, 3, 4]
values = [4, 5, 10]
capacity = 6
```

输出：

```text
14
```

## 知识点

- 动态规划
- 01 背包
- 状态转移

## 解题思路

定义 `dp[c]` 表示容量不超过 `c` 时能获得的最大价值。遍历每个物品时，容量必须从大到小更新，避免同一物品被重复选择。

状态转移：

```text
dp[c] = max(dp[c], dp[c - weight] + value)
```

## 参考实现

```python
def knapsack_01(weights, values, capacity):
    dp = [0] * (capacity + 1)

    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)

    return dp[capacity]
```

## 常见错误

- 容量从小到大遍历，导致一个物品被重复使用，变成完全背包。
- 没有明确 `dp[c]` 的含义，转移式容易写反。
- 忘记处理容量小于物品重量时不能选择该物品。
