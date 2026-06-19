# 动作: 上(0), 右(1), 下(2), 左(3)

> 来源模块: module2_training
> 原始文件: q32_qlearning_dqn.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】强化学习基础：Q-Learning、SARSA与DQN
【模块】模型训练与评估
【难度】6
【知识点】Q-Learning、SARSA、DQN、强化学习、网格世界、PyTorch、经验回放
【描述】
实现三种强化学习算法：表格型Q-Learning、SARSA和深度Q网络(DQN)。在自定义的
GridWorld环境中训练智能体，对比三种算法的学习效果。

【要求】
1. 实现GridWorld环境（4x4网格，起点、终点、障碍物）
2. 实现Q-Learning算法（epsilon-greedy策略）
3. 实现SARSA算法
4. 实现DQN算法（使用PyTorch，包含经验回放和目标网络）
5. 训练三种算法并对比奖励曲线
6. 输出学习到的最优策略

【提示】
- Q-Learning是off-policy算法，SARSA是on-policy算法
- DQN使用经验回放缓冲区打破数据相关性
- 使用epsilon-greedy策略进行探索
- 目标网络定期更新以稳定训练
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os


# ======================== GridWorld 环境 ========================

class GridWorld:
    """简单的网格世界环境"""

    # 动作: 上(0), 右(1), 下(2), 左(3)
    UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
    ACTIONS = [UP, RIGHT, DOWN, LEFT]

    def __init__(self, size=4):
        self.size = size
        self.start = (0, 0)
        self.goal = (size - 1, size - 1)
        self.obstacles = [(1, 1), (2, 2)]
        self.reset()

    def reset(self):
        self.agent_pos = self.start
        return self._get_state()

    def _get_state(self):
        return self.agent_pos[0] * self.size + self.agent_pos[1]

    def step(self, action):
        r, c = self.agent_pos

        # 执行动作
        if action == self.UP:
            r = max(0, r - 1)
        elif action == self.RIGHT:
            c = min(self.size - 1, c + 1)
        elif action == self.DOWN:
            r = min(self.size - 1, r + 1)
        elif action == self.LEFT:
            c = max(0, c - 1)

        new_pos = (r, c)

        # 检查是否撞障碍物
        if new_pos in self.obstacles:
            new_pos = self.agent_pos  # 原地不动
            reward = -2.0
        elif new_pos == self.goal:
            reward = 10.0
        else:
            reward = -0.1  # 每步小惩罚

        self.agent_pos = new_pos
        done = (new_pos == self.goal)
        next_state = self._get_state()

        return next_state, reward, done

    def get_num_states(self):
        return self.size * self.size

    def get_num_actions(self):
        return 4

    def render(self):
        """文本渲染环境"""
        grid = [["." for _ in range(self.size)] for _ in range(self.size)]
        for obs in self.obstacles:
            grid[obs[0]][obs[1]] = "X"
        grid[self.goal[0]][self.goal[1]] = "G"
        grid[self.agent_pos[0]][self.agent_pos[1]] = "A"
        for row in grid:
            print(" ".join(row))
        print()


# ======================== Q-Learning ========================

class QLearningAgent:
    """Q-Learning 智能体"""

    def __init__(self, num_states, num_actions, lr=0.1, gamma=0.95, epsilon=0.3):
        self.num_states = num_states
        self.num_actions = num_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = np.zeros((num_states, num_actions))

    def choose_action(self, state):
        """epsilon-greedy策略选择动作"""
        if random.random() < self.epsilon:
            return random.randint(0, self.num_actions - 1)
        else:
            return int(np.argmax(self.q_table[state]))

    def update(self, state, action, reward, next_state, done):
        """Q-Learning更新: Q(s,a) = Q(s,a) + lr * (r + gamma * max_a' Q(s',a') - Q(s,a))"""
        if done:
            target = reward
        else:
            target = reward + self.gamma * np.max(self.q_table[next_state])

        self.q_table[state, action] += self.lr * (target - self.q_table[state, action])

    def decay_epsilon(self, decay=0.995):
        self.epsilon = max(0.01, self.epsilon * decay)


# ======================== SARSA ========================

class SARSAAgent:
    """SARSA 智能体"""

    def __init__(self, num_states, num_actions, lr=0.1, gamma=0.95, epsilon=0.3):
        self.num_states = num_states
        self.num_actions = num_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = np.zeros((num_states, num_actions))

    def choose_action(self, state):
        """epsilon-greedy策略"""
        if random.random() < self.epsilon:
            return random.randint(0, self.num_actions - 1)
        else:
            return int(np.argmax(self.q_table[state]))

    def update(self, state, action, reward, next_state, next_action, done):
        """SARSA更新: Q(s,a) = Q(s,a) + lr * (r + gamma * Q(s',a') - Q(s,a))"""
        if done:
            target = reward
        else:
            target = reward + self.gamma * self.q_table[next_state, next_action]

        self.q_table[state, action] += self.lr * (target - self.q_table[state, action])

    def decay_epsilon(self, decay=0.995):
        self.epsilon = max(0.01, self.epsilon * decay)


