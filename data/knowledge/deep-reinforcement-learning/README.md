# 深度强化学习知识库索引

## 来源
- 课程：李宏毅 (Hung-yi Lee) — 深度强化学习
- 仓库：https://github.com/Mikoto10032/DeepLearning
- 路径：books/[深度强化学习][Hung-yi Lee]

## 文件清单

### Markdown 知识文件（RAG 检索用）
| 文件 | 主题 | 大小 |
|------|------|------|
| `overview.md` | 课程总览与知识体系 | ~1KB |
| `01-qlearning.md` | Q-Learning 与 DQN | ~3KB |
| `02-actor-critic.md` | Actor-Critic 与 A3C | ~3KB |
| `03-ppo.md` | PPO 近端策略优化 | ~3KB |
| `04-reward-shaping.md` | Reward Shaping 奖励塑形 | ~3KB |
| `05-inverse-rl.md` | 逆向强化学习 IRL | ~3KB |

### PDF 原始讲义
| 文件 | 对应主题 |
|------|----------|
| `QLearning (v2).pdf` | Q-Learning |
| `AC.pdf` | Actor-Critic |
| `PPO (v3).pdf` | PPO |
| `Reward (v3).pdf` | Reward Shaping |
| `IRL (v2).pdf` | Inverse RL |

## 知识结构
```
深度强化学习 (Deep RL)
├── 基础架构：Q-Learning → DQN → Double/Dueling DQN
├── 策略方法：Policy Gradient → Actor-Critic → A2C/A3C
├── 现代算法：TRPO → PPO → GAE
├── 奖励设计：Reward Shaping → Curiosity → Curriculum
└── 逆向学习：IRL → GAIL → RLHF
```

## RAG 使用方法

将此目录导入到 `data/knowledge/` 后，运行：
```bash
python backend/rag/knowledge_loader.py
```
可将 Markdown 文件向量化存入 ChromaDB，供 TutorAgent 和 ResourceAgent 检索使用。
