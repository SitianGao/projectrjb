# Reinforcement Learning: Foundations and Core Algorithms

## The RL Framework

Reinforcement Learning (RL) is the study of learning to make sequential decisions through interaction with an environment. The fundamental loop:

- The **Agent** observes the current **state** $s_t$ of the environment.
- It selects an **action** $a_t$ according to its **policy** $\pi$.
- The environment transitions to a new state $s_{t+1}$ and produces a scalar **reward** $r_t$.
- The agent's goal is to maximize the cumulative (discounted) sum of rewards: $G_t = \sum_{k=0}^\infty \gamma^k r_{t+k}$.

The discount factor $\gamma \in [0, 1]$ controls how much future rewards are valued relative to immediate ones.

---

## Markov Decision Process (MDP)

The environment is formalized as an MDP defined by the tuple:

$$\mathcal{M} = (S, A, P, R, \gamma)$$

- $S$: set of states.
- $A$: set of actions.
- $P(s' \mid s, a)$: state transition probability (Markov property — the future depends only on the current state and action, not the history).
- $R(s, a, s')$: reward function.
- $\gamma$: discount factor.

---

## Policy, Value, and Q-Functions

**Policy** $\pi(a \mid s)$: the probability of selecting action $a$ in state $s$. A deterministic policy maps $s \to a$.

**State-value function** $V^\pi(s)$: expected return starting from state $s$ and following $\pi$ thereafter:

$$V^\pi(s) = \mathbb{E}_\pi\left[\sum_{t=0}^\infty \gamma^t r_t \;\middle|\; s_0 = s\right]$$

**Action-value (Q) function** $Q^\pi(s, a)$: expected return starting from $s$, taking action $a$, then following $\pi$:

$$Q^\pi(s, a) = \mathbb{E}_\pi\left[\sum_{t=0}^\infty \gamma^t r_t \;\middle|\; s_0 = s, a_0 = a\right]$$

---

## The Bellman Equation

The Bellman equation expresses the recursive relationship between the value of a state and the values of successor states:

$$V^\pi(s) = \sum_{a \in A} \pi(a \mid s) \sum_{s' \in S} P(s' \mid s, a) \left[ R(s, a, s') + \gamma V^\pi(s') \right]$$

For the Q-function:

$$Q^\pi(s, a) = \sum_{s'} P(s' \mid s, a) \left[ R(s, a, s') + \gamma \sum_{a'} \pi(a' \mid s') Q^\pi(s', a') \right]$$

The **Bellman optimality equation** for the optimal value function $V^*$, which is the maximum expected return achievable from each state:

$$V^*(s) = \max_{a} \sum_{s'} P(s' \mid s, a) \left[ R(s, a, s') + \gamma V^*(s') \right]$$

---

## Value Iteration and Policy Iteration

These are the two fundamental planning methods when the MDP model $(P, R)$ is known.

### Policy Iteration

Alternate between two steps until convergence:

1. **Policy Evaluation:** Compute $V^\pi$ for the current policy by solving the Bellman equation (iterative or direct).
2. **Policy Improvement:** For each state, set $\pi(s) = \arg\max_a \sum_{s'} P(s' \mid s, a)[R + \gamma V^\pi(s')]$.

Policy iteration converges in a finite number of steps for finite MDPs.

### Value Iteration

Combine evaluation and improvement into a single update:

$$V_{k+1}(s) = \max_a \sum_{s'} P(s' \mid s, a) \left[ R(s, a, s') + \gamma V_k(s') \right]$$

Converges to $V^*$ as $k \to \infty$. More computationally efficient per iteration than policy iteration.

---

## Q-Learning: Off-Policy TD Control

Q-learning (Watkins, 1989) learns the optimal Q-function directly from experience without a model of the environment. It is an **off-policy** algorithm — it learns about the optimal policy regardless of the behavior policy used for exploration.

**Update rule (tabular):**

$$Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]$$

- $\alpha$: learning rate.
- The term in brackets is the **TD error** — the difference between the bootstrapped target and the current estimate.
- Uses $\max_{a'} Q(s', a')$ (the best action according to current estimates) regardless of the action actually taken next — this is what makes it off-policy.

---

## SARSA: On-Policy TD Control

SARSA (State-Action-Reward-State-Action) is the on-policy counterpart to Q-learning:

$$Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma Q(s', a') - Q(s, a) \right]$$

The key difference: it uses $Q(s', a')$ where $a'$ is the action **actually taken** by the current policy, not the maximizing action. This makes SARSA more conservative — it accounts for the exploration policy's suboptimal choices, which can be safer (e.g., avoiding risky paths that a Q-learning agent would optimistically navigate).

---

## Exploration vs. Exploitation

A fundamental trade-off: exploit known good actions to get reward now, or explore unknown actions to discover better strategies.

### $\epsilon$-Greedy

With probability $1 - \epsilon$, take the greedy action $\arg\max_a Q(s, a)$. With probability $\epsilon$, take a random action. Simple but explores uniformly and inefficiently.

### Softmax (Boltzmann) Exploration

Sample actions from a probability distribution:

$$\pi(a \mid s) = \frac{\exp(Q(s, a) / \tau)}{\sum_{a'} \exp(Q(s, a') / \tau)}$$

The temperature $\tau$ controls randomness: high $\tau$ is more exploratory, low $\tau$ is more greedy. $\tau$ is typically annealed over time.

### UCB (Upper Confidence Bound)

For bandit problems, select the action with the highest upper confidence bound:

$$a_t = \arg\max_a \left[ Q_t(a) + c \sqrt{\frac{\ln t}{N_t(a)}} \right]$$

The bonus term encourages trying actions with high uncertainty (few visits). In deep RL, similar principles appear in methods like Noisy Networks.

---

## Deep Q-Network (DQN)

Mnih et al. (2015) combined Q-learning with deep neural networks, achieving superhuman performance on Atari games. Two key innovations make this stable:

### Experience Replay

Store transitions $(s, a, r, s')$ in a replay buffer. During training, sample random mini-batches from this buffer. This:
- Breaks correlation between consecutive samples (making training closer to supervised i.i.d. assumptions).
- Allows each experience to be reused many times, improving sample efficiency.

### Target Network

Maintain a separate network $Q_{\text{target}}$ with parameters $\theta^-$ that are updated less frequently (e.g., every $C$ steps, or via Polyak averaging). The TD target uses the target network:

$$\text{target} = r + \gamma \max_{a'} Q_{\text{target}}(s', a')$$

This stabilizes training by preventing the target from changing at every step — which otherwise creates a "moving target" problem akin to chasing one's own tail.

---

## Policy Gradient and REINFORCE

Value-based methods learn $Q$ and derive a policy (e.g., $\epsilon$-greedy). Policy gradient methods directly optimize the policy parameters $\theta$ to maximize expected return $J(\theta)$.

### Policy Gradient Theorem

$$\nabla_\theta J(\theta) = \mathbb{E}_\pi \left[ \nabla_\theta \log \pi_\theta(a \mid s) \cdot Q^\pi(s, a) \right]$$

### REINFORCE (Monte Carlo Policy Gradient)

Uses the actual return $G_t$ as an unbiased (but high-variance) estimate of $Q^\pi$:

$$\theta \leftarrow \theta + \alpha \sum_{t} \nabla_\theta \log \pi_\theta(a_t \mid s_t) \cdot G_t$$

Collect a full episode, compute returns, and update. High variance but simple. A baseline $b(s)$ (typically $V(s)$) is subtracted from $G_t$ to reduce variance without introducing bias.

---

## Actor-Critic Methods

Actor-Critic combines value-based and policy-based approaches:
- **Actor ($\pi_\theta$):** The policy — decides which action to take. Updated via policy gradient.
- **Critic ($V_\phi$ or $Q_\phi$):** The value function — evaluates how good the actor's actions were. Updated via TD learning.

The TD error $\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)$ serves as an advantage estimate for the actor update:

$$\theta \leftarrow \theta + \alpha \nabla_\theta \log \pi_\theta(a_t \mid s_t) \cdot \delta_t$$

---

## Key Algorithm Evolution

| Algorithm | Year | Key Innovation |
|-----------|------|----------------|
| **DQN** | 2015 | Deep nets + experience replay + target network |
| **A3C** | 2016 | Asynchronous parallel actor-critic; entropy bonus for exploration |
| **PPO** | 2017 | Clipped surrogate objective; stable, sample-efficient, widely used |
| **SAC** | 2018 | Maximum entropy RL with automatic temperature tuning; state-of-the-art for continuous control |

PPO is the default choice for most modern RL applications due to its simplicity and robustness. SAC excels in continuous action spaces (robotics, locomotion).

---

## Applications

- **Game playing:** AlphaGo/AlphaZero (superhuman Go, chess, shogi), Atari, Dota 2, StarCraft II.
- **Robotics:** Dexterous manipulation, locomotion, drone control, sim-to-real transfer.
- **Recommendation systems:** Sequential recommendation as an MDP; maximize long-term user engagement.
- **Autonomous driving:** Decision-making under uncertainty in highway and urban scenarios.
- **Large language models:** RLHF (RL from Human Feedback) fine-tunes LLMs using PPO with a reward model trained on human preferences.
- **Finance:** Portfolio optimization, trade execution, market making.

---

## OpenAI Gym Example (Q-Learning on FrozenLake)

```python
import gymnasium as gym
import numpy as np

env = gym.make("FrozenLake-v1", is_slippery=False)
Q = np.zeros([env.observation_space.n, env.action_space.n])
alpha, gamma, epsilon = 0.1, 0.99, 0.1

for episode in range(10000):
    state, _ = env.reset()
    done = False
    while not done:
        if np.random.random() < epsilon:
            action = env.action_space.sample()
        else:
            action = np.argmax(Q[state])
        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        # Q-learning update
        Q[state, action] += alpha * (
            reward + gamma * np.max(Q[next_state]) - Q[state, action]
        )
        state = next_state

print("Trained Q-table:")
print(Q)
```
