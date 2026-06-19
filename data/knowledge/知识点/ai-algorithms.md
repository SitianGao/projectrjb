<center><h1>
    人工智能第一次实验报告
    </h1></center>

<center><h2>AStar求解八数码问题</h2></center>

| 课程：人工智能原理 | 年级专业：19级软件工程 |
| ------------------ | ---------------------- |
| 姓名：郑有为       | 学号：19335286         |

## 目录

[toc]

## 一、N数码问题

### 1.1 N数码问题简介

N数码问题又称为重拍拼图游戏，以8数码为例：在 3X3 的方格棋盘上，放置8个标有1、2、3、4、5、6、7、8数字的方块和1个空白块，空白块可以上下左右移动，游戏要求通过反复移动空白格，寻找一条从某初始状态到目标状态的移动路径。

令$W, H$为棋盘的宽高，有$N = W \times H - 1$，维度越高求解难度也就越高。

N数码问题的求解策略有广度优先搜索和启发式搜索等，启发式搜索能够利用N数码信息，加快搜索速度。使用广度优先搜索和A*搜索算法都可以求得最优解，即总开始状态到结束状态的最短路径。

### 1.2 N数码问题的不可解情况

首先给出逆序数的定义：对于串中相邻的一对数，如果位置较前的数大于位置靠后的数，则成为一对逆序，一个串的逆序总数成为逆序数。例如 $21432$ 的逆序数为3，逆序对包括 $21$，$43$，$32$

在N数码中，并不是所有状态都是可解的。将一个状态表示为一维数组的形式，计算除了空位置（0）之外的所有数字的逆序数之和，如果初始状态和结束状态的逆序奇数的偶性相同，则相互可达，否则相互不可达。

简单证明上述结论的必要性：当空块左右移动是不改变逆序数，上下移动时，相当于一个非空块向前或向后移动2格子，如果跨过的两个数字都大于/小于移动的数字，则逆序数可能增减2，如果两个数字一个大一个小，逆序数不变。

因此在设计测试样例时需要考虑逆序数为偶数，否则程序不会终止。例如：[1,2,3,4,5,6,8,7,0] 就是一个不可解情况。

## 二、A*搜索算法

### 2.1 基本思想

A\*搜索算法利用启发性信息来引导搜索，动态地确定搜索节点的排序，每次选择最优的节点往下搜索，可以高效地减少搜索范围，减少求解的问题的时间。

A\*算法用估价函数来衡量一个节点的优先度，优先度越小的节点越应该被优先访问。估价函数用如下公式表示：$f(n) = h(n) + d(n)$，$h(n)$是对于当前状态的估计值，例如曼哈顿距离，$d(h)$是已经付出的搜索代价，例如节点的深度。

A\*算法和A搜索算法的不同之处在于，A\*保证对于所有节点都有：$h(n) \le h^*(n)$，其中$h^*(n)$为当前状态到目的状态的最优路径的代价。

在本次实验中，我们选择曼哈顿距离为$h(n)$，节点深度为$d(n)$，在实际考虑中：所有放错位的数码个数、后续节点不正确的数码个数都可以作为估价方法，也可以选择多个估价方法并给予适当权重来加快搜索速度。	

### 2.2 算法步骤

1. 将起始节点放入 explore_list 中
2. 如果 explore_list 为空，则搜索失败，问题无解，否则循环求解
   1. 取出 explore_list 的估价函数最小的节点，置为当前节点 current_state，若 current_state 为目标节点，则搜索成功，计算解路径，退出
   2. 寻找所有与 current_state 邻接且未曾被发现的节点，插入到 explore_list 中，并加入 visited_list 中，表示已发现

## 三、原程序说明

原程序在搜索基础上使用了估价函数来进行优化，但无法求得最优解。原程序在每一个状态的下一个可行状态中选择评估函数最小的一个状态作为下一步，搜索的节点为链状结构（可能有环，而一般的A*搜索结果是树状结构）。

**程序步骤**：

1. 创建 openTable（队列结构） 和 closeTable，并将初始节点加入 openTable
2. 如果 openTable 为空，则结束程序，问题无解，否则循环求解
   1. 从 openTable Pop出一个状态并将其加入到 closeTable 中
   2. 确定下一步的节点：从当前可行状态中寻找下一步可行状态，选择估价值最小的一个加入到 openTable 中
   3. 判断当前状态和终止状态是否相等，若相等则结束程序输出路径

**原程序没有充分利用 closeTable，因此可能会出现死循环**（未证明）：

* 一个状态在选择它的下一个状态时不会选择父亲状态，但是有可能选择父亲状态的父亲状态（即爷爷状态），导致有可能出现一个长度至少为3的回路。

要修改程序，必须修改2-1、2-2 步骤

* 选取的新状态应该是 openTable 估价值最小的状态，
* 应该将当前所有可行状态加入到 openTable 中，而不是仅加入估价值最小的状态，
* 应充分利用 closeTable，状态不能重复出现

## 四、程序修改

我们在源程序的基础上修改程序，使其能够实现最优求解。

**正确的A\*搜索算法步骤**：

* 将起始节点放入 explore_list 中
* 如果 explore_list 为空，则搜索失败，问题无解，否则循环求解
  * 取出 explore_list 的估价函数最小的节点，置为当前节点 current_state
  * 若 current_state 为目标节点，则搜索成功，计算解路径，退出
  * 寻找所有与 current_state 邻接且未曾被发现的节点，插入到 explore_list 中，并加入 visited_list 中，表示已发现

### 4.1 程序修改

* **State类：表示一个状态**
  * 在源代码的基础上，做了以下修改：
    * 删除`def solve(self)`方法：将搜索职责转移到Solution类上，State类只负责管理当前的状态。
    * 增加属性值`self.d`：状态的深度，并在`nextStep()`方法中维护，起始状态的深度为0，终点状态的深度为最右搜索路径长度。
    * 修改`getFunctionValue(self)`方法：返回值为哈夫曼距离和状态深度的和，这是一个满足A*搜索的评估函数。

* **Solution类：负责求解N数码问题**
  * 记录起始状态、结束状态、当前状态和搜索结点总数，并用三个链表记录待检查状态链表、已检查状态链表和最优路径。
  * `getBestState`方法：遍历待检查状态链表 explore_list，返回估价函数最小的状态
  * `isVisited`方法：遍历已检查状态链表 visited_list， 返回 True 如果该状态已经存在于 visited_list 中
  * `getPath`方法：获取最终解路径，保存在 path_list 中
  * **`AStarSolve`方法**：使用A*搜索策略求解问题
  * **`BFSSolve`方法**：使用BFS策略求解问题，用于测试A*算法是否正确

### 4.2 复杂度分析

由于我们使用普通的链表来记录记录待检查状态链表（`explore_list`）、已检查状态链表（`visited_list`）和最优路径（`path_list`）:

* 每次获取估价函数最小的状态时需要遍历 `explore_list`，时间复杂度为$O(n)$
* 每次判断一个状态是否已经被搜索过时需要遍历`visited_list`，时间复杂度为$O(n)$

设最终所搜的节点数目为$M$，有复杂度为$O(M^2)$

### 4.3 代码优化

在修改程序的基础上对待检查状态链表（`explore_list`）和已检查状态链表（`visited_list`）进行优化：

* 考虑它们的特性，用一个优先队列来实现 `explore_list`，用一个哈希表（字典）来实现 `visited_list`，可以将每次获取估价函数最小的状态和每次判断一个状态是否已经被搜索过的复杂度都降为$O(1)$
* 而`explore_list`插入节点并维护优先队列结构的复杂度为$O(\log(n))$

从而让整个算法复杂度降低到$O(M\log(M))$，从下面的测试中可以看到优化的运行速度优于优化前的运行速度。

最后，可以通过优化估价函数来缩短搜索次数，例如使用错误码数、曼哈顿距离的加权。

## 五、测试结果

### 5.1 使用BFS验证A*算法正确性

* 对于8数码测试样例：

  ```
  begin = State(np.array([[1, 5, 2],[7, 0, 4],[6, 3, 8]]))
  end = State(np.array([[1, 2, 3],[4, 5, 6],[7, 8, 0]]))
  ```

* **原程序测试结果：（非最优路径）**

  ```
  ...
  Total steps is 28
  ```

* BFS结果：耗时长，访问节点数多，求得最短路径及其长度 14 。

  ```
  ...
  Total search node is 5905
  Total steps is 14
  Totally cost is 105.18757700920105 s

* 优化前的结果：正确求得最短路径，耗时0.02秒

  ```
  ...
  Total search node is 53
  Total steps is 14
  Totally cost is 0.020945310592651367 s
  ```

* 优化后的结果：正确求得最短路径，耗时0.01秒

  ```
  ...
  Total search node is 52
  Total steps is 14
  Totally cost is 0.010965108871459961 s
  ```

### 5.2 优化前后效率对比

* 对于下面八数码测试样例：

  ```
  begin = State(np.array([[1, 3, 2],[4, 5, 6],[8, 7, 0]]))
  end = State(np.array([[1, 2, 3],[4, 5, 6],[7, 8, 0]]))
  ```

* 优化前的结果：需要 9 秒才能求出最优解

  ```
  ...
  Total search node is 1664
  Total steps is 20
  Totally cost is 9.302738666534424 s
  ```

* 优化后的结果：只需要 0.6 秒就能求出最优解

  ```
  ...
  Total search node is 2730
  Total steps is 20
  Totally cost is 0.641481876373291 s
  ```

### 5.3 24数码问题求解测试

* 对于以下24数码的测试样例：

  ```
  begin = State(np.array([[ 1,  2,  3,  4,  5],
                          [ 6, 12,  8,  9, 10],
                          [11,  7, 13, 14, 15],
                          [16, 19, 18, 17, 20],
                          [21, 22, 23, 24,  0]]))
  
  end = State(np.array([[ 1,  2,  3,  4,  5],
                        [ 6,  7,  8,  9, 10],
                        [11, 12, 13, 14, 15],
                        [16, 17, 18, 19, 20],
                        [21, 22, 23, 24,  0]]))
  ```

* AStarSearchOptimized 运行输出：求得最短路径及其长度为26，此时非优化A*与BFS无法在可接受时间内完成求解。

  ```
  ...
  ->
  26: 
  1 2 3 4 5  
  6 7 8 9 10  
  11 12 13 14 15  
  16 17 18 19 20  
  21 22 23 0 24  
  ->
  27: 
  1 2 3 4 5  
  6 7 8 9 10  
  11 12 13 14 15  
  16 17 18 19 20  
  21 22 23 24 0  
  ->
  Total search node is 91640
  Total steps is 26
  Totally cost is 36.743870973587036 s
  ```

## 附录

### 附录 1 - 重写程序 AStarSearch.py 

```python
import numpy as np
import time

class Solution:

    # State:   self.begin_state   起始状态
    # State:   self.end_state     结束状态
    # State:   self.current_state 当前状态
    # int:     self.searched_num  搜索结点总数
    # State[]: self.explore_list  待检查状态链表
    # State[]: self.visited_list  已检查状态链表
    # State[]: self.path_list     搜索最优路径

    # 初始化A*搜索
    def __init__(self, begin_state, end_state):
        self.begin_state = begin_state
        self.end_state = end_state
        self.current_state = None
        self.searched_num = 0
        self.explore_list = []
        self.visited_list = []
        self.path_list = []

    # 返回 explore_list 中 估价函数最小的节点
    def getBestState(self):

        return_state = self.explore_list[0]
        for explore_state in self.explore_list:
            if explore_state.f < return_state.f:
                return_state = explore_state

        return return_state


    # isVisited 返回 True 如果该状态已经存在于 visited_state 中
    def isVisited(self, next_state):
        for visited_state in self.visited_list:
            if (visited_state.state == next_state.state).all():
                return True
        return False

    # getPath 获取最终解路径，保存在 path_list 中
    def getPath(self):
        temp_state = self.current_state
        self.path_list.append(self.end_state)

        while temp_state.parent and temp_state.parent != self.begin_state:
            self.path_list.append(temp_state.parent)
            temp_state = temp_state.parent

        self.path_list.append(self.begin_state)
        self.path_list.reverse()

    # AStarSolve 搜索
    def AStarSolve(self):

        # 将起始节点放入 explore_list 中
        self.explore_list.append(self.begin_state)
        self.visited_list.append(self.begin_state)

        # 如果 explore_list 为空，则搜索失败，问题无解，否则循环求解
        while len(self.explore_list) > 0:
            self.searched_num += 1
            if self.searched_num % 1000 == 0:
                print(self.searched_num)

            # 取出 explore_list 的估价函数最小的节点，置为当前节点 current_state
            # 若 current_state 为目标节点，则搜索成功，计算解路径，退出
            self.current_state = self.getBestState()
            self.explore_list.remove(self.current_state)
            if (self.current_state.state == self.end_state.state).all():
                self.getPath()
                break

            # 寻找所有与 current_state 邻接且未曾被发现的节点，插入到 explore_list 中
            # 并加入 visited_list 中，表示已发现
            next_list = self.current_state.nextStep()
            for next_state in next_list:
                if not self.isVisited(next_state):
                    self.explore_list.append(next_state)
                    self.visited_list.append(next_state)

    # BFS 用于测试A*是否求得了最优解
    def BFSSolve(self):

        # 将起始节点放入 explore_list 中
        self.explore_list.append(self.begin_state)
        self.visited_list.append(self.begin_state)

        # 如果 explore_list 为空，则搜索失败，问题无解，否则循环求解
        while len(self.explore_list) > 0:
            self.searched_num += 1
            if self.searched_num % 1000 == 0:
                print(self.searched_num)

            # 取出 explore_list 的估价函数最小的节点，置为当前节点 current_state
            # 若 current_state 为目标节点，则搜索成功，计算解路径，退出
            self.current_state = self.explore_list[0]
            del(self.explore_list[0])
            if (self.current_state.state == self.end_state.state).all():
                self.getPath()
                break

            # 寻找所有与 current_state 邻接且未曾被发现的节点，插入到 explore_list 中
            # 并加入 visited_list 中，表示已发现
            next_list = self.current_state.nextStep()
            for next_state in next_list:
                if not self.isVisited(next_state):
                    self.explore_list.append(next_state)
                    self.visited_list.append(next_state)


