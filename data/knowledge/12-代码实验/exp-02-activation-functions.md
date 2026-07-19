# 激活函数对比实验

## 实验类型
参数实验型（param_experiment）

## 难度
中级

## 预计时长
30 分钟

## 实验描述
通过对比 Sigmoid、ReLU、Tanh 三种激活函数在神经网络中的表现，理解激活函数的作用和选择依据。

## 学习目标
- 理解激活函数在神经网络中的作用
- 对比 Sigmoid、ReLU、Tanh 的特性
- 掌握激活函数对训练速度和效果的影响

## 知识点
激活函数, Sigmoid, ReLU, Tanh, 神经网络

## 实验内容

```json
{
  "title": "激活函数对比实验",
  "scenario": "本实验在一个简单的二分类任务上，分别使用 Sigmoid、ReLU 和 Tanh 激活函数训练神经网络，对比它们的训练速度和最终效果。",
  "experiment_mode": "param_experiment",
  "difficulty": "中级",
  "estimated_minutes": 30,
  "learning_objectives": [
    "理解激活函数引入非线性的作用",
    "对比 Sigmoid、ReLU、Tanh 的收敛速度",
    "了解梯度消失问题及其影响"
  ],
  "knowledge_points": ["激活函数", "Sigmoid", "ReLU", "Tanh", "梯度消失"],
  "prerequisite_knowledge": ["Python 基础", "神经网络基本概念", "梯度下降"],
  "steps": [
    {
      "step_id": "step-1",
      "title": "运行 Sigmoid 实验",
      "instruction": "默认使用 Sigmoid 激活函数运行，观察损失曲线和准确率变化。",
      "code_snippet": "activation = 'sigmoid'",
      "expected_result": "损失下降较慢，可能出现梯度消失"
    },
    {
      "step_id": "step-2",
      "title": "切换到 ReLU",
      "instruction": "将激活函数改为 ReLU，重新运行，对比训练速度。",
      "code_snippet": "activation = 'relu'",
      "expected_result": "损失下降更快，训练效率更高"
    },
    {
      "step_id": "step-3",
      "title": "切换到 Tanh",
      "instruction": "将激活函数改为 Tanh，观察其表现。",
      "code_snippet": "activation = 'tanh'",
      "expected_result": "表现介于 Sigmoid 和 ReLU 之间"
    },
    {
      "step_id": "step-4",
      "title": "总结对比",
      "instruction": "对比三种激活函数的训练曲线，总结各自的优缺点。",
      "code_snippet": "",
      "expected_result": "ReLU 训练最快，Sigmoid 可能有梯度消失，Tanh 居中"
    }
  ],
  "starter_code": "\"\"\"\n激活函数对比实验\n对比 Sigmoid、ReLU、Tanh 在简单神经网络中的表现。\n\"\"\"\nimport numpy as np\n\n# ── 可调参数 ──\nactivation = 'sigmoid'  # 可选: sigmoid, relu, tanh\nlearning_rate = 0.1\nn_iters = 500\n\n# ── 生成二分类数据 ──\nnp.random.seed(42)\nn = 200\nX = np.random.randn(n, 2)\ny = (X[:, 0] ** 2 + X[:, 1] ** 2 > 1.5).astype(float).reshape(-1, 1)\n\n# ── 激活函数定义 ──\ndef sigmoid(z):\n    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))\n\ndef sigmoid_deriv(z):\n    s = sigmoid(z)\n    return s * (1 - s)\n\ndef relu(z):\n    return np.maximum(0, z)\n\ndef relu_deriv(z):\n    return (z > 0).astype(float)\n\ndef tanh(z):\n    return np.tanh(z)\n\ndef tanh_deriv(z):\n    return 1 - np.tanh(z) ** 2\n\n# 选择激活函数\nact_funcs = {\n    'sigmoid': (sigmoid, sigmoid_deriv),\n    'relu': (relu, relu_deriv),\n    'tanh': (tanh, tanh_deriv),\n}\nact, act_deriv = act_funcs[activation]\n\n# ── 初始化权重 ──\nnp.random.seed(0)\nW1 = np.random.randn(2, 8) * 0.5\nb1 = np.zeros((1, 8))\nW2 = np.random.randn(8, 1) * 0.5\nb2 = np.zeros((1, 1))\n\n# ── 训练 ──\nfor i in range(n_iters):\n    # 前向传播\n    z1 = X @ W1 + b1\n    a1 = act(z1)\n    z2 = a1 @ W2 + b2\n    a2 = sigmoid(z2)  # 输出层始终用 sigmoid\n\n    # 计算损失\n    loss = -np.mean(y * np.log(a2 + 1e-8) + (1 - y) * np.log(1 - a2 + 1e-8))\n    acc = np.mean((a2 > 0.5) == y)\n\n    # 反向传播\n    dz2 = a2 - y\n    dW2 = a1.T @ dz2 / n\n    db2 = np.mean(dz2, axis=0, keepdims=True)\n    da1 = dz2 @ W2.T\n    dz1 = da1 * act_deriv(z1)\n    dW1 = X.T @ dz1 / n\n    db1 = np.mean(dz1, axis=0, keepdims=True)\n\n    # 更新参数\n    W1 -= learning_rate * dW1\n    b1 -= learning_rate * db1\n    W2 -= learning_rate * dW2\n    b2 -= learning_rate * db2\n\n    if i % 50 == 0:\n        print(f\"epoch {i}, loss = {loss:.6f}, accuracy = {acc:.4f}\")\n\nprint(f\"\\n最终 loss = {loss:.6f}\")\nprint(f\"最终 accuracy = {acc:.4f}\")\nprint(f\"使用激活函数: {activation}\")\n",
  "editable_parameters": [
    {
      "name": "activation",
      "label": "激活函数",
      "default_value": "sigmoid",
      "allowed_values": ["sigmoid", "relu", "tanh"],
      "explanation": "隐藏层使用的激活函数类型"
    },
    {
      "name": "learning_rate",
      "label": "学习率",
      "default_value": 0.1,
      "allowed_values": [0.01, 0.05, 0.1, 0.5],
      "explanation": "参数更新的步长"
    },
    {
      "name": "n_iters",
      "label": "迭代次数",
      "default_value": 500,
      "allowed_values": [200, 500, 1000],
      "explanation": "训练总轮数"
    }
  ],
  "observation_questions": [
    "使用 Sigmoid 时，损失下降的速度如何？是否存在梯度消失的迹象？",
    "切换到 ReLU 后，训练速度有什么变化？",
    "三种激活函数中，哪种在这个任务上表现最好？",
    "为什么输出层始终使用 Sigmoid 而不是 ReLU？"
  ],
  "common_errors": [
    "Sigmoid 输入过大导致数值溢出（已用 clip 处理）",
    "ReLU 可能导致「死亡神经元」—— 某些神经元永远不被激活",
    "忘记区分输出层和隐藏层的激活函数"
  ],
  "expected_phenomena": [
    "Sigmoid：损失下降较慢，可能需要更多迭代",
    "ReLU：损失下降最快，训练效率最高",
    "Tanh：表现介于两者之间，零中心化有优势"
  ],
  "visualization_type": "loss_curve",
  "personalization_reason": "激活函数是神经网络的核心组件，通过对比实验能直观理解不同激活函数的特性"
}
```
