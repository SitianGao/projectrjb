# x: (batch, 1, 28, 28)

> 来源模块: module2_training
> 原始文件: q21_lenet5.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】LeNet-5 CNN：PyTorch实现与MNIST手写数字识别
【模块】模型训练与评估
【难度】4
【知识点】CNN、卷积层、池化层、全连接层、LeNet-5、MNIST、PyTorch
【描述】
LeNet-5是Yann LeCun提出的经典卷积神经网络，是最早的CNN之一。
本题要求使用PyTorch实现LeNet-5网络，并在MNIST手写数字数据集上
进行训练和测试。

网络结构：
- 输入: 1x28x28 (MNIST灰度图像)
- Conv1: 1->6, kernel=5x5, padding=2 -> 6x28x28 -> Pool(2x2) -> 6x14x14
- Conv2: 6->16, kernel=5x5 -> 16x5x5 (after pool)
- FC1: 400 -> 120
- FC2: 120 -> 84
- FC3: 84 -> 10

【要求】
1. 使用PyTorch实现LeNet-5模型类
2. 加载MNIST数据集（使用torchvision.datasets）
3. 使用交叉熵损失和SGD优化器训练模型
4. 训练3个epoch（小规模训练演示）
5. 打印每个epoch的训练损失和测试精度
6. 可视化部分预测结果
7. 计算最终测试精度和混淆矩阵

【提示】
- 使用torchvision.datasets.MNIST下载数据集
- 使用torchvision.transforms.ToTensor进行预处理
- batch_size建议64，学习率0.01
- 使用model.eval()切换到评估模式
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np


class LeNet5(nn.Module):
    """LeNet-5 卷积神经网络"""

    def __init__(self):
        super(LeNet5, self).__init__()
        # 卷积层
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=6,
                               kernel_size=5, padding=2)
        self.conv2 = nn.Conv2d(in_channels=6, out_channels=16,
                               kernel_size=5)
        # 池化层
        self.pool = nn.AvgPool2d(kernel_size=2, stride=2)
        # 全连接层
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)
        # 激活函数
        self.activation = nn.Tanh()

    def forward(self, x):
        # x: (batch, 1, 28, 28)
        x = self.activation(self.conv1(x))   # (batch, 6, 28, 28)
        x = self.pool(x)                      # (batch, 6, 14, 14)
        x = self.activation(self.conv2(x))    # (batch, 16, 10, 10)
        x = self.pool(x)                      # (batch, 16, 5, 5)
        x = x.view(x.size(0), -1)             # (batch, 400)
        x = self.activation(self.fc1(x))      # (batch, 120)
        x = self.activation(self.fc2(x))      # (batch, 84)
        x = self.fc3(x)                       # (batch, 10)
        return x


def solve():
    # 设备选择
    device = torch.device("cpu")

    # ---- 1. 数据加载 ----
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    train_dataset = datasets.MNIST(root="./data", train=True,
                                    download=True, transform=transform)
    test_dataset = datasets.MNIST(root="./data", train=False,
                                   download=True, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=1000, shuffle=False)

    print(f"训练集大小: {len(train_dataset)}")
    print(f"测试集大小: {len(test_dataset)}")

    # ---- 2. 模型、损失函数、优化器 ----
    model = LeNet5().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)

    # 打印模型结构
    print("\n模型结构:")
    print(model)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"总参数量: {total_params:,}")

    # ---- 3. 训练 ----
    n_epochs = 3
    print(f"\n开始训练 ({n_epochs} epochs)...")

    for epoch in range(n_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)

            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            pred = output.argmax(dim=1)
            correct += pred.eq(target).sum().item()
            total += target.size(0)

            if (batch_idx + 1) % 200 == 0:
                print(f"  Epoch {epoch+1}/{n_epochs} "
                      f"[{batch_idx+1}/{len(train_loader)}] "
                      f"损失: {loss.item():.4f} "
                      f"训练精度: {100.*correct/total:.2f}%")

        # ---- 4. 测试 ----
        model.eval()
        test_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for data, target in test_loader:
                data, target = data.to(device), target.to(device)
                output = model(data)
                test_loss += criterion(output, target).item()
                pred = output.argmax(dim=1)
                correct += pred.eq(target).sum().item()
                total += target.size(0)

        test_loss /= len(test_loader)
        acc = 100. * correct / total
        print(f"  >> Epoch {epoch+1} 测试结果: "
              f"损失={test_loss:.4f}, 精度={acc:.2f}% "
              f"({correct}/{total})")

    # ---- 5. 最终评估与混淆矩阵 ----
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for data, target in test_loader:
            data = data.to(device)
            output = model(data)
            pred = output.argmax(dim=1)
            all_preds.extend(pred.cpu().numpy())
            all_targets.extend(target.numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    # 混淆矩阵
    n_classes = 10
    conf_matrix = np.zeros((n_classes, n_classes), dtype=int)
    for t, p in zip(all_targets, all_preds):
        conf_matrix[t][p] += 1

    print("\n混淆矩阵:")
    print("     " + " ".join(f" {i:2d}" for i in range(10)))
    for i in range(10):
        row = " ".join(f"{conf_matrix[i][j]:3d}" for j in range(10))
        print(f"  {i}: {row}")

    # 每类精度
    print("\n各类别精度:")
    for i in range(10):
        class_acc = conf_matrix[i][i] / conf_matrix[i].sum() * 100
        print(f"  数字 {i}: {class_acc:.2f}%")

    final_acc = (all_preds == all_targets).mean() * 100
    print(f"\n最终测试精度: {final_acc:.2f}%")


if __name__ == "__main__":
    solve()

```