# ======================== DQN ========================

class ReplayBuffer:
    """经验回放缓冲区"""

    def __init__(self, capacity=5000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32),
        )

    def __len__(self):
        return len(self.buffer)


class QNetwork(nn.Module):
    """DQN网络"""

    def __init__(self, state_dim, action_dim, hidden_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(self, x):
        return self.net(x)


class DQNAgent:
    """DQN 智能体"""

    def __init__(self, state_dim, action_dim, lr=1e-3, gamma=0.95,
                 epsilon=0.5, buffer_capacity=5000, batch_size=32,
                 target_update_freq=50):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 在线网络
        self.policy_net = QNetwork(state_dim, action_dim).to(self.device)
        # 目标网络
        self.target_net = QNetwork(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.buffer = ReplayBuffer(buffer_capacity)
        self.train_step = 0

    def choose_action(self, state):
        """epsilon-greedy策略"""
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        else:
            with torch.no_grad():
                state_t = torch.FloatTensor([state]).to(self.device)
                q_values = self.policy_net(state_t)
                return int(q_values.argmax(dim=1).item())

    def update(self, state, action, reward, next_state, done):
        """存储经验并学习"""
        self.buffer.push(state, action, reward, next_state, done)

        if len(self.buffer) < self.batch_size:
            return

        # 采样batch
        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)

        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards_t = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        # 当前Q值
        q_values = self.policy_net(states_t).gather(1, actions_t)

        # 目标Q值
        with torch.no_grad():
            next_q_max = self.target_net(next_states_t).max(dim=1, keepdim=True)[0]
            target_q = rewards_t + self.gamma * next_q_max * (1 - dones_t)

        # 计算损失
        loss = nn.MSELoss()(q_values, target_q)

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 定期更新目标网络
        self.train_step += 1
        if self.train_step % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self, decay=0.995):
        self.epsilon = max(0.01, self.epsilon * decay)


# ======================== 训练函数 ========================

