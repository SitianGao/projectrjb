# Actor-Critic 方法

## 1. Policy Gradient 基础

### 策略梯度方法 vs 值方法

| 方法 | 核心思想 | 优点 | 缺点 |
|------|----------|------|------|
| Value-based (DQN) | 学习 Q(s,a)，策略由 max Q 导出 | 样本效率高 | 不适于连续动作空间 |
| Policy-based | 直接学习策略 π(a|s) | 支持连续/随机策略 | 方差大、收敛慢 |

### Policy Gradient 定理

策略梯度目标：最大化期望累积奖励 J(θ) = E[Σ r_t]

梯度：
```
∇J(θ) = E[∇log π_θ(a|s) * G_t]
```

其中 G_t 是累积奖励（Return），可以用以下替代：
- **Monte Carlo**：G_t = Σ γ^k * r_{t+k}（完整 episode）
- **TD**：G_t ≈ r_t + γ * V(s_{t+1})（单步）

### REINFORCE 算法

最基础的策略梯度方法：
1. 用当前策略采样完整 episode
2. 对每个时间步，用 G_t 作为权重更新策略
3. 优点：无偏估计
4. 缺点：方差大（需要大量样本）

## 2. Actor-Critic 架构

### 核心思想

Actor-Critic 结合了策略梯度（Actor）和值函数（Critic）：
- **Actor（π(a|s)）**：决定采取什么动作（策略网络）
- **Critic（V(s) 或 Q(s,a)）**：评估动作的好坏（价值网络）

### 优势函数（Advantage Function）

A(s, a) = Q(s, a) - V(s)

优势函数衡量动作 a 相对于平均水平的优劣。用它替代原始 Return 可以显著**减少方差**。

### 梯度更新

Actor 更新（策略梯度）：
```
∇J(θ) = E[∇log π_θ(a|s) * A(s, a)]
```

Critic 更新（TD 误差）：
```
δ = r + γ * V(s') - V(s)
Loss_critic = δ²
```

## 3. A2C（Advantage Actor-Critic）

A2C 是同步版本的 Actor-Critic：
- 多个并行环境同时采样
- 每个环境独立与环境交互
- 将各环境的梯度平均后统一更新
- **优势**：稳定、适合 GPU 加速

## 4. A3C（Asynchronous Advantage Actor-Critic）

### 异步架构

- 多个 Worker 线程独立运行
- 每个 Worker 有自己的环境副本
- 各 Worker 异步向全局网络推送梯度更新
- 全局网络聚合更新后分发最新参数

### 优势

- **探索多样性**：不同 Worker 使用不同探索策略
- **无需经验回放**：异步更新天然去相关
- **训练速度快**：充分利用多核 CPU

### 算法流程

1. 初始化全局网络 θ（Actor + Critic）
2. 每个 Worker 线程：
   - 从全局网络复制参数
   - 与环境交互收集 N 步经验
   - 计算梯度并更新全局网络
3. 持续运行直到收敛

## 5. 实践建议

### 网络设计
- Actor 和 Critic 通常共享底层特征提取层
- Actor 输出层：softmax（离散）或高斯分布参数（连续）
- Critic 输出层：单个标量值

### 超参数
- Actor 学习率：1e-4 到 1e-3
- Critic 学习率：通常比 Actor 大 2-10 倍
- 熵正则化系数：0.01（鼓励探索）
- N 步回报：通常 5-20 步
