# 梯度下降参数实验

## 实验类型
参数实验型（param_experiment）

## 难度
初级

## 预计时长
25 分钟

## 实验描述
通过调整学习率和迭代次数，观察梯度下降算法的收敛行为。学生将对比不同参数下的损失曲线，理解学习率对训练过程的影响。

## 学习目标
- 理解梯度下降的核心原理
- 掌握学习率对收敛速度和稳定性的影响
- 能够通过观察损失曲线判断训练状态

## 知识点
梯度下降, 学习率, 损失函数, 参数更新

## 实验内容

```json
{
  "title": "梯度下降参数实验",
  "scenario": "本实验通过调整学习率等参数，观察梯度下降算法的训练过程和收敛行为。学生将对比不同参数下的损失曲线，理解参数对模型训练的影响。",
  "experiment_mode": "param_experiment",
  "difficulty": "初级",
  "estimated_minutes": 25,
  "learning_objectives": [
    "理解梯度下降的核心原理",
    "掌握学习率对训练收敛的影响",
    "能够通过观察损失曲线判断训练状态"
  ],
  "knowledge_points": ["梯度下降", "学习率", "损失函数"],
  "prerequisite_knowledge": ["Python 基础", "NumPy 基础"],
  "steps": [
    {
      "step_id": "step-1",
      "title": "运行基准实验",
      "instruction": "使用默认参数（学习率=0.01）运行代码，观察损失曲线的整体趋势。",
      "code_snippet": "# 直接点击「运行实验」按钮",
      "expected_result": "损失值随迭代次数增加而下降，最终趋于稳定"
    },
    {
      "step_id": "step-2",
      "title": "增大学习率",
      "instruction": "将学习率从 0.01 改为 0.1，运行实验，观察损失曲线变化。",
      "code_snippet": "learning_rate = 0.1",
      "expected_result": "收敛速度加快，但可能出现轻微震荡",
      "hint": "学习率增大后，每步参数更新的幅度更大"
    },
    {
      "step_id": "step-3",
      "title": "学习率过大实验",
      "instruction": "将学习率改为 1.0，运行实验，观察损失曲线变化。",
      "code_snippet": "learning_rate = 1.0",
      "expected_result": "损失值可能出现剧烈震荡甚至发散",
      "hint": "当学习率过大时，参数可能在最优解两侧来回震荡"
    },
    {
      "step_id": "step-4",
      "title": "对比与总结",
      "instruction": "回顾三次实验的损失曲线，总结学习率对训练的影响规律。",
      "code_snippet": "",
      "expected_result": "较小学习率收敛稳定但慢，较大学习率可能震荡或发散"
    }
  ],
  "starter_code": "\"\"\"\n梯度下降参数实验\n通过调整学习率观察梯度下降的收敛行为。\n\"\"\"\n\nimport numpy as np\n\n# ── 可调参数 ──\nlearning_rate = 0.01\nn_iters = 500\n\n# ── 步骤 1：生成数据 ──\nnp.random.seed(42)\nn_samples = 100\nX = np.random.randn(n_samples, 3)\ny = X[:, 0] * 2.5 + X[:, 1] * (-1.3) + np.random.randn(n_samples) * 0.1\n\n# ── 步骤 2：梯度下降训练 �──\nweights = np.zeros(3)\nfor i in range(n_iters):\n    y_pred = X @ weights\n    loss = np.mean((y_pred - y) ** 2)\n    gradient = (2 / n_samples) * X.T @ (y_pred - y)\n    weights -= learning_rate * gradient\n    if i % 50 == 0:\n        print(f\"epoch {i}, loss = {loss:.6f}\")\n\n# ── 步骤 3：结果 ──\nfinal_pred = X @ weights\nfinal_loss = np.mean((final_pred - y) ** 2)\nprint(f\"\\n最终 loss = {final_loss:.6f}\")\nprint(f\"学习到的权重: {np.round(weights, 4)}\")\n",
  "editable_parameters": [
    {
      "name": "learning_rate",
      "label": "学习率",
      "default_value": 0.01,
      "allowed_values": [0.001, 0.01, 0.1, 0.5, 1.0],
      "explanation": "控制每次参数更新的步长大小"
    },
    {
      "name": "n_iters",
      "label": "迭代次数",
      "default_value": 500,
      "allowed_values": [100, 300, 500, 1000],
      "explanation": "梯度下降的总迭代轮数"
    }
  ],
  "observation_questions": [
    "学习率为 0.01 时，损失曲线的整体形状是什么样的？大约在第几轮开始收敛？",
    "学习率调大到 0.1 后，损失曲线有什么变化？收敛速度和稳定性如何？",
    "学习率为 1.0 时，训练出现了什么现象？为什么会这样？",
    "如果让你选择一个学习率进行实际训练，你会选择哪个？为什么？"
  ],
  "common_errors": [
    "学习率设置过大导致损失值变为 NaN（数值溢出）",
    "迭代次数不足导致模型看起来没有收敛",
    "忘记设置随机种子导致每次运行结果不同，难以对比"
  ],
  "expected_phenomena": [
    "学习率 0.01：损失缓慢但稳定下降，约 300 轮后趋于平稳",
    "学习率 0.1：损失快速下降，约 100 轮后收敛",
    "学习率 1.0：损失剧烈震荡，可能发散到极大值"
  ],
  "visualization_type": "loss_curve",
  "personalization_reason": "梯度下降是深度学习的基础，通过实验观察能帮助建立直觉理解"
}
```
