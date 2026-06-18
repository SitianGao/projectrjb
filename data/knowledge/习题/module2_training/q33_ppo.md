# 如果超出限制则给负奖励

> 来源模块: module2_training
> 原始文件: q33_ppo.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】PPO策略优化
【模块】模型训练与评估
【难度】8
【知识点】PPO、Actor-Critic、策略梯度、优势函数、Clip、PyTorch
【描述】
使用PyTorch实现PPO（Proximal Policy Optimization）算法，采用Actor-Critic结构，
在CartPole环境（或自定义简单环境）上训练。PPO通过裁剪目标函数限制策略更新幅度，
保证训练稳定性。

【要求】
1. 实现Actor网络（策略网络）和Critic网络（价值网络）
2. 实现PPO的裁剪目标函数（clip epsilon）
3. 实现广义优势估计（GAE）
4. 实现完整的PPO训练循环（收集轨迹 -> 计算优势 -> 多轮更新）
5. 在CartPole-v1环境或自定义环境中训练
6. 可视化训练过程中的奖励曲线

【提示】
- PPO-Clip目标: L = min(ratio * A, clip(ratio, 1-eps, 1+eps) * A)
- ratio = pi_new(a|s) / pi_old(a|s)
- GAE: A_t = sum_{l=0}^{T-t-1} (gamma*lambda)^l * delta_{t+l}
- 使用Gymnasium或自定义简单环境
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from collections import deque


# ======================== 自定义CartPole环境 ========================

class SimpleCartPole:
    """
    简化的CartPole环境（不依赖gym）
    状态: [x, x_dot, theta, theta_dot]
    动作: 0(向左推), 1(向右推)
    """

    def __init__(self):
        self.gravity = 9.8
        self.masscart = 1.0
        self.masspole = 0.1
        self.total_mass = self.masscart + self.masspole
        self.length = 0.5
        self.polemass_length = self.masspole * self.length
        self.force_mag = 10.0
        self.tau = 0.02
        self.state_dim = 4
        self.action_dim = 2

        self.x_threshold = 2.4
        self.theta_threshold = 12 * np.pi / 180  # 12度

        self.max_steps = 500
        self.step_count = 0

    def reset(self):
        self.state = np.random.uniform(-0.05, 0.05, size=4).astype(np.float32)
        self.step_count = 0
        return self.state.copy()

    def step(self, action):
        x, x_dot, theta, theta_dot = self.state
        force = self.force_mag if action == 1 else -self.force_mag

        costheta = np.cos(theta)
        sintheta = np.sin(theta)

        temp = (force + self.polemass_length * theta_dot ** 2 * sintheta) / self.total_mass
        theta_acc = (
            (self.gravity * sintheta - costheta * temp)
            / (self.length * (4.0 / 3.0 - self.masspole * costheta ** 2 / self.total_mass))
        )
        x_acc = temp - self.polemass_length * theta_acc * costheta / self.total_mass

        x += self.tau * x_dot
        x_dot += self.tau * x_acc
        theta += self.tau * theta_dot
        theta_dot += self.tau * theta_acc

        self.state = np.array([x, x_dot, theta, theta_dot], dtype=np.float32)
        self.step_count += 1

        done = (
            abs(x) > self.x_threshold
            or abs(theta) > self.theta_threshold
            or self.step_count >= self.max_steps
        )

        reward = 1.0 if not done else 0.0
        # 如果超出限制则给负奖励
        if abs(x) > self.x_threshold or abs(theta) > self.theta_threshold:
            reward = 0.0

        return self.state.copy(), reward, done


# ======================== Actor-Critic 网络 ========================

class ActorCritic(nn.Module):
    """PPO的Actor-Critic网络"""

    def __init__(self, state_dim, action_dim, hidden_dim=64):
        super().__init__()

        # 共享特征提取层
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
        )

        # Actor头（策略网络）
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1),
        )

        # Critic头（价值网络）
        self.critic = nn.Linear(hidden_dim, 1)

    def forward(self, state):
        features = self.shared(state)
        action_probs = self.actor(features)
        state_value = self.critic(features)
        return action_probs, state_value

    def get_action(self, state):
        """选择动作并返回相关信息"""
        action_probs, state_value = self.forward(state)
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        return action, log_prob, state_value, entropy

    def evaluate(self, states, actions):
        """评估给定状态-动作对"""
        action_probs, state_values = self.forward(states)
        dist = torch.distributions.Categorical(action_probs)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return log_probs, state_values.squeeze(), entropy