class State:

    # int[][]:  self.state        当前状态的数码矩阵
    # string[]: self.direction    当前空块的可移动方向
    # State:    self.parent       当前状态的上一个状态
    # int:      self.f            当前状态的估价函数值
    # int:      self.d            当前状态的深度

    dist_state = None

    # 初始化一个状态
    def __init__(self, state, directionFlag=None, parent=None, f=0, d=0):
        self.state = state
        self.direction = ['up', 'down', 'right', 'left']
        if directionFlag:
            self.direction.remove(directionFlag)
        self.parent = parent
        self.f = f
        self.d = d

    # 获得当前状态下空快可移动的方向
    def getDirection(self):
        return self.direction

    # 设置状态的估价函数值
    def setF(self, f):
        self.f = f
        return

    # 打印一个状态的数码矩阵
    def showInfo(self):
        for i in range(len(self.state)):
            for j in range(len(self.state)):
                print(self.state[i, j], end=' ')
            print(" ")
        print('->')
        return

    # 获取0点（即空块在矩阵中的位置）
    def getZeroPos(self):
        postion = np.where(self.state == 0)
        return postion

    # 评估函数计算：目前的评估函数为当前状态与目标状态的哈夫曼距离
    def getFunctionValue(self):
        cur_node = self.state.copy()
        fin_node = self.dist_state.state.copy()
        dist = 0
        error = 0
        N = len(cur_node)
        for i in range(N):
            for j in range(N):
                if cur_node[i][j] != fin_node[i][j]:
                    index = np.argwhere(fin_node == cur_node[i][j])
                    x = index[0][0]  # 最终x距离
                    y = index[0][1]  # 最终y距离
                    dist += (abs(x - i) + abs(y - j))
                    error += 1

        return dist + self.d

    # 寻找当前状态的下一个可行状态集合
    def nextStep(self):
        if not self.direction:
            return []
        subStates = []
        boarder = len(self.state) - 1
        # 获取0点位置
        x, y = self.getZeroPos()
        # 向左
        if 'left' in self.direction and y > 0:
            s = self.state.copy()
            tmp = s[x, y - 1]
            s[x, y - 1] = s[x, y]
            s[x, y] = tmp
            news = State(s, directionFlag='right', parent=self,d=self.d+1)
            news.setF(news.getFunctionValue())
            subStates.append(news)
        # 向上
        if 'up' in self.direction and x > 0:
            # it can move to upper place
            s = self.state.copy()
            tmp = s[x - 1, y]
            s[x - 1, y] = s[x, y]
            s[x, y] = tmp
            news = State(s, directionFlag='down', parent=self,d=self.d+1)
            news.setF(news.getFunctionValue())
            subStates.append(news)
        # 向下
        if 'down' in self.direction and x < boarder:
            # it can move to down place
            s = self.state.copy()
            tmp = s[x + 1, y]
            s[x + 1, y] = s[x, y]
            s[x, y] = tmp
            news = State(s, directionFlag='up', parent=self,d=self.d+1)
            news.setF(news.getFunctionValue())
            subStates.append(news)
        # 向右
        if self.direction.count('right') and y < boarder:
            # it can move to right place
            s = self.state.copy()
            tmp = s[x, y + 1]
            s[x, y + 1] = s[x, y]
            s[x, y] = tmp
            news = State(s, directionFlag='left', parent=self,d=self.d+1)
            news.setF(news.getFunctionValue())
            subStates.append(news)
        # 所有状态
        return subStates


if __name__ == '__main__':

    begin = State(np.array([[1, 5, 2],
                            [7, 0, 4],
                            [6, 3, 8]]))
    end = State(np.array([[1, 2, 3],
                          [4, 5, 6],
                          [7, 8, 0]]))

    State.dist_state = end
    
    time_start = time.time()
    solution = Solution(begin, end)
    solution.AStarSolve()
    # solution.BFSSolve()
    time_end = time.time()

    if solution.path_list:
        i = 0
        for node in solution.path_list:
            i += 1
            print(str(i) + ": ")
            node.showInfo()
        print("Total search node is %d" % solution.searched_num)
        print("Total steps is %d" % (len(solution.path_list) - 1))
    print('Totally cost is', time_end - time_start, "s")
```

### 附录 2 - 优化代码 AStarSearchOptimized.py

> 注：State类与附录一：AStarSearch.py 中的State类一致，故在这里省略，主函数也省略

``` python
import numpy as np
from queue import PriorityQueue
import time

class Solution:

    # State:   self.begin_state   起始状态
    # State:   self.end_state     结束状态
    # State:   self.current_state 当前状态
    # int:     self.searched_num  搜索结点总数
    # State[]: self.explore_list  待检查状态链表
    # State[]: self.visited_list  已检查状态链表
    # State[]: self.path_list     搜索最优路径

    # 初始化A*搜索
    def __init__(self, begin_state, end_state):
        self.begin_state = begin_state
        self.end_state = end_state
        self.current_state = None
        self.searched_num = 0
        self.explore_list = PriorityQueue()
        self.visited_list = {}
        self.path_list = []

    # 返回 explore_list 中 估价函数最小的节点
    def getBestState(self):
        return self.explore_list.get() # 返回并删除

    # isVisited 返回 True 如果该状态已经存在于 visited_state 中
    def isVisited(self, next_state):
        if self.visited_list.get(next_state) == None:
            return False
        else:
            return True

    # getPath 获取最终解路径，保存在 path_list 中
    def getPath(self):
        temp_state = self.current_state
        self.path_list.append(self.end_state)

        while temp_state.parent and temp_state.parent != self.begin_state:
            self.path_list.append(temp_state.parent)
            temp_state = temp_state.parent

        self.path_list.append(self.begin_state)
        self.path_list.reverse()

    # AStarSolve 搜索
    def AStarSolve(self):

        # 将起始节点放入 explore_list 中
        self.explore_list.put(self.begin_state)
        self.visited_list[self.begin_state] = self.begin_state

        # 如果 explore_list 为空，则搜索失败，问题无解，否则循环求解
        while not self.explore_list.empty():
            self.searched_num += 1
            if self.searched_num % 1000 == 0:
                print(self.searched_num)

            # 取出 explore_list 的估价函数最小的节点，置为当前节点 current_state
            # 若 current_state 为目标节点，则搜索成功，计算解路径，退出

            self.current_state = self.getBestState()

            if (self.current_state.state == self.end_state.state).all():
                self.getPath()
                break

            # 寻找所有与 current_state 邻接且未曾被发现的节点，插入到explore_list中
            # 并加入 visited_list 中，表示已发现
            next_list = self.current_state.nextStep()
            for next_state in next_list:
                if not self.isVisited(next_state):
                    self.explore_list.put(next_state)
                    self.visited_list[next_state] = next_state
