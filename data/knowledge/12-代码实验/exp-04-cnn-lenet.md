# CNN 基础模型实验（LeNet-5 简化版）

## 实验类型
代码实验型（code_experiment）

## 难度
中级

## 预计时长
30 分钟

## 实验描述
通过搭建一个简化的 LeNet-5 卷积神经网络，理解 CNN 的基本结构和前向传播过程。学生将使用 PyTorch 手动搭建卷积层、池化层和全连接层，观察特征图的变化，并在 MNIST 数据集上训练和测试模型。

## 学习目标
- 理解 CNN 的基本组成：卷积层、池化层、全连接层
- 掌握 PyTorch 搭建 CNN 模型的方法
- 理解卷积操作对输入特征图的影响
- 能够在真实数据集上训练和评估 CNN 模型

## 知识点
CNN, 卷积神经网络, LeNet-5, PyTorch, 卷积层, 池化层, 全连接层, MNIST

## 前置知识
Python 基础, PyTorch 张量操作, 神经网络基本概念

## 实验内容

```json
{
  "title": "CNN 基础模型实验（LeNet-5 简化版）",
  "scenario": "本实验通过搭建简化的 LeNet-5 模型，理解 CNN 的基本结构。学生将使用 PyTorch 定义卷积层、池化层和全连接层，在 MNIST 手写数字数据集上训练并测试模型性能。",
  "experiment_mode": "param_experiment",
  "difficulty": "中级",
  "estimated_minutes": 30,
  "learning_objectives": [
    "理解 CNN 的基本组成结构",
    "掌握 PyTorch 搭建 CNN 的方法",
    "理解卷积操作对特征图的影响",
    "能够在 MNIST 上训练和评估 CNN"
  ],
  "knowledge_points": ["CNN", "卷积层", "池化层", "全连接层", "LeNet-5", "PyTorch"],
  "prerequisite_knowledge": ["Python 基础", "PyTorch 张量操作", "神经网络基本概念"],
  "steps": [
    {
      "step_id": "step-1",
      "title": "导入必要的库",
      "instruction": "首先导入 PyTorch 和数据处理相关的库。",
      "code_snippet": "import torch\nimport torch.nn as nn\nimport torch.optim as optim\nimport torchvision\nimport torchvision.transforms as transforms\n\n# 设置设备\ndevice = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\nprint(f'使用设备: {device}')",
      "expected_result": "输出使用的设备（CPU 或 CUDA）",
      "hint": "如果没有 GPU，PyTorch 会自动使用 CPU"
    },
    {
      "step_id": "step-2",
      "title": "加载 MNIST 数据集",
      "instruction": "加载 MNIST 手写数字数据集，并进行预处理（归一化、转为张量）。",
      "code_snippet": "# 数据预处理\ntransform = transforms.Compose([\n    transforms.ToTensor(),\n    transforms.Normalize((0.1307,), (0.3081,))  # MNIST 的均值和标准差\n])\n\n# 加载训练集和测试集\ntrain_dataset = torchvision.datasets.MNIST(\n    root='./data', train=True, download=True, transform=transform\n)\ntest_dataset = torchvision.datasets.MNIST(\n    root='./data', train=False, download=True, transform=transform\n)\n\n# 创建数据加载器\ntrain_loader = torch.utils.data.DataLoader(train_dataset, batch_size=64, shuffle=True)\ntest_loader = torch.utils.data.DataLoader(test_dataset, batch_size=1000, shuffle=False)\n\nprint(f'训练集大小: {len(train_dataset)}')\nprint(f'测试集大小: {len(test_dataset)}')",
      "expected_result": "输出训练集大小 60000，测试集大小 10000",
      "hint": "MNIST 数据集会自动下载到 ./data 目录"
    },
    {
      "step_id": "step-3",
      "title": "定义简化版 LeNet-5 模型",
      "instruction": "定义一个简化版的 LeNet-5 CNN 模型，包含 2 个卷积层、2 个池化层和 3 个全连接层。",
      "code_snippet": "class SimpleLeNet(nn.Module):\n    def __init__(self):\n        super(SimpleLeNet, self).__init__()\n        # 第一个卷积层: 1个输入通道（灰度图），6个输出通道，5x5卷积核\n        self.conv1 = nn.Conv2d(1, 6, kernel_size=5)\n        # 第二个卷积层: 6个输入通道，16个输出通道，5x5卷积核\n        self.conv2 = nn.Conv2d(6, 16, kernel_size=5)\n        # 最大池化层\n        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)\n        # 全连接层\n        self.fc1 = nn.Linear(16 * 4 * 4, 120)\n        self.fc2 = nn.Linear(120, 84)\n        self.fc3 = nn.Linear(84, 10)  # 10个数字类别\n    \n    def forward(self, x):\n        # 卷积 -> ReLU -> 池化\n        x = self.pool(torch.relu(self.conv1(x)))  # 输出: 6x12x12\n        x = self.pool(torch.relu(self.conv2(x)))  # 输出: 16x4x4\n        # 展平\n        x = x.view(-1, 16 * 4 * 4)\n        # 全连接层\n        x = torch.relu(self.fc1(x))\n        x = torch.relu(self.fc2(x))\n        x = self.fc3(x)\n        return x\n\n# 创建模型实例\nmodel = SimpleLeNet().to(device)\nprint(model)",
      "expected_result": "输出模型结构，显示各层的参数",
      "hint": "注意输入图像尺寸为 28x28，经过两次卷积和池化后变为 4x4"
    },
    {
      "step_id": "step-4",
      "title": "定义损失函数和优化器",
      "instruction": "使用交叉熵损失函数和 SGD 优化器。",
      "code_snippet": "# 损失函数\n criterion = nn.CrossEntropyLoss()\n\n# 优化器\noptimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)\n\nprint('损失函数: CrossEntropyLoss')\nprint('优化器: SGD (lr=0.01, momentum=0.9)')",
      "expected_result": "确认损失函数和优化器已定义",
      "hint": "交叉熵损失函数适用于多分类问题"
    },
    {
      "step_id": "step-5",
      "title": "训练模型",
      "instruction": "在训练集上训练模型，观察训练过程中的损失变化。",
      "code_snippet": "# 训练模型\nnum_epochs = 3\nfor epoch in range(num_epochs):\n    running_loss = 0.0\n    for i, (images, labels) in enumerate(train_loader):\n        images, labels = images.to(device), labels.to(device)\n        \n        # 前向传播\n        outputs = model(images)\n        loss = criterion(outputs, labels)\n        \n        # 反向传播和优化\n        optimizer.zero_grad()\n        loss.backward()\n        optimizer.step()\n        \n        running_loss += loss.item()\n        \n        # 每 200 个 batch 打印一次损失\n        if (i + 1) % 200 == 0:\n            print(f'Epoch [{epoch+1}/{num_epochs}], Step [{i+1}/{len(train_loader)}], Loss: {loss.item():.4f}')\n    \n    # 每个 epoch 结束后打印平均损失\n    avg_loss = running_loss / len(train_loader)\n    print(f'Epoch [{epoch+1}/{num_epochs}] 完成, 平均损失: {avg_loss:.4f}')\n\nprint('训练完成!')",
      "expected_result": "输出每个 epoch 的损失值，损失应该逐渐减小",
      "hint": "损失值应该随着训练逐渐减小，如果损失不下降可能是学习率设置不当"
    },
    {
      "step_id": "step-6",
      "title": "测试模型性能",
      "instruction": "在测试集上评估模型的准确率。",
      "code_snippet": "# 测试模型\nmodel.eval()\ncorrect = 0\ntotal = 0\nwith torch.no_grad():\n    for images, labels in test_loader:\n        images, labels = images.to(device), labels.to(device)\n        outputs = model(images)\n        _, predicted = torch.max(outputs.data, 1)\n        total += labels.size(0)\n        correct += (predicted == labels).sum().item()\n\naccuracy = 100 * correct / total\nprint(f'测试集准确率: {accuracy:.2f}%')",
      "expected_result": "输出测试集准确率，通常应该在 98% 以上",
      "hint": "MNIST 是一个相对简单的数据集，好的模型应该能达到 99% 以上的准确率"
    }
  ],
  "expected_outcomes": [
    "理解 CNN 的基本结构（卷积层、池化层、全连接层）",
    "掌握使用 PyTorch 搭建 CNN 的方法",
    "理解卷积操作对输入特征图的影响",
    "能够在真实数据集上训练和评估 CNN 模型"
  ],
  "extensions": [
    "尝试修改卷积核大小，观察对模型性能的影响",
    "增加卷积层的数量，观察模型复杂度和性能的关系",
    "尝试不同的优化器（如 Adam）和学习率",
    "在 CIFAR-10 数据集上测试模型"
  ]
}
```

## 参考资料
- LeNet-5 原始论文: LeCun et al., 1998
- PyTorch 官方文档: https://pytorch.org/docs/stable/nn.html
- MNIST 数据集: http://yann.lecun.com/exdb/mnist/
