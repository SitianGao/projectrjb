# 编程题 13：网格迷宫最短路

## 题目描述

给定一个 `m x n` 的网格，`0` 表示可通行，`1` 表示障碍。机器人从左上角 `(0, 0)` 出发，想走到右下角 `(m-1, n-1)`。每次只能上下左右移动一格，求最少步数；如果无法到达，返回 `-1`。

## 输入输出

输入：

```text
grid = [
  [0, 0, 0],
  [1, 1, 0],
  [0, 0, 0]
]
```

输出：

```text
4
```

## 知识点

- BFS
- 队列
- 网格搜索
- 最短路径

## 解题思路

无权图最短路优先使用 BFS。把每个可通行格子看作图中的节点，上下左右相邻看作边。BFS 第一次到达终点时，层数就是最短步数。

## 参考实现

```python
from collections import deque

def shortest_path_grid(grid):
    if not grid or not grid[0]:
        return -1

    m, n = len(grid), len(grid[0])
    if grid[0][0] == 1 or grid[m - 1][n - 1] == 1:
        return -1

    q = deque([(0, 0, 0)])
    visited = {(0, 0)}
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while q:
        x, y, dist = q.popleft()
        if x == m - 1 and y == n - 1:
            return dist

        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < m and 0 <= ny < n:
                if grid[nx][ny] == 0 and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    q.append((nx, ny, dist + 1))

    return -1
```

## 常见错误

- 用 DFS 求最短路，容易得到非最短路径。
- 入队后没有立刻标记访问，导致重复入队。
- 没有处理起点或终点是障碍的情况。