# ======================== PPO算法 ========================

class PPOAgent:
    """PPO智能体"""

    def __init__(
        self, state_dim, action_dim, hidden_dim=64,
        lr=3e-4, gamma=0.99, gae_lambda=0.95,
        clip_epsilon=0.2, ppo_epochs=4, batch_size=64,
        entropy_coef=0.01, value_coef=0.5,
    ):
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.ppo_epochs = ppo_epochs
        self.batch_size = batch_size
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = ActorCritic(state_dim, action_dim, hidden_dim).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)

    def compute_gae(self, rewards, values, dones, next_value):
        """计算广义优势估计(GAE)"""
        advantages = []
        gae = 0

        # 从后往前计算
        values = list(values) + [next_value]
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages.insert(0, gae)

        advantages = torch.tensor(advantages, dtype=torch.float32)
        returns = advantages + torch.tensor(values[:-1], dtype=torch.float32)
        return advantages, returns

    def collect_trajectories(self, env, num_steps=2048):
        """收集轨迹数据"""
        states, actions, rewards, dones, log_probs, values = [], [], [], [], [], []

        state = env.reset()
        episode_rewards = []
        current_ep_reward = 0

        for _ in range(num_steps):
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                action, log_prob, value, _ = self.model.get_action(state_t)

            action_np = action.item()
            next_state, reward, done = env.step(action_np)

            states.append(state)
            actions.append(action_np)
            rewards.append(reward)
            dones.append(float(done))
            log_probs.append(log_prob.item())
            values.append(value.item())

            current_ep_reward += reward
            if done:
                episode_rewards.append(current_ep_reward)
                current_ep_reward = 0
                state = env.reset()
            else:
                state = next_state

        # 计算最后一个状态的价值
        with torch.no_grad():
            last_state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            _, next_value = self.model(last_state_t)
            next_value = next_value.item()

        # 计算GAE和returns
        advantages, returns = self.compute_gae(rewards, values, dones, next_value)

        return (
            torch.FloatTensor(np.array(states)).to(self.device),
            torch.LongTensor(actions).to(self.device),
            log_probs,
            advantages.to(self.device),
            returns.to(self.device),
            episode_rewards,
        )

    def update(self, states, actions, old_log_probs, advantages, returns):
        """PPO更新"""
        # 标准化优势
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        old_log_probs = torch.FloatTensor(old_log_probs).to(self.device).detach()

        total_loss_val = 0
        num_updates = 0

        dataset_size = states.size(0)
        for _ in range(self.ppo_epochs):
            # 随机打乱
            indices = torch.randperm(dataset_size)

            for start in range(0, dataset_size, self.batch_size):
                end = min(start + self.batch_size, dataset_size)
                idx = indices[start:end]

                batch_states = states[idx]
                batch_actions = actions[idx]
                batch_old_log_probs = old_log_probs[idx]
                batch_advantages = advantages[idx]
                batch_returns = returns[idx]

                # 评估当前策略
                new_log_probs, state_values, entropy = self.model.evaluate(
                    batch_states, batch_actions
                )

                # 计算ratio
                ratio = torch.exp(new_log_probs - batch_old_log_probs)

                # PPO Clip目标
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(
                    ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon
                ) * batch_advantages
                actor_loss = -torch.min(surr1, surr2).mean()

                # Critic损失
                critic_loss = F.mse_loss(state_values, batch_returns)

                # 熵奖励
                entropy_loss = -entropy.mean()

                # 总损失
                loss = actor_loss + self.value_coef * critic_loss + self.entropy_coef * entropy_loss

                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), 0.5)
                self.optimizer.step()

                total_loss_val += loss.item()
                num_updates += 1

        return total_loss_val / num_updates


