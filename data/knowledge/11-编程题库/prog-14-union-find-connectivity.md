# 编程题 14：朋友圈数量

## 题目描述

给定 `n` 个学生和若干组朋友关系。如果 A 和 B 是朋友，B 和 C 是朋友，则 A、B、C 属于同一个朋友圈。请计算朋友圈数量。

## 输入输出

输入：

```text
n = 5
relations = [(0, 1), (1, 2), (3, 4)]
```

输出：

```text
2
```

## 知识点

- 并查集
- 连通分量
- 图建模

## 解题思路

把每个学生看作一个节点，把朋友关系看作无向边。用并查集合并朋友关系，最后统计有多少个不同的根节点。

## 参考实现

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1

def count_friend_circles(n, relations):
    uf = UnionFind(n)
    for a, b in relations:
        uf.union(a, b)
    return len({uf.find(i) for i in range(n)})
```

## 常见错误

- 只统计直接朋友关系，没有合并传递关系。
- `find` 没有路径压缩，数据量大时性能变差。
- 合并后没有重新查找根节点，导致统计结果错误。
