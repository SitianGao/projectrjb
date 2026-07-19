# PyTorch 训练循环常见错误诊断

## 实验类型
错误诊断型（error_diagnosis）

## 难度
中级

## 预计时长
20 分钟

## 实验描述
给出一段有典型错误的 PyTorch 训练代码，让学生观察运行现象并找出错误。涵盖忘记清零梯度、忘记切换评估模式等常见问题。

## 学习目标
- 掌握 PyTorch 训练循环的标准写法
- 理解 optimizer.zero_grad() 的作用
- 理解 model.train() 和 model.eval() 的区别

## 知识点
PyTorch, 训练循环, 梯度清零, 训练模式, 评估模式

## 实验内容

```json
{
  "title": "PyTorch 训练循环错误诊断",
  "scenario": "以下代码试图训练一个简单的线性回归模型，但运行后损失值异常。请找出代码中的错误并修正。",
  "experiment_mode": "error_diagnosis",
  "difficulty": "中级",
  "estimated_minutes": 20,
  "learning_objectives": [
    "掌握 PyTorch 训练循环的标准写法",
    "理解 optimizer.zero_grad() 的必要性",
    "了解训练模式和评估模式的区别"
  ],
  "knowledge_points": ["PyTorch", "训练循环", "梯度清零"],
  "prerequisite_knowledge": ["Python 基础", "PyTorch 基础", "梯度下降"],
  "steps": [
    {
      "step_id": "step-1",
      "title": "运行有 bug 的代码",
      "instruction": "先运行原始代码，观察损失值的变化趋势。",
      "code_snippet": "# 直接运行，观察现象",
      "expected_result": "损失值异常，可能出现震荡或不收敛"
    },
    {
      "step_id": "step-2",
      "title": "分析问题",
      "instruction": "仔细阅读代码，找出缺少的关键步骤。提示：注意训练循环中是否每轮都清空了梯度。",
      "code_snippet": "",
      "expected_result": "发现缺少 optimizer.zero_grad()"
    },
    {
      "step_id": "step-3",
      "title": "修正并验证",
      "instruction": "在正确位置添加 optimizer.zero_grad()，重新运行验证。",
      "code_snippet": "optimizer.zero_grad()  # 添加在 loss.backward() 之前",
      "expected_result": "损失值正常下降并收敛"
    }
  ],
  "buggy_code": "\"\"\"\n线性回归训练 —— 但有 bug！\n请找出问题并修正。\n\"\"\"\nimport torch\nimport torch.nn as nn\n\n# 生成数据\nx = torch.linspace(0, 10, 100).unsqueeze(1)\ny = 2 * x + 1 + torch.randn_like(x) * 0.5\n\n# 定义模型\nmodel = nn.Linear(1, 1)\ncriterion = nn.MSELoss()\noptimizer = torch.optim.SGD(model.parameters(), lr=0.01)\n\n# 训练循环\nfor epoch in range(200):\n    output = model(x)\n    loss = criterion(output, y)\n    loss.backward()\n    optimizer.step()\n    \n    if epoch % 50 == 0:\n        print(f'Epoch {epoch}, Loss: {loss.item():.4f}')\n\nprint(f'\\n最终 Loss: {loss.item():.4f}')\nprint(f'学到的权重: {model.weight.item():.4f}')\nprint(f'学到的偏置: {model.bias.item():.4f}')\n",
  "bug_description": "训练循环中缺少 optimizer.zero_grad()。在 PyTorch 中，梯度默认会累加，如果不每轮清零，梯度会不断累积，导致参数更新异常。",
  "fix_hint": "在 loss.backward() 之前添加 optimizer.zero_grad()，清空上一轮计算的梯度。这是 PyTorch 训练循环中非常关键的一步。",
  "observation_questions": [
    "没有 zero_grad() 时，损失值的变化趋势是怎样的？",
    "添加 zero_grad() 后，损失值的变化有什么不同？",
    "为什么 PyTorch 默认累加梯度而不是自动清零？"
  ],
  "common_errors": [
    "忘记调用 optimizer.zero_grad() 导致梯度累积",
    "忘记调用 loss.backward() 导致无法计算梯度",
    "忘记调用 optimizer.step() 导致参数不更新"
  ],
  "expected_phenomena": [
    "缺少 zero_grad()：损失值可能震荡、发散或收敛到异常值",
    "正确代码：损失值稳定下降，最终收敛到较小值"
  ],
  "visualization_type": "loss_curve",
  "personalization_reason": "训练循环是深度学习的日常代码，掌握标准写法能避免大量常见 bug"
}
```