def train_qlearning(env, num_episodes=300):
    """训练Q-Learning"""
    agent = QLearningAgent(
        num_states=env.get_num_states(),
        num_actions=env.get_num_actions(),
        lr=0.1, gamma=0.95, epsilon=0.3,
    )

    rewards_history = []

    for ep in range(num_episodes):
        state = env.reset()
        total_reward = 0
        done = False
        steps = 0

        while not done and steps < 100:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            agent.update(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            steps += 1

        agent.decay_epsilon()
        rewards_history.append(total_reward)

    return agent, rewards_history


def train_sarsa(env, num_episodes=300):
    """训练SARSA"""
    agent = SARSAAgent(
        num_states=env.get_num_states(),
        num_actions=env.get_num_actions(),
        lr=0.1, gamma=0.95, epsilon=0.3,
    )

    rewards_history = []

    for ep in range(num_episodes):
        state = env.reset()
        action = agent.choose_action(state)
        total_reward = 0
        done = False
        steps = 0

        while not done and steps < 100:
            next_state, reward, done = env.step(action)
            next_action = agent.choose_action(next_state)
            agent.update(state, action, reward, next_state, next_action, done)
            state = next_state
            action = next_action
            total_reward += reward
            steps += 1

        agent.decay_epsilon()
        rewards_history.append(total_reward)

    return agent, rewards_history


def train_dqn(env, num_episodes=300):
    """训练DQN"""
    # DQN使用one-hot编码的状态
    state_dim = env.get_num_states()
    action_dim = env.get_num_actions()

    agent = DQNAgent(
        state_dim=state_dim, action_dim=action_dim,
        lr=1e-3, gamma=0.95, epsilon=0.5,
        buffer_capacity=5000, batch_size=32,
        target_update_freq=50,
    )

    rewards_history = []

    for ep in range(num_episodes):
        state_idx = env.reset()
        # one-hot编码
        state = np.zeros(state_dim, dtype=np.float32)
        state[state_idx] = 1.0

        total_reward = 0
        done = False
        steps = 0

        while not done and steps < 100:
            action = agent.choose_action(state)
            next_state_idx, reward, done = env.step(action)
            next_state = np.zeros(state_dim, dtype=np.float32)
            next_state[next_state_idx] = 1.0

            agent.update(state, action, reward, next_state, float(done))
            state = next_state
            total_reward += reward
            steps += 1

        agent.decay_epsilon()
        rewards_history.append(total_reward)

    return agent, rewards_history


# ======================== 可视化与输出 ========================

def print_policy(q_table, env_size, obstacles, name="Q-Table"):
    """打印从Q表导出的策略"""
    action_symbols = ["^", ">", "v", "<"]
    print(f"\n{name} 学习到的策略:")
    print("-" * (env_size * 4 + 1))
    for r in range(env_size):
        row_str = "|"
        for c in range(env_size):
            if (r, c) in obstacles:
                row_str += " X |"
            elif r == env_size - 1 and c == env_size - 1:
                row_str += " G |"
            else:
                state = r * env_size + c
                best_action = np.argmax(q_table[state])
                row_str += f" {action_symbols[best_action]} |"
        print(row_str)
        print("-" * (env_size * 4 + 1))


def smooth(data, window=20):
    """移动平均平滑"""
    if len(data) < window:
        return data
    return np.convolve(data, np.ones(window) / window, mode="valid")


# ======================== 主函数 ========================

def solve():
    """强化学习三种算法对比演示"""
    print("=" * 60)
    print("强化学习基础: Q-Learning, SARSA, DQN")
    print("=" * 60)

    # ---- 创建环境 ----
    env = GridWorld(size=4)
    print(f"\n环境: {env.size}x{env.size} GridWorld")
    print(f"起点: {env.start}, 终点: {env.goal}")
    print(f"障碍物: {env.obstacles}")
    print(f"状态数: {env.get_num_states()}, 动作数: {env.get_num_actions()}")
    print("\n初始环境:")
    env.render()

    # ---- 训练三种算法 ----
    num_episodes = 300

    print("训练 Q-Learning...")
    q_agent, q_rewards = train_qlearning(env, num_episodes)
    print(f"  最终100轮平均奖励: {np.mean(q_rewards[-100:]):.2f}")

    print("训练 SARSA...")
    sarsa_agent, sarsa_rewards = train_sarsa(env, num_episodes)
    print(f"  最终100轮平均奖励: {np.mean(sarsa_rewards[-100:]):.2f}")

    print("训练 DQN...")
    dqn_agent, dqn_rewards = train_dqn(env, num_episodes)
    print(f"  最终100轮平均奖励: {np.mean(dqn_rewards[-100:]):.2f}")

    # ---- 输出策略 ----
    print_policy(q_agent.q_table, env.size, env.obstacles, "Q-Learning")
    print_policy(sarsa_agent.q_table, env.size, env.obstacles, "SARSA")

    # DQN策略
    print("\nDQN 学习到的策略:")
    action_symbols = ["^", ">", "v", "<"]
    print("-" * (env.size * 4 + 1))
    for r in range(env.size):
        row_str = "|"
        for c in range(env.size):
            if (r, c) in env.obstacles:
                row_str += " X |"
            elif r == env.size - 1 and c == env.size - 1:
                row_str += " G |"
            else:
                state_oh = np.zeros(env.get_num_states(), dtype=np.float32)
                state_oh[r * env.size + c] = 1.0
                with torch.no_grad():
                    state_t = torch.FloatTensor([state_oh]).to(dqn_agent.device)
                    best_action = int(dqn_agent.policy_net(state_t).argmax(dim=1).item())
                row_str += f" {action_symbols[best_action]} |"
        print(row_str)
        print("-" * (env.size * 4 + 1))

    # ---- 奖励曲线对比 ----
    output_dir = os.path.dirname(__file__) or "."
    plt.figure(figsize=(10, 5))

    q_smooth = smooth(q_rewards, 20)
    sarsa_smooth = smooth(sarsa_rewards, 20)
    dqn_smooth = smooth(dqn_rewards, 20)

    plt.plot(q_smooth, label="Q-Learning", alpha=0.8)
    plt.plot(sarsa_smooth, label="SARSA", alpha=0.8)
    plt.plot(dqn_smooth, label="DQN", alpha=0.8)
    plt.xlabel("Episode")
    plt.ylabel("Total Reward (smoothed)")
    plt.title("强化学习算法对比 - GridWorld")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, "rl_comparison.png"), dpi=100, bbox_inches="tight")
    plt.close()
    print(f"\n奖励曲线已保存: {os.path.join(output_dir, 'rl_comparison.png')}")

    # ---- 测试最优策略 ----
    print("\n测试最优策略（Q-Learning）:")
    state = env.reset()
    env.render()
    total_reward = 0
    for step in range(20):
        action = int(np.argmax(q_agent.q_table[state]))
        next_state, reward, done = env.step(action)
        action_names = ["上", "右", "下", "左"]
        print(f"Step {step + 1}: 动作={action_names[action]}, 奖励={reward:.1f}")
        state = next_state
        total_reward += reward
        if done:
            print(f"到达终点! 总奖励: {total_reward:.2f}")
            break

    print("\n强化学习演示完成。")


if __name__ == "__main__":
    solve()

```