# ======================== 主函数 ========================

def solve():
    """PPO算法完整演示"""
    print("=" * 60)
    print("PPO (Proximal Policy Optimization) 算法演示")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # ---- 创建环境 ----
    env = SimpleCartPole()
    print(f"\n环境: CartPole (自定义实现)")
    print(f"状态维度: {env.state_dim}, 动作维度: {env.action_dim}")

    # ---- 超参数 ----
    state_dim = env.state_dim
    action_dim = env.action_dim
    hidden_dim = 64
    lr = 3e-4
    gamma = 0.99
    gae_lambda = 0.95
    clip_epsilon = 0.2
    ppo_epochs = 4
    batch_size = 64
    num_iterations = 30
    steps_per_iter = 2048

    # ---- 创建PPO智能体 ----
    agent = PPOAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        hidden_dim=hidden_dim,
        lr=lr,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_epsilon=clip_epsilon,
        ppo_epochs=ppo_epochs,
        batch_size=batch_size,
    )

    total_params = sum(p.numel() for p in agent.model.parameters())
    print(f"模型参数量: {total_params:,}")

    # ---- 训练 ----
    print("\n开始训练...")
    print("-" * 60)

    all_rewards = []
    all_losses = []

    for iteration in range(num_iterations):
        # 收集轨迹
        states, actions, log_probs, advantages, returns, episode_rewards = (
            agent.collect_trajectories(env, num_steps=steps_per_iter)
        )

        # 更新策略
        avg_loss = agent.update(states, actions, log_probs, advantages, returns)

        mean_reward = np.mean(episode_rewards) if episode_rewards else 0
        all_rewards.extend(episode_rewards)
        all_losses.append(avg_loss)

        if (iteration + 1) % 5 == 0 or iteration == 0:
            recent = all_rewards[-50:] if len(all_rewards) >= 50 else all_rewards
            print(
                f"Iter {iteration + 1:3d}/{num_iterations} | "
                f"Episodes: {len(episode_rewards)} | "
                f"Mean Reward: {mean_reward:.1f} | "
                f"Recent Avg: {np.mean(recent):.1f} | "
                f"Loss: {avg_loss:.4f}"
            )

    print("-" * 60)

    # ---- 结果可视化 ----
    output_dir = os.path.dirname(__file__) or "."

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 奖励曲线
    window = min(20, len(all_rewards) // 5) if len(all_rewards) > 5 else 1
    if window > 1:
        smoothed = np.convolve(all_rewards, np.ones(window) / window, mode="valid")
        ax1.plot(smoothed, "b-", alpha=0.8, label=f"Smoothed (w={window})")
    ax1.plot(all_rewards, "b-", alpha=0.2, label="Raw")
    ax1.set_xlabel("Episode")
    ax1.set_ylabel("Total Reward")
    ax1.set_title("PPO Training - Episode Rewards")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 损失曲线
    ax2.plot(all_losses, "r-")
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("Loss")
    ax2.set_title("PPO Training - Loss")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ppo_training.png"), dpi=100, bbox_inches="tight")
    plt.close()
    print(f"\n训练曲线已保存: {os.path.join(output_dir, 'ppo_training.png')}")

    # ---- 测试训练后的策略 ----
    print("\n测试训练后的策略（运行5个episode）:")
    test_rewards = []
    for ep in range(5):
        state = env.reset()
        total_reward = 0
        for _ in range(500):
            state_t = torch.FloatTensor(state).unsqueeze(0).to(device)
            with torch.no_grad():
                action_probs, _ = agent.model(state_t)
            action = action_probs.argmax(dim=1).item()
            state, reward, done = env.step(action)
            total_reward += reward
            if done:
                break
        test_rewards.append(total_reward)
        print(f"  Episode {ep + 1}: Reward = {total_reward:.1f}")

    print(f"\n测试平均奖励: {np.mean(test_rewards):.1f} +/- {np.std(test_rewards):.1f}")
    print("\nPPO演示完成。")


if __name__ == "__main__":
    solve()

```