```
<center><h1>
    人工智能第二次实验报告
    </h1></center>

<center><h2>AStar求解迷宫寻路问题</h2></center>

| 课程：人工智能原理 | 年级专业：19级软件工程 |
| ------------------ | ---------------------- |
| 姓名：郑有为       | 学号：19335286         |

## 目录

[toc]

## 一、迷宫寻路问题

* 在一个布满障碍的有限空间中，玩家需要绕开阻碍寻找一条从起点到终点的最短路径。

* 迷宫问题有两种类型：有回路迷宫和无回路迷宫。

  * 对于无回路迷宫：无回路迷宫可以与一棵树对应，其中每个迷宫每一个分叉的路口对应到树中就是一个分叉节点，无回路迷宫可以使用深度搜索，广度搜索，启发式搜索的方法解决。

    对于无回路迷宫，只要不重复经过某个节点，就一定是最短路径。

  * 对于有回路迷宫：迷宫可能存在多条到达终点的最短路径，在启发式搜索中，由于算法维护一个 openList 和 closeList，可以避免搜索进入死循环。但如果启发函数设计的不好，搜索结果的最终路径不一定是最短的。

    **在下面的测试（5.1）中，我们可以看到源代码在有回路迷宫中，不一定能得到最短路径。**

## 二、A*搜索算法

### 2.1 基本思想

A\*搜索算法利用启发性信息来引导搜索，动态地确定搜索节点的排序，每次选择最优的节点往下搜索，可以高效地减少搜索范围，减少求解的问题的时间。

A\*算法用估价函数来衡量一个节点的优先度，优先度越小的节点越应该被优先访问。估价函数用如下公式表示：$f(n) = h(n) + d(n)$，$h(n)$是对于当前状态的估计值，例如曼哈顿距离，$d(h)$是已经付出的搜索代价，例如节点的深度。

A\*算法和A搜索算法的不同之处在于，A\*保证对于所有节点都有：$h(n) \le h^*(n)$，其中$h^*(n)$为当前状态到目的状态的最优路径的代价。

### 2.2 算法步骤

1. 将起始节点放入 openTable 中
2. 如果 openTable 为空，则搜索失败，问题无解，否则循环求解
   1. 取出 openTable 的估价函数最小的节点，置为当前节点 currentPoint，若 currentPoint 为目标节点，则搜索成功，计算解路径，退出
   2. 寻找所有与 currentPoint 邻接且未曾被发现的节点，插入到 openTable 中，并加入 closeTable 中，表示已发现

## 三、原程序说明

* 主要类：使用 Point 类来表示一个格子的位置和它的评估函数值，使用 State 类来表示当前迷宫的状态。
* 主要函数：
  * `nextStep(map, openTable, closeTable, wrongTable)`：用于确定下一步的路径，更新 openTable， closeTable 和 wrongTable。
  * `solve(map, openTable, closeTable, wrongTable)`：求解问题，循环调用 nextStep

* 思路说明：
  * 原程序除了使用 openTable 和 closeTable 存储待搜索的记录和已经访问过的的记录，还用一个 wrongTable 记录了下一步不能选择的位置。
  * 程序会每次在当前可行的几个方向里选取一个评估函数最小的作为下一步的路径，而不是从 openList 中选择最小的作下一步的路径，因此它无法获得全局最优性，也就无法求得最优解。
* 评估函数：曼哈顿距离 + 1，不考虑过去的路径长度，即不考虑已经付出的代价。
* 其他的问题：没有处理起点和终点·之间不连通的情况

## 四、程序修改

### 4.1 程序修改

* 保留 Point 类，增加以下内容：

  | 新增内容      | 注释                                                 |
  | ------------- | ---------------------------------------------------- |
  | `self.d`      | 深度，即起点到该点的路径的长度，用于表示已付出的代价 |
  | `self.parent` | 上一步的位置，用于记录路径，可以回溯到开始结点       |
  | `__le__`      | 比较两个点的评估函数值大小                           |
  | `__hash__`    | 将 Point 类定义为可哈希结构                          |

* Solution 类：和上一篇报告类似，使用一个类来处理搜索问题。以下是属性和方法：

  | 属性名       | 类型           | 注释                                           |
  | ------------ | -------------- | ---------------------------------------------- |
  | map          | 二维字符矩阵   | 记录迷宫地图（每一个元素1表示障碍，0表示可通） |
  | openTable    | Point 优先队列 | 记录全局的下一步可以走的点                     |
  | closeTable   | Point 字典     | 哈希结构，保存已访问的点                       |
  | bestPath     | Point 数组     | 保存最优路径                                   |
  | beginPoint   | Point类型      | 保存出发点位置                                 |
  | currentPoint | Point类型      | 保存当前点位置                                 |
  | destPoint    | Point类型      | 保存终点位置                                   |
  | serachCount  | int 类型       | 记录查询的总结点数                             |

  | 方法名                   | 注释                                                         |
  | ------------------------ | ------------------------------------------------------------ |
  | \__init__                | 初始化                                                       |
  | getBestPointInOpenList() | 获取 openTable 中估值函数最小的节点                          |
  | isVisited()              | 判断一个点是否被访问过，即是否位于 closeTable                |
  | getPath()                | 生成从起点到当前节点的位置                                   |
  | nextStep()               | 搜寻当前节点的下一步可行解点，加入到 openTable 和 closeTable 当中 |
  | AStarSolve()             | 求解迷宫问题                                                 |
  | showInfo()               | 生成迷宫最优解，最短路径用 `*` 表示，访问过但不是最短路径的点用 `C` 表示 |

### 4.2 复杂度分析

* 优先队列来实现 `openTable`，用一个哈希表（字典）来实现 `closeTable`，可以将每次获取估价函数最小的点和每次判断一个点是否已经被搜索过的复杂度都降为$O(1)$
* 而`openTable`插入节点并维护优先队列结构的复杂度为$O(\log(n))$

* 算法复杂度为$O(M\log(M))$，设$M$为迷宫非障碍的位置总数，但在启发式策略的基础上，实际搜索的节点远没有这么多。

## 五、测试结果

### 5.1 源程序测试

* **无回路情况**：原程序在无回路下的运行情况，对于输入：

  ```
  state = np.array([[0, 0, 0, 0, 0], 
                    [1, 0, 1, 0, 1], 
                    [0, 0, 0, 0, 1], 
                    [0, 1, 0, 0, 0], 
                    [0, 0, 0, 1, 0]])
  ```

  程序输出：搜索节点次数和最短路径长度都为 8。

  ```
  Best Way:
  *  *  *  *  0  
  1  1  1  *  1  
  0  0  0  *  1  
  0  1  0  *  *  
  0  0  0  1  *  
  
  Total search steps is 8
  Total steps is 8
  ```

* **有回路情况**：原程序不能保证最优解，例如以下输入：

  ```
  state = np.array([[0, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0],
                    [0, 0, 1, 1, 0],
                    [0, 1, 1, 0, 0],
                    [0, 0, 0, 0, 0]])
  ```

  程序输出是：**搜索节点次数和最短路径长度都为 10，但一条最优路径应该是：沿着最右的一条边向上走，再沿着最上面一条边往左走，共 8 步。**

  ```
  Best Way:
  *  *  0  0  0  
  1  *  0  0  0  
  *  *  1  1  0  
  *  1  1  0  0  
  *  *  *  *  *  
  
  Total search steps is 10
  Total steps is 10
  ```

### 5.2 修改程序测试

* 对于**无回路迷宫**：输入：

  ```python
  state = np.array([[0, 0, 0, 0, 0],
  			   	  [1, 0, 1, 0, 1],
  				  [0, 0, 1, 1, 1],
  				  [0, 1, 0, 0, 0],
  				  [0, 0, 0, 1, 0]])
  ```

  输出：共搜索了16个点，路径为12。矩阵中 C 表示搜索了但未被加入最短路径的点。

  ```
  Best Way:
  *  *  C  C  C  
  1  *  1  C  1  
  *  *  1  1  1  
  *  1  *  *  *  
  *  *  *  1  *  
  
  Total search steps is 16
  Total steps is 12
  ```

* 对于**有回路迷宫**：输入：

  ```python
  state = np.array([[0, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0],
                    [0, 0, 1, 1, 0],
                    [0, 1, 1, 0, 0],
                    [0, 0, 0, 0, 0]])
  ```

  输出：一共搜索了14个点，最短路径为 8，**可以找到最优解**。矩阵中 C 表示搜索了但未被加入最短路径的点。

  ```
  Best Way:
  *  *  C  C  C  
  1  *  *  *  *  
  C  C  1  1  *  
  0  1  1  C  *  
  0  0  0  0  *  
  
  Total search steps is 14
  Total steps is 8
  ```

### 5.3 20*20迷宫测试

* 输入：

  ```python
  state=np.array([
      [0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1],
      [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1],
      [0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1],
      [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1],
      [1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1],
      [0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1],
      [0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1],
      [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1],
      [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1],
      [0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
      [0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1],
      [0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1],
      [0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1],
      [1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      [0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
      [0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      [1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0],
      [0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0]])
  ```

* 输出：

| 修改程序求解结果：最短路径（42步）          | 原程序求解结果：非最短路径（50步）          |
| ------------------------------------------- | ------------------------------------------- |
| ![image-20211120202711695](image/5-3-1.png) | ![image-20211120195600252](image/5-3-2.png) |

## 附录

### 附录 1 - 修改程序 AStarMaze.py 

``` python
import numpy as np
from queue import PriorityQueue

class Point:

    def __init__(self, x, y, parent=None, d=0):
        self.x = x
        self.y = y
        self.f = 0
        self.d = d
        self.parent = parent

    def setF(self, f):
        self.f = f

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __lt__(self, other):
        return self.f < other.f

    def __hash__(self):
        return self.x * 1000 + self.y

    # 计算估价函数值： f = g + h, g = depth, h 为距离终点的曼哈顿距离
    def getFunctionValue(self, end):
        dist = abs(self.x - end.x) + abs(self.y - end.y)
        return dist + self.d

class Solution:

    # 初始化A*搜索
    def __init__(self, map, start_point, end_point):
        self.map = map
        self.openTable = PriorityQueue()
        self.closeTable = {}
        self.bestPath = []
        self.beginPoint = start_point
        self.destPoint = end_point
        self.currentPoint = None
        self.searchCount = 0

    # 获取 openTable 中估值函数最小的节点
    def getBestPointInOpenList(self):
        return self.openTable.get() # 返回并删除

    # 判断一个点是否被访问过，即是否位于 closeTable
    def isVisited(self, nextPoint):
        if self.closeTable.get(nextPoint) == None:
            return False
        else:
            return True

    # 生成从起点到当前节点的位置
    def getPath(self):
        tempPoint = self.currentPoint
        self.bestPath.append(self.destPoint)

        while tempPoint.parent and tempPoint.parent != self.beginPoint:
            self.bestPath.append(tempPoint.parent)
            tempPoint = tempPoint.parent

        self.bestPath.append(self.beginPoint)
        self.bestPath.reverse()

    # 搜寻当前节点的下一步可行解点，加入到 openTable 和 closeTable 当中
    def nextStep(self):

        nextPoints = []
        boarder = len(self.map) - 1
        x = self.currentPoint.x
        y = self.currentPoint.y
        d = self.currentPoint.d

        # 往左走
        if y > 0 and self.map[x][y - 1] == 0:
            nextPoints.append(Point(x, y - 1, self.currentPoint, d + 1))
        # 往上走
        if x > 0 and self.map[x - 1][y] == 0:
            nextPoints.append(Point(x - 1, y, self.currentPoint, d + 1))
        # 往下走
        if x < boarder and self.map[x + 1][y] == 0:
            nextPoints.append(Point(x + 1, y, self.currentPoint, d + 1))
        # 往右走
        if y < boarder and self.map[x][y + 1] == 0:
            nextPoints.append(Point(x, y + 1, self.currentPoint, d + 1))

        for nextPoint in nextPoints:
            if nextPoint not in self.closeTable:

                self.searchCount += 1
                if self.searchCount % 10 == 0:
                    print("Search point is up to " + str(self.searchCount))

                nextPoint.setF(nextPoint.getFunctionValue(self.destPoint))
                self.openTable.put(nextPoint)
                self.closeTable[nextPoint] = nextPoint

    # 求解迷宫问题
    def AStarSolve(self):

        self.openTable.put(self.beginPoint)
        self.closeTable[self.beginPoint] = self.beginPoint

        while not self.openTable.empty():

            self.currentPoint = self.getBestPointInOpenList()

            if(self.currentPoint == self.destPoint):
                self.getPath()
                break

            self.nextStep()

    # 展示最后结果，最短路径用 `*` 表示，访问过但不是最短路径的点用 `C` 表示
    def showInfo(self):
        for i in range(len(self.map)):
            for j in range(len(self.map)):
                if Point(i, j) in self.bestPath:
                    # 正确路径用‘*’表示
                    print('*', end='  ')
                elif Point(i,j) in self.closeTable:
                    # 搜寻过的结点用‘C’表示
                    print('C', end='  ')
                else:
                    print(self.map[i, j], end='  ')
            print("")
        return


if __name__ == '__main__':

    # state = np.array([[0, 0, 0, 0, 0],
    #                   [1, 0, 0, 0, 0],
    #                   [0, 0, 1, 1, 0],
    #                   [0, 1, 1, 0, 0],
    #                   [0, 0, 0, 0, 0]])

    # state = np.array([[0, 0, 0, 0, 0],
    #                   [1, 0, 1, 0, 1],
    #                   [0, 0, 1, 1, 1],
    #                   [0, 1, 0, 0, 0],
    #                   [0, 0, 0, 1, 0]])

    state=np.array([
        [0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1],
        [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1],
        [0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1],
        [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1],
        [1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1],
        [0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1],
        [0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1],
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1],
        [0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0],
        [0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1],
        [0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1],
        [0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1],
        [1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0],
        [0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0]])

    # 起点终点
    start_point = Point(0, 0)
    end_point = Point(len(state) - 1, len(state) - 1)

    # 最终路径
    solution = Solution(state, start_point, end_point)
    solution.AStarSolve()
    print('Best Way:')
    solution.showInfo()

    print("Total search steps is %d" % solution.searchCount)
    print("Total steps is %d" % (len(solution.bestPath) - 1))
```<center><h1>
    人工智能第三次实验报告
    </h1></center>

<center><h2>遗传算法求最值问题</h2></center>

| 课程：人工智能原理 | 年级专业：19级软件工程 |
| ------------------ | ---------------------- |
| 姓名：郑有为       | 学号：19335286         |

## 目录

[toc]

## 一、遗传算法

### 1.1 遗传算法简介

​		遗传算法是一种进化算法，基于自然选择和生物遗传等生物进化机制的一种搜索算法，其通过选择、重组和变异三种操作实现优化问题的求解。它的本质是从原问题的一组解出发改进到另一组较好的解，再从这组改进的解出发进一步改进。在搜索过程中，它利用结构和随机的信息，是满足目标的决策获得最大的生存可能，是一种概率型算法。

​		遗传算法主要借用生物中“适者生存”的原则，在遗传算法中，染色体对应的是数据或数组，通常由一维的串结构数据来表示。串上的各个位置对应一个基因座，而各个位置上所取的值对等位基因。遗传算法处理的是基因型个体，一定数量的个体组成了群体。群体的规模就是个体的数目。不同个体对环境的适应度不同，适应度打的个体被选择进行遗传操作产生新个体。每次选择两个染色体进行产生一组新染色体，染色体也可能发生变异，得到下一代群体。

### 1.2 遗传算法基本要素

1. **参数编码**：可以采用位串编码、实数编码、多参数级联编码等
2. **设定初始群体**：
   1. 启发 / 非启发给定一组解作为初始群体
   2. 确定初始群体的规模
3. **设定适应度函数**：将目标函数映射为适应度函数，可以进行尺度变换来保证非负、归一等特性
4. **设定遗传操作**：
   1. 选择：从当前群体选出一系列优良个体，让他们产生后代个体，一般采用蒙特卡洛法，即按适应度占比分配概率
   2. 交叉：两个个体的基因进行交叉重组来获得新个体
   3. 变异：随机变动个体串基因座上的某些基因
5. **设定控制参数**：例如变异概率、交叉程度、迭代上限等

### 1.3 遗传算法一般步骤

<img src="image/GA.png" alt="image-20211130103502395" style="zoom:70%;" />

## 二、程序说明

### 2.1 控制参数

以 ***ga_max.py*** 为例，默认参数如下：

| 变量           | 默认值 | 含义     |
| -------------- | ------ | -------- |
| **DNA_SIZE**   | 24     | 编码长度 |
| **POP_SIZE**   | 100    | 种群大小 |
| **CROSS_RATE** | 0.8    | 交叉率   |
| **MUTA_RATE**  | 0.15   | 编译率   |
| **Iterations** | 1000   | 迭代次数 |

### 2.2 编码规则

 ***ga_max.py*** 和  ***ga_min.py*** 采用一样的编码规则，由于一个解是一个二元组 ***(x,y)*** ，编码采用多参数级联编码，编码步骤如下：

1. 设一个 DNA 是一个长度为 ***l*** 的二进制码串，因为解是二元组，一个染色体长为 ***2l***；
2. 使用奇偶级联的方式级联两条 DNA，即染色体二进制串的奇数位是 ***x*** 的 DNA，偶数位是 ***y*** 的 DNA；
3. 解码时需要将 ***x*** 和 ***y*** 分别从染色体中取出，然后映射到解空间，解空间是 [0,10] X [0,10]，用 $2^l$ 均匀划分解空间来获得实际的 ***x*** 和 ***y***。

代码如下：

``` python
# 编码
# pop（二维矩阵） = 种群数 * (DNA长度 * 2) 个 0,1 随机数
pop = np.random.randint(2, size=(POP_SIZE, DNA_SIZE * 2))   

# 解码
# 奇数列表示 X：取 pop 的奇数位
# 偶数列表示 Y：取 pop 的偶数位
x_pop = pop[:,1::2]		                                                                       
y_pop = pop[:,::2] 		
# 二进制转十进制，在归一化塞入区间[0,10]中
x = x_pop.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(X_BOUND[1]-X_BOUND[0])+X_BOUND[0] 
y = y_pop.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(Y_BOUND[1]-Y_BOUND[0])+Y_BOUND[0]
```

### 2.3 选择初始群体

对于一个函数求最大值/最小值问题，一般启发式信息比较少，故程序采用完全随机生成来产生初始群体。

``` python
# 产生初始群体 pop
# pop（二维矩阵） = 种群数 * (DNA长度 * 2) 个 0,1 随机数
pop = np.random.randint(2, size=(POP_SIZE, DNA_SIZE * 2))
```

### 2.4 适应度函数

​		适应度函数给予待求解的问题函数，为了方便后续的选择操作，一般保证适应度函数为正， ***ga_max.py*** 和  ***ga_min.py*** 的适应度函数分别如下。

​		虽然实验分别给出了最大值和最小值的算法，但实际上没什么必要，因为在求一个问题的最小值，只需将问题表达式乘以 -1，再用最大值算法求解即可。

```python
# 最大值问题的适应度函数
def getfitness(pop): # 计算适应度函数                                    
	x,y = decodeDNA(pop)                                          
	temp = F(x, y)                                                
	return (temp - np.min(temp)) + 0.0001   # 减去最小的适应度是为了防止适应度出现负数 
```

```python
# 最小值问题的适应度函数
def getfitness(pop):
    x,y = decodeDNA(pop)
    temp = F(x, y)
    return -(temp - np.max(temp)) + 0.0001  # 减去最大的适应度是为了防止适应度出现负数
```

### 2.5 遗传操作

* **选择**：使用蒙特卡洛法，即个体被选择的概率为其适应度占群体总适应度的比例`(fitness)/(fitness.sum())`

  ``` python
  def select(pop, fitness):    # 根据适应度选择
  	temp = np.random.choice(np.arange(POP_SIZE), size=POP_SIZE, replace=True,p=(fitness)/(fitness.sum()))
  	return pop[temp]
  ```

* **交换**：以概率 CROSS_RATE 进行两点交叉（交换两个染色体两点间的片段）

  ```python
  temp = i  # 子代先得到父亲的全部基因
  if np.random.rand() < CROSS_RATE:  # 以交叉概率发生交叉
      j = pop[np.random.randint(POP_SIZE)]  # 从种群中随机选择另一个个体，并将该个体作为母代
      cpoints1 = np.random.randint(0, DNA_SIZE*2-1)  # 随机产生交叉的点
      cpoints2 = np.random.randint(cpoints1,DNA_SIZE*2)
      temp[cpoints1:cpoints2] = j[cpoints1:cpoints2]  # 子代得到位于交叉点后的母代的基因
  ```

* **变异**：以概率 MUTA_RATE 进行变异，变异行为具体为随机选取一个二进制位进行反转

  ```python
  def mutation(temp, MUTA_RATE):
  	if np.random.rand() < MUTA_RATE: 					# 以MUTA_RATE的概率进行变异
  		mutate_point = np.random.randint(0, DNA_SIZE)	# 随机产生一个实数，代表要变异基因的位置
  		temp[mutate_point] = temp[mutate_point]^1 		# 将变异点的二进制为反转
  ```

### 2.6 迭代过程

```python
for _ in range(Iterations):  		# 迭代 Iterations 代
    pop = np.array(crossmuta(pop, CROSS_RATE))	# 交换变异
    fitness = getfitness(pop)		# 计算适应度函数
    pop = select(pop, fitness)  # 选择生成新的种群
```



## 三、参数测试

​		下面以 ***ga_max.py*** 为例，通过调整参数，研究单一参数的变化对求解结果和求解耗时的影响，相关代码在附录 - 2，测试图表分别为修改不同参数下耗时、最优值、最右适应度的变化。

### 3.1 编码长度

* 编码长度测试范围：[6,30]，每一个长度重复测试 10 次来减小随机误差。
* 测试显示随着编码长度的增加，算法耗时和适应度有降低趋势，最优值变化较小。

![](image/DNA_SIZE.png)

### 3.2 种群大小

* 种群大小测试范围：[20,800]，每一个长度重复测试 3 次来减小随机误差。
* 测试显示随着编码长度的增加，算法耗时呈线性增加，在种群数目大于100时最优值和最右适应度比较稳定。

![](image/POP_SIZE.png)

### 3.3 交叉率

* 交叉率测试范围：[0,1]，每一个长度重复测试 10 次来减小随机误差。
* 测试显示随着编码长度的增加，算法耗时有上升趋势，而最优值和最有适应度变化不大。

![](image/CROSS_RATE.png)

### 3.4 变异率

* 变异率测试范围：[0,1]，每一个长度重复测试 10 次来减小随机误差。
* 测试显示随着编码长度的增加，算法耗时和最优值变化不大，而变异率越高最有适应度越高，在适应度大于0.4后趋于平缓。

![](image/MUTA_RATE.png)

### 3.5 迭代次数

* 迭代次数测试范围：[1,1000]，每一个长度重复测试 5 次来减小随机误差。
* 测试显示随着编码长度的增加，算法耗时有线性上升，而最优值和最右适应度有波动但总体平稳。

![](image/ITERATION.png)

## 四、算法改进

### 4.1 最佳个体保存

​		把群体中适应度最高的一个或多个个体不进行交叉和变异而直接复制到下一代，保证历代最优能够延续到下一代。只需对迭代部分做简单的修改即可以实现。（**附录 - 1：最佳个体保存优化**）

​		经过多次测试，我们发现使用最佳个体保存的选择策略一般能够得到更好的结果。分别对最佳个体保存和非优化进行 100 次测试，对比其求得的最优值。如下图，橙色三角为优化结果，蓝色圆圈为未优化结果。

​		**优化前后最优值主要分布在 78 到 81之间**，但优化后的效果更好。

![](image/OPT1.png)



### 4.2 双倍体遗传

* **基本思路**：双倍体遗传下，编码由显性基因和隐性基因组成，因此DNA长度翻倍。每次产生子代继承了两个个体的显性基因（显性遗传），为了避免收敛过快陷入局部最优解，提高了变异率（0.8），代码在源码的基础上修改，详见**附录 - 2：双倍体遗传**

* **测试结果**：可以看到 **100** 次测试**最优值全部都在 80.4 到 81.0 之间**，相比于非优化和最佳个体保存要更加稳定且准确。同时，双倍体遗传策略收敛速度更快。

![](image/OPT2.png)

---

## 附录

**代码地址：https://gitee.com/WondrousWisdomcard/ai-homework**

### 附录 1 - 最佳个体保存代码

```python
# 最佳个体保存优化
def Opt_1():
	start_t = datetime.datetime.now()
	pop = np.random.randint(2, size=(POP_SIZE, DNA_SIZE * 2))
	for _ in range(Iterations):
		pop = np.array(crossmuta(pop, CROSS_RATE))
		fitness = getfitness(pop)					
		best = pop[np.argmax(fitness)]
		pop = select(pop, fitness)  
		pop[0] = best
	end_t = datetime.datetime.now()
	print("\n最佳个体保存\n耗时: ",(end_t - start_t))
	print_info(pop)
	fitness = getfitness(pop)
	maxfitness = np.argmax(fitness)
	x, y = decodeDNA(pop)
	return F(x[maxfitness],y[maxfitness])

def OPT1_TEST():
	i_list = range(0, 100)
	f = []
	f_opt = []
	for i in i_list:
		f.append(NonOpt())
		f_opt.append(Opt_1())

	f.sort()
	f_opt.sort()

	plt.plot(i_list, f, marker='o', label="Non Optimized")
	plt.plot(i_list, f_opt, marker='^', label="Best Preserve")
	plt.gca().xaxis.set_major_locator(MultipleLocator(10))
	plt.legend()
	plt.show()
```

### 附录 2 - 双倍体遗传代码 `opt_2.py`

``` python
import numpy as np
from matplotlib.ticker import MultipleLocator
from numpy.ma import cos
import matplotlib.pyplot as plt

DNA_SIZE = 12  		# 编码长度
POP_SIZE = 100  	# 种群大小
CROSS_RATE = 0.8  	# 交叉率
MUTA_RATE = 0.8 	# 变异率
Iterations = 100  	# 代次数
X_BOUND = [0, 10]  	# X区间
Y_BOUND = [0, 10]  	# Y区间

def F(x, y):  # 问题函数
    return (6.452 * (x + 0.125 * y) * (cos(x) - cos(2 * y)) ** 2) / (
                0.8 + (x - 4.2) ** 2 + 2 * (y - 7) ** 2) + 3.226 * y

def decodeDNA(pop):  # 基因解码
    x1_pop = pop[:, 0::4]
    y1_pop = pop[:, 1::4]
    x2_pop = pop[:, 2::4]
    y2_pop = pop[:, 3::4]

    x1 = x1_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (X_BOUND[1] - X_BOUND[0]) + X_BOUND[0]
    y1 = y1_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (Y_BOUND[1] - Y_BOUND[0]) + Y_BOUND[0]
    x2 = x2_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (X_BOUND[1] - X_BOUND[0]) + X_BOUND[0]
    y2 = y2_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (Y_BOUND[1] - Y_BOUND[0]) + Y_BOUND[0]

    x = []
    y = []
    for i in range(POP_SIZE):
        if F(x1[i],y1[i]) > F(x2[i],y2[i]):
            x.append(x1[i])
            y.append(y1[i])
        else:
            x.append(x2[i])
            y.append(y2[i])
    return x, y

def getfitness(pop):  # 计算适应度函数
    x, y = decodeDNA(pop)
    temp = []
    for i in range(POP_SIZE):
        temp.append(F(x[i], y[i]))
    return (temp - np.min(temp)) + 0.0001  # 减去最小的适应度是为了防止适应度出现负数

def select(pop, fitness):  # 根据适应度选择（蒙特卡罗）
    temp = np.random.choice(np.arange(POP_SIZE), size=POP_SIZE, replace=True, p=(fitness) / (fitness.sum()))
    return pop[temp]

def merge(i, j):
    temp = []

    i_x1_pop, i_y1_pop = i[0::4], i[1::4]
    i_x2_pop, i_y2_pop = i[2::4], i[3::4]
    j_x1_pop, j_y1_pop = j[0::4], j[1::4]
    j_x2_pop, j_y2_pop = j[2::4], j[3::4]

    i_x1 = i_x1_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (X_BOUND[1] - X_BOUND[0]) + X_BOUND[0]
    i_y1 = i_y1_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (Y_BOUND[1] - Y_BOUND[0]) + Y_BOUND[0]
    i_x2 = i_x2_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (X_BOUND[1] - X_BOUND[0]) + X_BOUND[0]
    i_y2 = i_y2_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (Y_BOUND[1] - Y_BOUND[0]) + Y_BOUND[0]

    j_x1 = j_x1_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (X_BOUND[1] - X_BOUND[0]) + X_BOUND[0]
    j_y1 = j_y1_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (Y_BOUND[1] - Y_BOUND[0]) + Y_BOUND[0]
    j_x2 = j_x2_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (X_BOUND[1] - X_BOUND[0]) + X_BOUND[0]
    j_y2 = j_y2_pop.dot(2 ** np.arange(DNA_SIZE)[::-1]) / float(2 ** DNA_SIZE - 1) * (Y_BOUND[1] - Y_BOUND[0]) + Y_BOUND[0]

    if F(i_x1, i_y1) > F(i_x2, i_y2):
        i_x_pop = i_x1_pop
        i_y_pop = i_y1_pop
    else:
        i_x_pop = i_x2_pop
        i_y_pop = i_y2_pop

    if F(j_x1, j_y1) > F(j_x2, j_y2):
        j_x_pop = j_x1_pop
        j_y_pop = j_y1_pop
    else:
        j_x_pop = j_x2_pop
        j_y_pop = j_y2_pop

    for i in range(DNA_SIZE):
        temp.append(i_x_pop[i])
        temp.append(i_y_pop[i])
        temp.append(j_x_pop[i])
        temp.append(j_y_pop[i])

    return temp

def crossmuta(pop, CROSS_RATE):  # 种群的交叉变异操作
    new_pop = []
    for i in pop:  # 遍历种群中的每一个个体，将该个体作为父代
        j = pop[np.random.randint(POP_SIZE)]  # 从种群中随机选择另一个个体，并将该个体作为母代
        temp = merge(i, j)                    # 两个个体的显性基因相结合成新个体
        if np.random.rand() < CROSS_RATE:  # 以交叉概率发生交叉
            cpoints1 = np.random.randint(0, DNA_SIZE * 4 - 1)  # 随机产生交叉的两个点（区间：[cpoints1, cpoints2]）
            cpoints2 = np.random.randint(cpoints1, DNA_SIZE * 4)
            temp[cpoints1:cpoints2] = j[cpoints1:cpoints2]  # 子代得到位于交叉点后的母代的基因

        mutation(temp, MUTA_RATE)  # 每一个后代以变异率发生变异
        new_pop.append(temp)
    return new_pop

def mutation(temp, MUTA_RATE):
    if np.random.rand() < MUTA_RATE:  # 以MUTA_RATE的概率进行变异
        mutate_point = np.random.randint(0, DNA_SIZE * 4)  # 随机产生一个实数，代表要变异基因的位置
        temp[mutate_point] = temp[mutate_point] ^ 1  # 将变异点的二进制为反转

def OPT2_TEST():
    i_list = range(100)
    best_fitness = []
    best_f = []
    for i in i_list:
        print(i)
        pop = np.random.randint(2, size=(POP_SIZE, DNA_SIZE * 4))  # pop（二维矩阵） = (种群数) * (DNA长度 * 4) 个 0,1 随机数
        for _ in range(Iterations):  # 迭代 N 代
            pop = np.array(crossmuta(pop, CROSS_RATE))  # 对种群进行交叉（cross）和变异（muta）
            fitness = getfitness(pop)  # 计算种群每一个基因的适应度函数
            pop = select(pop, fitness)  # 选择生成新的种群

        fitness = getfitness(pop)
        maxfitness = np.argmax(fitness)
        x, y = decodeDNA(pop)
        best_fitness.append(fitness[maxfitness])
        best_f.append(F(x[maxfitness], y[maxfitness]))

    best_f.sort()
    plt.plot(i_list, best_f, marker='o', label="F_max(x,y)")
    plt.gca().xaxis.set_major_locator(MultipleLocator(10))
    plt.legend()
    plt.show()

if __name__ == "__main__":

    OPT2_TEST()
```



<center><h1>
    人工智能第五次实验报告
    </h1></center>
<center><h2>决策树模型</h2></center>

| 课程：人工智能原理 | 年级专业：19级软件工程 |
| ------------------ | ---------------------- |
| 姓名：郑有为       | 学号：19335286         |

## 目录

[toc]

## 一、问题背景

### 1.1 监督学习简介

​		机器学习的形式包括无监督学习，强化学习，监督学习和半监督学习；学习任务有分类、聚类和回归等。

​		监督学习通过观察“输入—输出”对，学习从输入到输出的映射函数。分类监督学习的训练集为标记数据，每一条数据有对应的”标签“，根据标签可以将数据集分为若干个类别。分类监督学习经训练集生成一个学习模型，可以用来预测一条新数据的标签。

​		常见的监督学习模型有决策树、KNN算法、朴素贝叶斯和随机森林等。

### 1.2 决策树简介

决策树归纳是一类简单的机器学习形式，它表示为一个函数，以属性值向量作为输入，返回一个决策。

* **决策树的组成**

  * 决策树由内节点上的属性值测试、分支上的属性值和叶子节点上的输出值组成。

    <img src="image/mushroom5000.png" style="zoom:67%;" />

* **决策树的学习算法**

  ```
  函数: dt(dataset, par_dataset, attrs)
  输入: 子数据集 dataset, 父数据集 par_dataset, 属性列表 attrs
  输出: 决策树
  
  if dataset 为空
  	return 父数据集 par_dataset 概率最大的标签
  else if atrs 为空
  	return 子数据集 dataset 概率最大的标签
  else if 子数据集 dataset 的标签全部相同
  	return 子数据集一致的标签
  else
  	best_attr <- attrs 在 dataset 中信息收益最高的属性
  	tree <- 值为 best_attr 的节点
  	for best_attr 的所有可选取值 best_attr_value
  		sub_dataset <- dataset中所有属性best_arr的值为best_attr_value的数据构成的子数据集
  		sub_tree <- dt(sub_dataset, dataset, attrs - best_attr)
  		添加一条从 tree 指向 sub_tree 的边，边的值为 best_attr_value
  	return tree
  ```

* **属性的优先程度判准 - 信息收益**

  使用信息熵来量化当前状态信息的不确定程度，对我们来说，信息熵越小，信息量就越大，也就越重要。熵的的定义如下：
  $$
  H(V) = - \sum_{k} P(v_k) \log_2 P(v_k)
  $$
  设有 $d$ 个不同值的属性 $A$ 将训练集划分为 $d$ 个子集 $E_k$，使用属性 $A$ 对数据集进行划分所得到的信息收益为：

  $$
  G(A) = H(E) - \sum_{k=1}^{d} \frac{|E_k|}{|E|}H(E_k)
  $$
  这里的信息收益也就是使用属性A划分带来熵的期望减少值。

* **决策树算法的改进**
  * **增加信息增益的最小阈值**：如果通过属性 $A$ 划分带来的信息增益小于阈值 $\epsilon$，则不再继续划分，而是生成叶子节点，节点的标签为当前数据集概率最大的标签，这种改进可以减小决策树的规模，避免过度拟合，缩短决策时间。
  *  **$\chi^2$剪枝**：早期终止可能会组织我们发现更好的属性组合，在生成决策树后进行剪枝，即自底向上移除决策树中划分效果不好的节点，替换为叶子节点。$\chi^2$剪枝通过量化数据的偏离程度（带$v-1$个自由度的卡方分布，$v$为样例总数），来判断是否剪枝。剪枝也能减小决策树的规模，避免过度拟合，缩短决策时间。

* **(类ID3) 决策树的适用范围**

  上述给出的决策树基于信息熵的度量，根据属性值来划分节点，当属性值不是离散的选项，如布尔值，而是浮点类型时，需要对数值进行划分，否则会生成非常多的分支节点，不能达到很好的效果。故上述算法要求属性值离散或经过预先分组，构建出的决策树也称为离散决策树。

  * **常见的决策树算法**

    常见的决策树算法除了有基于信息收益的ID3算法，还有基于信息增益比的C4.5算法和基于基尼指数的CART算法。

    **C4.5算法**与ID3算法基本一致，只是将ID3算法的信息收益换成了信息增益比：
    $$
    GR(D,A) = \frac{G(A)}{H(D)}
    $$
    其中 A 为属性， D 为训练集。

    **CART算法**可以处理非离散的属性值，每次划分将训练集根据某个特征 $A$ 的一个可能值 $a_m$ 分割为两个部分（$a < a_m$和$a >= a_m$），在所有可能的特征 $A$ 以及他们所有可能的切分点 $a_m$ 中，选择基尼指数最小的特征及其对应可能的切分点作为最有特征与最优切分点，以此来构建出一棵二叉决策树。

* **决策树的优缺点**：

  * 优点：分类快，具有可读性，易于理解。
  * 缺点：可能会出现过度拟合的问题，并非适用于所有分类场景。

## 二、程序说明

### 2.1 数据载入

数据集被统一格式化为一个类，它包含四个属性： 

* `feature_names`：属性名列表
* `target_names`：标签(分类)名
* `data`：属性数据矩阵, 每行是一个数据, 每个数据是每个属性的对应值的列表
* `target`：目标分类值列表

类`load_car`和`loca_mushroom`分别从文件中导入汽车数据集和蘑菇数据集，类`new_dataset`用于快速生成一个满足格式的数据集，使用方法如下：

### 2.2 功能函数

* **`get_h(target)`** 计算并返回信息熵

  * 参数：`target` 给定目标分类值列表

* **`get_subset(dataset, feature_name, feature_value)`** 筛选并返回子数据集

  * 参数：`dataset` 待分析数据集；`feature_name` 属性名字符串；`feature_value`属性值
  * 选择条件：原数据集中的属性 `feature_name` 值是否等于 `feature_value`

  * 备注：选择后会从数据子集中删去 `feature_name` 属性对应的一列

* **`best_spilt(dataset)`** 寻找并返回信息收益最大的属性划分，返回最佳属性
  * 参数：`dataset` 待分析数据集
* **`vote_most(dataset)`** 返回数据集中一个数据概率上最可能的标签
  * 参数：`dataset` 待分析数据集
* **`accuracy_rate(predict_result, target_result)`** 返回测试的正确率
  * 参数：`predict_result`：预测标签列表，`target_result`：实际标签列表

### 2.3 决策树模型

* **决策树节点 `dt_node`** 一个节点有以下属性：

  | 属性名           | 注释                                                 |
  | ---------------- | ---------------------------------------------------- |
  | **id**           | 为节点赋予一个全局ID, 目的是方便画图                 |
  | **feature_name** | 非叶子节点的属性名，若节点为叶子结点，则为 None      |
  | **target_value** | 叶子节点的标签，若节点为非叶子节点，则为 None        |
  | **vote_most**    | 非叶子节点最可能的标签，若节点为叶子结点，则为 None  |
  | **parent**       | 父亲节点                                             |
  | **child**        | 儿子节点，以当前节点的属性对应的属性值作为键值的字典 |

  **初始化：`dt_node(self, content, is_leaf=False, parent=None)`**

  | 参数名      | 注释                                                     |
  | ----------- | -------------------------------------------------------- |
  | **content** | 节点的内容，对于叶子节点为标签值，对于非叶子节点为属性名 |
  | **is_leaf** | 节点是否为叶子节点，默认为 False                         |
  | **parent**  | 指定节点的父节点，默认为 None                            |

* **决策树模型 `dt_tree`**

  | 属性名        | 注释                                   |
  | ------------- | -------------------------------------- |
  | **tree**      | 决策树的根节点                         |
  | **map_str**   | pydotplus 格式的代码串，用于做图       |
  | **color_dir** | 叶子节点可选颜色, 以标签值为键值的字典 |

  | 方法名                                 | 注释                                                        |
  | -------------------------------------- | ----------------------------------------------------------- |
  | **`fit(self, train_set)`**             | **训练**：根据提供的训练集生成决策树                        |
  | **`predict(self, test_set)`**          | **预测**：对测试集的数据进行预测，返回预测结果数组          |
  | **`show_tree(self, path="demo.png")`** | **可视化**：基于绘图工具 pydotplus 生成图片，保存在 path 中 |

### 2.4 决策树可视化

基于绘图工具 pydotplus ，生成绘图代码

* **初始化代码串**：

  ```python
  self.map_str = """
  digraph demo{
  node [shape=box, style="rounded", color="black", fontname="Microsoft YaHei"];
  edge [fontname="Microsoft YaHei"];
  """
  ```

* **创建叶子节点**：

  ```python
  node_content = "标签：" + str(node.target_value)
  self.map_str += "id" + str(node.id) + "[label=\"" + node_content + "\", fillcolor=\"" + self.color_dir[node.target_value] + "\", style=filled]\n"
  ```

* **创建非叶子节点**：

  ``` python
  node_content = "属性：" + node.feature_name
  self.map_str += "id" + str(node.id) + "[label=\"" + node_content + "\", fillcolor=\"#AADDFF\", style=filled]\n"
  ```

* **创建边**：从节点 `node` 指向一个 子节点 `node.child[feature_value]`

  ``` python
  self.map_str += "id" + str(node.id) + " -> " + "id" + str(node.child[feature_value].id) + "[label=\"" + str(feature_value) + "\"]\n"
  ```

* 生成的代码举例（部分代码）：

  ```
  digraph demo{
  node [shape=box, style="rounded", color="black", fontname="Microsoft YaHei"];
  edge [fontname="Microsoft YaHei"];
  id0[label="属性：safety", fillcolor="#AADDFF", style=filled]
  id1[label="标签：0", fillcolor="#AAFFDD", style=filled]
  id0 -> id1[label="low"]
  id2[label="属性：persons", fillcolor="#AADDFF", style=filled]
  id3[label="标签：0", fillcolor="#AAFFDD", style=filled]
  id2 -> id3[label="2"]}

## 三、程序测试

### 3.1 数据集说明

* **汽车数据 `load_car()`** ：汽车评价数据库是由一个简单的层次决策模型派生而来，该模型最初是为DEX （M. Bohanec, V. Rajkovic: Expert system for decision making. Sistemica 1(1), pp. 145-157, 1990.）模型根据以下概念结构评估汽车的可接受性。

  **属性**：如下表所示

  | 属性         | 属性值                 | 注释         |
  | ------------ | ---------------------- | ------------ |
  | **buying**   | v-high, high, med, low | 购买价格     |
  | **maint**    | v-high, high, med, low | 维护花销     |
  | **doors**    | 2, 3, 4, 5-more        | 门的数量     |
  | **persons**  | 2, 4, more             | 承载人数     |
  | **lug_boot** | small, med, big        | 后备箱的大小 |
  | **safety**   | low, med, high         | 安全性       |

  **标签**：0 - 不可接受， 1 - 可接受

  **数据总数**：1728条

* **蘑菇数据 `load_mushroom()`** ：这个数据集包括了蘑菇样本的描述，每一种都被确定为绝对可食用；绝对有毒；或未知可食用，不推荐。后一类是与有毒的一类结合起来的。

  **属性**：共有22项，依次是 "cap-shape", "cap-surface", "cap-color", "bruises", "odor", "gill-attachment", "gill-spacing", "gill-size", "gill-color", "stalk-shape", "stalk-root", "stalk-surface-above-ring", "stalk-surface-below-ring", "stalk-color-above-ring", "stalk-color-below-ring", "veil-type", "veil-color", "ring-number", "ring-type", "spore-print-color", "population", "habitat"。

  **标签**：e - 可食用（4208项）， p - 有毒（3916项）

  **数据总数**： 8124条

  **数据来源**： https://archive.ics.uci.edu/ml/datasets/Mushroom

### 3.2 决策树生成和测试

* **汽车模型**

​		当**训练规模为500时所生成的决策树**如下图所示。由于每一个属性都有3-5个可选值，故决策树看起来比较扁。

​		在图中，蓝色的节点为属性节点，绿色和紫色的节点为叶子节点，绿色的节点标签值为0，也就是不购买该汽车，蓝色节点标签值为1，表示购买该汽车，每条从一个节点指向其子节点的边上都有一个值，也就是该节点对应的属性的属性值。

​		对于该决策树，用剩下的数据集作为测试集进行测试，**准确度为：0.9307253463732681**。

![](image/car500.png)

​		当**训练规模为1000时所生成的决策树**如下图所示，比较上下两图可以看到随着测试规模的增大，决策树的规模也变得更大，但决策树的高度没有变化，只是叶子结点的数目有所增加。

​		对于该决策树，用剩下的数据集作为测试集进行测试，**准确度为：0.9559834938101788**。

![](image/car1000.png)



* **蘑菇模型**

​		虽然蘑菇模型的属性非常多，数据规模也远大于汽车，但其训练得到的决策树模型就很简单。

​		下图是**训练数据规模为5000时的决策树**，该树的高度只有5，也就意味着最多考虑4个属性（odor, spore-print-color, habitat, population）就可以很好的推断出一中蘑菇是否有毒。绿色和紫色的节点表示叶子节点，标签为 e 代表此种蘑菇可食用，标签为 p 代表此种蘑菇有毒。

​		对于该决策树，用剩下的数据集作为测试集进行测试，**准确度为：0.9859109830291386**

![](image/mushroom5000.png)

​		下图是当**训练规模增加到8000时的决策树**，只比上图稍微复杂了一些，但高度和考虑的属性都没有改变。

​		对于该决策树，用剩下的数据集作为测试集进行测试，**准确度为：1.0**

![](image/mushroom8000.png)

### 3.3 学习曲线评估算法精度

将所有的数据划分为训练集和测试集，用训练集学习生成决策树，再对测试集进行预测，分析预测的准确率。

调用方法 `incremental_train_scale_test(dataset, label, interval=1)` 来生成学习曲线，其中：dataset 为数据练集, label 为数据名称, interval 为测试规模递增的间隔。

* **汽车模型**

​		首先从规模为5的训练集开始学习，按照1的频率逐步提高训练规模，直到1729。如下图，可以看到随着训练集规模的逐步递增，精度也在不断升高。

![](image/car.png)

* **蘑菇模型**

​		首先从规模为5的训练集开始学习，按照25的频率逐步提高训练规模，直到8124。如下图，可以看到随着训练集规模的逐步递增，精度也在不断升高，在训练集规模大于7000时，测试的准确率已经达到了100%。

![](image/mushroom.png)

## 四、实验总结

通过本次实验，我们进一步监督学习的基本知识，重点理解决策树的常见算法和改进策略，掌握决策树的基本实现方法，考虑决策树的实现细节，实现了基本的决策树模型并使用汽车模型和蘑菇模型对模型进行测试和可视化，测试效果较好。

## 附录 - 程序代码

**电子版报告和代码地址：https://gitee.com/WondrousWisdomcard/ai-homework**

``` python
import numpy as np
from matplotlib import pyplot as plt
from math import log
import pandas as pd
import pydotplus as pdp

"""
19335286 郑有为
人工智能作业 - 实现ID3决策树
"""

nonce = 0  # 用来给节点一个全局ID
color_i = 0
# 绘图时节点可选的颜色, 非叶子节点是蓝色的, 叶子节点根据分类被赋予不同的颜色
color_set = ["#AAFFDD", "#DDAAFF", "#DDFFAA", "#FFAADD", "#FFDDAA"]

# 载入汽车数据, 判断顾客要不要买
class load_car:
    # 在表格中,最后一列是分类结果
    # feature_names: 属性名列表
    # target_names: 标签(分类)名
    # data: 属性数据矩阵, 每行是一个数据, 每个数据是每个属性的对应值的列表
    # target: 目标分类值列表
    def __init__(self):
        df = pd.read_csv('../dataset/car/car_train.csv')
        labels = df.columns.values
        data_array = np.array(df[1:])
        self.feature_names = labels[0:-1]
        self.target_names = labels[-1]
        self.data = data_array[0:,0:-1]
        self.target = data_array[0:,-1]

# 载入蘑菇数据, 鉴别蘑菇是否有毒
class load_mushroom:
    # 在表格中, 第一列是分类结果: e 可食用; p 有毒.
    # feature_names: 属性名列表
    # target_names: 标签(分类)名
    # data: 属性数据矩阵, 每行是一个数据, 每个数据是每个属性的对应值的列表
    # target: 目标分类值列表
    def __init__(self):
        df = pd.read_csv('../dataset/mushroom/agaricus-lepiota.data')
        data_array = np.array(df)
        labels = ["edible/poisonous", "cap-shape", "cap-surface", "cap-color", "bruises", "odor", "gill-attachment",
                  "gill-spacing", "gill-size", "gill-color", "stalk-shape", "stalk-root", "stalk-surface-above-ring",
                  "stalk-surface-below-ring", "stalk-color-above-ring", "stalk-color-below-ring",
                  "veil-type", "veil-color", "ring-number", "ring-type", "spore-print-color", "population", "habitat"]
        self.feature_names = labels[1:]
        self.target_names = labels[0]
        self.data = data_array[0:,1:]
        self.target = data_array[0:,0]

# 创建一个临时的子数据集, 在划分测试集和训练集时使用
class new_dataset:
    # feature_names: 属性名列表
    # target_names: 标签(分类)名
    # data: 属性数据矩阵, 每行是一个数据, 每个数据是每个属性的对应值的列表
    # target: 目标分类值列表
    def __init__(self, f_n, t_n, d, t):
        self.feature_names = f_n
        self.target_names = t_n
        self.data = d
        self.target = t

# 计算熵, 熵的数学公式为: $H(V) = - \sum_{k} P(v_k) \log_2 P(v_k)$
#        其中 P(v_k) 是随机变量 V 具有值 V_k 的概率
# target: 分类结果的列表, return: 信息熵
def get_h(target):
    target_count = {}
    for i in range(len(target)):
        label = target[i]
        if label not in target_count.keys():
            target_count[label] = 1.0
        else:
            target_count[label] += 1.0
    h = 0.0
    for k in target_count:
        p = target_count[k] / len(target)
        h -= p * log(p, 2)
    return h

# 取数据子集, 选择条件是原数据集中的属性 feature_name 值是否等于 feature_value
# 注: 选择后会从数据子集中删去 feature_name 属性对应的一列
def get_subset(dataset, feature_name, feature_value):
    sub_data = []
    sub_target = []
    f_index = -1
    for i in range(len(dataset.feature_names)):
        if dataset.feature_names[i] == feature_name:
            f_index = i
            break

    for i in range(len(dataset.data)):
        if dataset.data[i][f_index] == feature_value:
            l = list(dataset.data[i][:f_index])
            l.extend(dataset.data[i][f_index+1:])
            sub_data.append(l)
            sub_target.append(dataset.target[i])

    sub_feature_names = list(dataset.feature_names[:f_index])
    sub_feature_names.extend(dataset.feature_names[f_index+1:])
    return new_dataset(sub_feature_names, dataset.target_names, sub_data, sub_target)

# 寻找并返回信息收益最大的属性划分
# 信息收益值划分该数据集前后的熵减
# 计算公式为: Gain(A) = get_h(ori_target) - sum(|sub_target| / |ori_target| * get_h(sub_target))$
def best_spilt(dataset):

    base_h = get_h(dataset.target)
    best_gain = 0.0
    best_feature = None
    for i in range(len(dataset.feature_names)):
        feature_range = []
        for j in range(len(dataset.data)):
            if dataset.data[j][i] not in feature_range:
                feature_range.append(dataset.data[j][i])

        spilt_h = 0.0
        for feature_value in feature_range:
            subset = get_subset(dataset, dataset.feature_names[i], feature_value)
            spilt_h += len(subset.target) / len(dataset.target) * get_h(subset.target)

        if best_gain <= base_h - spilt_h:
            best_gain = base_h - spilt_h
            best_feature = dataset.feature_names[i]

    return best_feature

# 返回数据集中一个数据最可能的标签
def vote_most(dataset):
    target_range = {}
    best_target = None
    best_vote = 0

    for t in dataset.target:
        if t not in target_range.keys():
            target_range[t] = 1
        else:
            target_range[t] += 1

    for t in target_range.keys():
        if target_range[t] > best_vote:
            best_vote = target_range[t]
            best_target = t

    return best_target

# 返回测试的正确率
# predict_result: 预测标签列表, target_result: 实际标签列表
def accuracy_rate(predict_result, target_result):
    # print("Predict Result: ", predict_result)
    # print("Target Result:  ", target_result)
    accuracy_score = 0
    for i in range(len(predict_result)):
        if predict_result[i] == target_result[i]:
            accuracy_score += 1
    return accuracy_score / len(predict_result)

# 决策树的节点结构
class dt_node:

    def __init__(self, content, is_leaf=False, parent=None):
        global nonce
        self.id = nonce # 为节点赋予一个全局ID, 目的是方便画图
        nonce += 1
        self.feature_name = None
        self.target_value = None
        self.vote_most = None # 记录当前节点最可能的标签
        if not is_leaf:
            self.feature_name = content # 非叶子节点的属性名
        else:
            self.target_value = content # 叶子节点的标签

        self.parent = parent
        self.child = {} # 以当前节点的属性对应的属性值作为键值

# 决策树模型
class dt_tree:

    def __init__(self):
        self.tree = None # 决策树的根节点
        self.map_str = """
            digraph demo{
            node [shape=box, style="rounded", color="black", fontname="Microsoft YaHei"];
            edge [fontname="Microsoft YaHei"];
            """ # 用于作图: pydotplus 格式的树图生成代码结构
        self.color_dir = {} # 用于作图: 叶子节点可选颜色, 以标签值为键值

    # 训练模型, train_set: 训练集
    def fit(self, train_set):

        if len(train_set.target) <= 0:  # 如果测试集数据为空, 则返回空节点, 结束递归
            return None

        target_all_same = True
        for i in train_set.target:
            if i != train_set.target[0]:
                target_all_same = False
                break

        if target_all_same:  # 如果测试集数据中所有数据的标签相同, 则构造叶子节点, 结束递归
            node = dt_node(train_set.target[0], is_leaf=True)
            if self.tree == None:  # 如果根节点为空,则让该节点成为根节点
                self.tree = node

            # 用于作图, 更新 map_str 内容, 为树图增加一个内容为标签值的叶子节点
            node_content = "标签：" + str(node.target_value)
            self.map_str += "id" + str(node.id) + "[label=\"" + node_content + "\", fillcolor=\"" + self.color_dir[node.target_value] + "\", style=filled]\n"

            return node
        elif len(train_set.feature_names) == 0:  # 如果测试集待考虑属性为空, 则构造叶子节点, 结束递归
            node = dt_node(vote_most(train_set), is_leaf=True)  # 这里让叶子结点的标签为概率上最可能的标签
            if self.tree == None:  # 如果根节点为空,则让该节点成为根节点
                self.color_dir[vote_most(train_set)] = color_set[0]
                self.tree = node

            # 用于作图, 更新 map_str 内容, 为树图增加一个内容为标签值的叶子节点
            node_content = "标签：" + str(node.target_value)
            self.map_str += "id" + str(node.id) + "[label=\"" + node_content + "\", fillcolor=\"" + self.color_dir[node.target_value] + "\", style=filled]\n"

            return node
        else: # 普通情况, 构建一个内容为属性的非叶子节点
            best_feature = best_spilt(train_set) # 寻找最优划分属性, 作为该结点的值
            best_feature_index = -1
            for i in range(len(train_set.feature_names)):
                if train_set.feature_names[i] == best_feature:
                    best_feature_index = i
                    break

            node = dt_node(best_feature)
            node.vote_most = vote_most(train_set)
            if self.tree == None: # 如果根节点为空,则让该节点成为根节点
                self.tree = node
                # 用于作图, 初始化叶子节点可选颜色
                for i in range(len(train_set.target)):
                    if train_set.target[i] not in self.color_dir:
                        global color_i
                        self.color_dir[train_set.target[i]] = color_set[color_i]
                        color_i += 1
                        color_i %= len(color_set)

            feature_range = [] # 获取该属性出现在数据集中的可选属性值
            for t in train_set.data:
                if t[best_feature_index] not in feature_range:
                    feature_range.append(t[best_feature_index])

            # 用于做图, 创建一个内容为属性的非叶子节点
            node_content = "属性：" + node.feature_name
            self.map_str += "id" + str(node.id) + "[label=\"" + node_content + "\", fillcolor=\"#AADDFF\", style=filled]\n"

            for feature_value in feature_range:
                subset = get_subset(train_set, best_feature, feature_value)  # 获取每一个子集
                node.child[feature_value] = self.fit(subset)  # 递归调用 fit 函数生成子节点
                if node.child[feature_value] == None:
                    # 如果创建的子节点为空, 则创建一个叶子节点作为其子节点, 其中标签值为概率上最可能的标签
                    node.child[feature_value] = dt_node(vote_most(train_set), is_leaf=True)
                node.child[feature_value].parent = node

                # 用于做图, 创建当前节点到所有子节点的连线
                self.map_str += "id" + str(node.id) + " -> " + "id" + str(node.child[feature_value].id) + "[label=\"" + str(feature_value) + "\"]\n"

            # print("Rest Festure: ", train_set.feature_names)
            # print("Best Feature: ", best_feature_index, best_feature, "Feature Range: ", feature_range)
            # for feature_value in feature_range:
            #     print("Child[", feature_value, "]: ", node.child[feature_value].feature_name, node.child[feature_value].target_value)
            return node

    # 测试模型, 对测试集 test_set 进行预测
    def predict(self, test_set):
        test_result = []
        for test in test_set.data:
            node = self.tree # 从根节点一只往下找, 知道到达叶子节点
            while node.target_value == None:
                feature_name_index = -1
                for i in range(len(test_set.feature_names)):
                    if test_set.feature_names[i] == node.feature_name:
                        feature_name_index = i
                        break
                if test[feature_name_index] not in node.child.keys():
                    break
                else:
                    node = node.child[test[feature_name_index]]

            if node.target_value == None:
                test_result.append(node.vote_most)
            else: # 如果没有到达叶子节点, 则取最后到达节点概率上最可能的标签为目标值
                test_result.append(node.target_value)

        return test_result

    # 输出树, 生成图片, path: 图片的位置
    def show_tree(self, path="demo.png"):
        map = self.map_str + "}"
        # print(map)
        graph = pdp.graph_from_dot_data(map)
        graph.write_png(path)

# 学习曲线评估算法精度 dataset: 数据练集, label: 纵轴的标签, interval: 测试规模递增的间隔
def incremental_train_scale_test(dataset, label, interval=1):
    c = dataset
    r = range(5, len(c.data) - 1, interval)
    rates = []
    for train_num in r:
        print(train_num)
        train_set = new_dataset(c.feature_names, c.target_names, c.data[:train_num], c.target[:train_num])
        test_set = new_dataset(c.feature_names, c.target_names, c.data[train_num:], c.target[train_num:])
        dt = dt_tree()
        dt.fit(train_set)
        rates.append(accuracy_rate(dt.predict(test_set), list(test_set.target)))

    print(rates)
    plt.plot(r, rates)
    plt.ylabel(label)
    plt.show()

if __name__ == '__main__':

    c = load_car()  # 载入汽车数据集
    # c = load_mushroom()  # 载入蘑菇数据集
    train_num = 1000 # 训练集规模(剩下的数据就放到测试集)
    train_set = new_dataset(c.feature_names, c.target_names, c.data[:train_num], c.target[:train_num])
    test_set = new_dataset(c.feature_names, c.target_names, c.data[train_num:], c.target[train_num:])

    dt = dt_tree()  # 初始化决策树模型
    dt.fit(train_set)  # 训练
    dt.show_tree("../image/demo.png") # 输出决策树图片
    print(accuracy_rate(dt.predict(test_set), list(test_set.target))) # 进行测试, 并计算准确率吧

    # incremental_train_scale_test(load_car(), "car")
    # incremental_train_scale_test(load_mushroom(), "mushroom", interval=20)
```



<center><h1>
    人工智能第六次实验报告
    </h1></center>
<center><h2>神经网络分类MNIST数据集</h2></center>

| 课程：人工智能原理 | 年级专业：19级软件工程 |
| ------------------ | ---------------------- |
| 姓名：郑有为       | 学号：19335286         |

## 目录

[toc]

## 一、问题背景

### 1.1 神经网络简介

**神经网络基本概念**：神经网络由许多单元组成，单元之间通过有向的链进行连接。单元的结构非常简单，如下图所示，若干结点的输出作为一个节点的输入，通过神经元输出。每一个边有一个权值，神经单元的激活函数相同。

![image-20211222224617671](image/1.png)

**前馈神经网络模型**：

前馈神经网络模型如图所示，神经网络被分为若干层次，相邻两层的结点全连接，即一层的输出作为下一层的输入；不相邻的层不存在直接相邻，网络中也不会出现环。最底层为输入层，最顶层为输出层，剩下的层为隐藏层。

![](image/9.png)

**训练神经网络过程**：反向传播算法

​		一个神经网络的好坏由各个结点的权重$w$和偏置$b$决定，神经网络引入损失函数来评估模型训练的结果，模型优化的过程就是最小化损失函数的过程。

​		反向传播的过程可以总结为：先利用观察到的误差计算输出单元的修正误差值$\Delta$，然后从输出层开始，重复以下两步：将$\Delta$值传播回前一层；更新这两层之间的权重；直到到达最早的隐藏层。

**常用的优化算法：**

* **梯度下降**：

  * 一维梯度下降：通过$x \leftarrow \eta f'(x)$来迭代$x$来逼近最优解，其中$\eta$为学习率。
  * 多维梯度下降：通过$x \leftarrow x - \eta\bigtriangledown f(x)$，来逼近最优解，其中$x$是输入向量，$\bigtriangledown f(x)$为目标函数$f(x)$有关$x$的梯度（偏导向量）
  * 随机梯度下降：每次随机均匀采样一个样本索引$i$，并计算梯度$\bigtriangledown f_i(x)$来迭代$x$。
  * 批量梯度下降：每次迭随机均匀采样多个样本来组成一个小批量，然后使用整个小批量来计算梯度。

  梯度下降算法每次迭代的方向仅取决于自变量的当前位置，可能会导致收敛变慢，甚至越过最优解并发散的问题。

* **动量法**：引入动量超参数$\gamma$，保存上一步迭代的影响，所以自变量在各个方向上的移动幅度不仅取决于当前的梯度，还取决于过去的各个梯度在各个方向上是否一致。每次迭代的步骤：
  $$
  v_t \leftarrow \gamma v_{t-1} + \eta_t \bigtriangledown f(x) \\
  x_t \leftarrow x_{t-1} - v_t
  $$

* **AdaGrad算法**：根据自变量在每个纬度的梯度值的大小来调整各个纬度上的学习率，从而避免统一的学习率难以适应所有纬度的问题。使用AdaGrad算法时，自变量中每个元素的学习率在迭代过程中会随着迭代次数而下降。
  $$
  s_t \leftarrow s_{t-1} + \bigtriangledown f(x) \odot \bigtriangledown f(x)\\
  x_t \leftarrow x_t - \frac{\eta}{\sqrt(s_t + \epsilon)} \odot \bigtriangledown f(x)
  $$
  注：这里的$\odot$是指每个元素单独相乘。

* **Adam算法**（自适应矩估计）：示例代码所使用的最优化算法就是Adam算法，算法使用了梯度按元素平方做指数加权移动平均$s_t$和动量法中的动量变量$v_t$，同样目标函数自变量中每个元素都分别拥有各自的学习率。
  $$
  v_t \leftarrow \beta_1 v_{t-1} + (1-\beta_1) \bigtriangledown f(x) \\
  s_t \leftarrow \beta_2s_{t-1} + (1-\beta_2) \bigtriangledown f(x) \odot \bigtriangledown f(x)
  $$
  当$t$较小时，过去各时间步小批量随机梯度权值之和会较小，故引入偏差修正：
  $$
  \hat{v_t} \leftarrow \frac{v_t}{1-\beta_1^t} \\
  \hat{s_t} \leftarrow \frac{s_t}{1-\beta_2^t}
  $$
  最终将模型参数中每个元素的学习率通过按元素运算重新调整，得到：
  $$
  g_t' \leftarrow \frac{\eta \hat{v}_t}{\sqrt{\hat{s}_t}+\epsilon} \\
  x_t \leftarrow x_t-1 - g_t'
  $$

### 1.2 MINST 数据说明

MNIST 数据集由手写数字 ( 0-9 ) 图片组成，每张图片由 28 x 28（784）个像素点构成，每个像素点用一个灰度值表示。

通过 import ***tensorflow1.4*** 的 `tensorflow.examples.tutorials.mnist`，调用 `read_data_sets` 方法即可获取 MNIST 数据集，数据集的组成如下：（IDX文件，是一种用来存储向量与多维度矩阵的文件格式）

* 训练集图片: train-images-idx3-ubyte.gz (含60000个样本)
* 训练集标签: train-labels-idx1-ubyte.gz (含60000个标签)
* 测试集图片: t10k-images-idx3-ubyte.gz(含10000个样本)
* 测试集标签: t10k-labels-idx1-ubyte.gz (含10000个标签)

可以执行以下代码查看部分训练集图像和标签：

```python
mnist = input_data.read_data_sets('MNIST_data', one_hot=False)
x_train, y_train = mnist.train.images, mnist.train.labels # 返回的 X_train 是 numpy 下的 多维数组，(55000, 784)

fig, ax = plt.subplots(nrows = 2, ncols = 5, sharex = True, sharey = True)
fig.tight_layout()
ax = ax.flatten()
for i in range(10):
  img = x_train[i].reshape(28,28)
  ax[i].set_title(str(y_train[i]))
  ax[i].imshow(img,cmap='Greys')
  
ax[0].set_xticks([])
ax[0].set_yticks([])
plt.show()
```



![image-20211222092652186](image/2.png)

### 1.3 TensorFlow基本概念

​		TensorFlow为张量从流图的一端流动到另一端计算过程。TensorFlow是将复杂的数据结构传输至人工智能神经网中进行分析和处理过程的系统。

​		Tensorflow的设计理念称之为计算流图，在编写程序时，首先构筑整个系统的计算流图（Graph），代码并不会直接生效，这一点和 python 的其他数值计算库（如Numpy等）不同，结构为静态的。在实际的运行时，启动一个 session（`tf.Session()`），程序才会真正的运行。Tensorflow通过计算流图的方式，来优化整个 session 所执行的代码。

* ***Tensor***：张量是 Tensorflow 中主要的数据结构，用于在计算图中进行数据传递，创建了张量后，需要将其赋值给一个变量或占位符，之后才会将该张量添加到计算图中。
* ***Session***：会话是 Tensorflow 中计算流图的具体执行者，与流图进行实际的交互。会话的主要目的是将训练数据添加到流图中进行计算，也可以修改流图的结构。一般使用 with 语句创建会话。
* ***Variable***：变量表示图中的各个计算参数，创建变量应使用 `tf.Variable()`，通过输入一个张量，返回一个变量，变量声明后需进行初始化才能使用。
* ***Placeholder***：占位符用于表示输入输出数据的格式，声明了数据位置，允许传入指定类型和形状的数据，通过会话中的 `feed_dict` 参数获取数据，在计算流图运行时使用获取的数据进行计算，计算完毕后获取的数据就会消失。

## 二、实现说明

### 2.1 构建神经网络模型

1. **为输入输出分配占位符**

   首先，为训练数据集的输入 x 和输出标签 y 创建占位符，即根据神经网络模型中的占位分配必要的内存。

   ``` python
   x = tf.placeholder(tf.float32, [None,784]) # 若干图片，大小为28*28的像素
   y = tf.placeholder(tf.float32, [None,10])  # 若干标签，大小为10的独热编码串
   ```

   同时，为了防止过度拟合，为神经网络设置 Dropout 层，以下为其分配一个占位符。

   ``` python
   keep_prob = tf.placeholder(tf.float32) # 范围：0 ~ 1
   ```

   在一些神经网络模型中，如果模型的参数太多，而训练样本又太少的话，这样训练出来的模型很容易产生过拟合现象。Dropout 层在神经网络每一批训练当中随机减掉一些神经元，上述的 `keep_drop` 就是去除神经元数目的比例。

2. **搭建分层的神经网络**

   实验程序中，包括输入输出层共有五层，每一层的节点数目分别是：768，500，1000，300，10，隐层的节点数目是可以进行调整的。在激活函数的选择上，除了最后一层采用 softmax 之外，其余采用 relu。

   *  ReLU 线性整流函数（Rectified Linear Unit）：在输入小于0的值幅值为0，输入大于0的值不变。
     $$
     ReLU(x) = \left\{  
                  \begin{array}{**lr**}  
                  0, &  x \le 0\\  
                  x, & x > 0
                  \end{array}  
     \right.
     $$

   * Softmax 归一化函数：将输入序列转化成每个数字都在[0,1)之间，且数字的和加起来都等于1的概率序列。
     $$
     Softmax(x)_i = \frac{\exp(x_i)}{\sum_j\exp(x_j)}
     $$

   在搭建网络前，引入两个初始化函数 `weight_variable` 和 `bias_variable` ，分别用来初始化权重 $w$ 和偏置 $b$（节点计算 $y = w x + b$），其中权重初始化采取截断正态分布随机数，生成均值为 $0$ ，标准差为 $0.1$ 且范围位于 $[-0.2,0.2]$ 的随机数，而偏置量取 $0.1$。

   ```python
   def weight_variable(shape):
       initial = tf.truncated_normal(shape, stddev = 0.1) 
       return tf.Variable(initial)
   
   def bias_variable(shape):
       initial = tf.constant(0.1, shape = shape)
       return tf.Variable(initial)
   ```

   接下来搭建分层网络：

   ```python
   # Level 1
   W_layer1 = weight_variable([784, 500])  
   b_layer1 = bias_variable([500]) 
   h1 = tf.add(tf.matmul(x, W_layer1), b_layer1)
   h1 = tf.nn.relu(h1)
   
   # Level 2
   W_layer2 = weight_variable([500, 1000])  
   b_layer2 = bias_variable([1000])   
   h2 = tf.add(tf.matmul(h1, W_layer2), b_layer2)
   h2 = tf.nn.relu(h2)
   
   # Level 3
   W_layer3 = weight_variable([1000, 300])  
   b_layer3 = bias_variable([300])    
   h3 = tf.add(tf.matmul(h2, W_layer3), b_layer3)
   h3 = tf.nn.relu(h3)
   
   # Level 4
   W_layer4 = weight_variable([300, 10])  
   b_layer4 = bias_variable([10])    
   predict = tf.add(tf.matmul(h3, W_layer4), b_layer4)
   y_conv = tf.nn.softmax(tf.matmul(h3, W_layer4) + b_layer4)
   ```

   搭建完神经网络框架之后，需要考虑如何进行训练并修改参数。

   

3. 引入**交叉熵代价函数（Cross-entropy cost function）**，其定义如下：其中$x$为样本，$n$为样本的总数
   $$
   C = -\frac{1}{n}\sum_x[y\ln a + (1-y) \ln (1-a)]
   $$
   可以计算参数$w$和参数$b$的梯度：
   $$
   \frac{\partial C}{\partial w_j} = -\frac{1}{n}\sum_x[y\ln a + (1-y) \ln (1-a)] \frac{\partial \sigma}{\partial w_j} = \frac{1}{n}\sum_x x_j(\sigma(z) - y)
   $$

   $$
   \frac{\partial C}{\partial b} = \frac{1}{n}\sum_x(\sigma(z) - y)
   $$

   其中，Sigmoid函数
   $$
   \sigma(z) = \frac{1}{a+e^{-z}}
   $$
   根据神经网络得到输出后，计算预测结果的交叉熵代价函数。该函数用于衡量预测值与实际值的差距。在训练时，如果预测值与实际值的误差越大，那么在反向传播训练的过程中，各种参数调整的幅度就要更大，从而使训练更快收敛。实现上，可以使用`tf.nn.softmax_cross_entropy_with_logits`来实现。

   ``` python
   cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits = predict, labels = y))
   ```

4.	获得交叉熵代价后，通过Adam下降算法修正模型中的参数来缩小损失。

   **Adam下降算法**：Adam下降算法是一种自适应动量的随机优化方法，思路在1.1中简述，效果优于一般的梯度下降算法。TensorFlow提供Adam优化器`AdamOptimizer`，其默认参数如下：

   ```python
   __init__(
       learning_rate=0.001,    # 学习率
       beta1=0.9,				# 一阶矩估计的指数衰减率 \beta_1
       beta2=0.999,			# 二阶矩估计的指数衰减率 \beta_2
       epsilon=1e-08,			# 防止除以零的树 \epsilon
       use_locking=False,		
       name='Adam'
   )
   ```

   `minimize`函数最大限度地最小化 损失值。

   ```python
   train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
   ```


5. **处理预测结果**

   ``` python
   # 预测是否准确的结果存放在一个布尔型的列表中
   # argmax返回的矩阵行中的最大值的索引号
   correct_prediction = tf.equal(tf.argmax(y_conv, 1), tf.argmax(y, 1))
   
   # 求预测准确率
   # cast将布尔型的数据转换成float型的数据；reduce_mean求平均值
   accuracy = tf.reduce_mean(tf.cast(correct_prediction, 'float'))
   ```

### 2.2 运行模型

首先调用`tf.global_variables_initializer()`初始化模型的参数，Session提供了Operation执行和Tensor求值的环境

```python
# 初始化
init_op = tf.global_variables_initializer()

with tf.Session() as sess:
    sess.run(init_op)
    
    # 训练样本为55000，分成550批，每批为100个样本
    for i in range(550): 
        # 获取一批含100个样本的数据
        batch = mnist.train.next_batch(100)
        
        # 每过50批，显示其在训练集上的准确率和在测试集上的准确率
        if i % 50 == 0: 
            train_accuracy = accuracy.eval(feed_dict={x: batch[0], y: batch[1], keep_prob: 1.0})
            test_accuracy = accuracy.eval(feed_dict={x: mnist.test.images, y: mnist.test.labels})
            print( 'step %d, training accuracy %g, test accuracy %g' %(i, train_accuracy, test_accuracy))
            
            # 每一步迭代，都会加载100个训练样本，然后执行一次train_step，并通过feed_dict，用训练数据替代x和y张量占位符。 
            sess.run(train_step, feed_dict = {x: batch[0], y: batch[1], keep_prob: 0.5})
            # 显示最终在测试集上的准确率 
            print ('test accuracy %g' % accuracy.eval(feed_dict={x: mnist.test.images, y: mnist.test.labels, keep_prob: 1.0}))
```

其中：

* 模型训练分批次，每一批用100个样本训练神经网络模型，每一批都在上一批的基础上对网络模型的参数进行调整。

* `mnist.train.next_batch`：返回的是一组元组，元组的第一个元素图片像素阵列，第二个元素为 one-hot 格式的预测标签。

* `eval()` ：在一个Session 里面计算张量的值，执行定义的所有必要的操作来产生这个计算这个张量需要的输入，然后通过这些输入产生这个张量。
* `feed_dict`作用是给使用 `placeholder `创建出来的张量赋值，上述我们使用 `placeholder` 定义的占位符包括输入`x`、输出`y`和Dropout 层保留比例`keep_prob`。

## 三、程序测试

### 3.1 运行说明

因为实验代码所需要的TensorFlow版本为1.4.0，而现在TensorFlow的版本已经上升到了2.x，一些以前提供的数据集、函数已经被删除，故直接运行会报错，报错内容为找不到 `tensorflow.examples` 包。

我们可以使用一些Online运行环境，如 Google Colab （https://colab.research.google.com/）。使用云计算来运行我们的程序，将TensorFlow降级至1.4.0，而不修改本地 Python 的配置。

将TensorFlow降级的方法如下：在文件首行加入以下代码，然后再 `import tensorflow`。

```python
%tensorflow_version 1.4.0
```

执行程序后会首先出现以下输出，程序其他部分无需修改即可以正常运行，运行结果与预期一致。

```
`%tensorflow_version` only switches the major version: 1.x or 2.x.
You set: `1.4.0`. This will be interpreted as: `1.x`.

TensorFlow 1.x selected.
```

### 3.2 运行输出

运行输出如下：可以看到随着测试规模的增加，训练和测试的准确率也不断地在上升。

```
step 0, training accuracy 0.07, test accuracy 0.1024
step 50, training accuracy 0.91, test accuracy 0.8892
step 100, training accuracy 0.95, test accuracy 0.9325
step 150, training accuracy 0.94, test accuracy 0.9405
step 200, training accuracy 0.95, test accuracy 0.9468
step 250, training accuracy 0.96, test accuracy 0.9518
step 300, training accuracy 0.94, test accuracy 0.9543
step 350, training accuracy 0.97, test accuracy 0.9645
step 400, training accuracy 0.94, test accuracy 0.9588
step 450, training accuracy 0.95, test accuracy 0.9655
step 500, training accuracy 1, test accuracy 0.9608
test accuracy 0.9586
```

尝试修改部分参数，观察输出变化情况。

* **提高Adam下降算法的学习率**：将学习率从$10^{-4}$提高到$10^{-3}$、$10^-2$

  ``` python
  train_step = tf.train.AdamOptimizer(1e-3).minimize(cross_entropy)
  ```

  可以看到随着学习率的提高，测试正确率有明显的提高，但耗时随之上升。

  ```
  step 0, training accuracy 0.08, test accuracy 0.1123
  step 50, training accuracy 0.94, test accuracy 0.913
  step 100, training accuracy 0.9, test accuracy 0.9283
  step 150, training accuracy 0.95, test accuracy 0.9442
  step 200, training accuracy 0.91, test accuracy 0.9413
  step 250, training accuracy 0.94, test accuracy 0.954
  step 300, training accuracy 0.93, test accuracy 0.9513
  step 350, training accuracy 0.99, test accuracy 0.9598
  step 400, training accuracy 0.97, test accuracy 0.9609
  step 450, training accuracy 0.94, test accuracy 0.9584
  step 500, training accuracy 0.96, test accuracy 0.9609
  test accuracy 0.9651
  ```

  当学习率提高到$10^-2$时，过高的学习率容易跳过最优值，预测效果反而下降。

  ```
  step 0, training accuracy 0.07, test accuracy 0.0877
  step 50, training accuracy 0.89, test accuracy 0.9095
  step 100, training accuracy 0.94, test accuracy 0.9233
  step 150, training accuracy 0.91, test accuracy 0.9267
  step 200, training accuracy 0.89, test accuracy 0.882
  step 250, training accuracy 0.96, test accuracy 0.9383
  step 300, training accuracy 0.92, test accuracy 0.9426
  step 350, training accuracy 0.96, test accuracy 0.9384
  step 400, training accuracy 0.95, test accuracy 0.9524
  step 450, training accuracy 0.93, test accuracy 0.9504
  step 500, training accuracy 0.95, test accuracy 0.9563
  test accuracy 0.9469
  ```

  | 学习率   | $10^-4$          | $10^-3$（效果最好） | $10^-2$          |
  | -------- | ---------------- | ------------------- | ---------------- |
  | 输出图像 | ![](image/3.png) | ![](image/4.png)    | ![](image/5.Png) |

* **增加/减少神经网络隐层**

  经测试，网络层数（3，4，5）对模型效果的影响不明显。而层次相同的神经网络中节点数目多的表现出性能更优。

## 四、实验总结

​		通过本次实验，我们深入理解了前馈神经网络模型，通过示例代码，研究MINST数据集训练神经网络的过程。第一次了解 TensorFlow，学习了TensorFlow的基本概念和用法，掌握了如何运用TensorFlow来构建一个神经网络模型。
