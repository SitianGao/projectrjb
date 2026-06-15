# 深度强化学习 (Deep Reinforcement Learning)

> 课程来源：李宏毅 (Hung-yi Lee) — 深度强化学习
> 原始仓库：https://github.com/Mikoto10032/DeepLearning
> 整理时间：2026-06

## 课程概述

深度强化学习（Deep Reinforcement Learning, DRL）是将深度学习与强化学习相结合的方法，使智能体能够在复杂环境中通过与环境的交互来学习最优策略。根据李宏毅老师的课程，本知识库涵盖以下核心主题：

## 知识体系

### 1. Q-Learning（Q学习）
- Q-Learning 基础原理
- Deep Q-Network (DQN)
- 经验回放（Experience Replay）
- 目标网络（Target Network）
- 改进算法：Double DQN、Dueling DQN、Prioritized Replay

### 2. Actor-Critic（演员-评论家）
- Policy Gradient 基础
- Actor-Critic 架构
- Advantage Actor-Critic (A2C)
- Asynchronous Advantage Actor-Critic (A3C)
- 与 Q-Learning 的关系

### 3. PPO（近端策略优化）
- Trust Region Policy Optimization (TRPO)
- PPO 的目标函数设计
- Clipping 机制
- PPO2 与 PPO-Clip
- 实际应用中的调参经验

### 4. Reward Shaping（奖励塑形）
- 稀疏奖励问题
- 奖励设计原则
- Curiosity-driven Exploration
- Intrinsic Reward
- 课程学习（Curriculum Learning）

### 5. Inverse Reinforcement Learning（逆向强化学习）
- IRL 基本概念
- 学徒学习（Apprenticeship Learning）
- Maximum Entropy IRL
- Generative Adversarial Imitation Learning (GAIL)
- 从专家演示中学习

## 适用场景

- 游戏 AI（围棋、星际争霸、Dota 2）
- 机器人控制
- 自动驾驶
- 推荐系统
- 对话系统

## 前置知识要求

- 机器学习基础（监督学习、梯度下降）
- 深度学习（神经网络、CNN、RNN）
- 概率论基础
- Python 编程
