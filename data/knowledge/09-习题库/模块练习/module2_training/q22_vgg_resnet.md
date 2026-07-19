# Block 1

> 来源模块: module2_training
> 原始文件: q22_vgg_resnet.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】VGG和ResNet：PyTorch实现简化版经典网络
【模块】模型训练与评估
【难度】6
【知识点】VGG网络、ResNet、残差块(Residual Block)、批归一化、CIFAR-10、PyTorch
【描述】
VGG和ResNet是深度学习中两个里程碑式的网络架构。VGG通过堆叠小卷积核(3x3)
构建深层网络，ResNet通过残差连接解决深层网络的梯度消失问题。
本题要求使用PyTorch实现简化版VGG和ResNet，在CIFAR-10上训练和对比。

简化版VGG结构（适配CIFAR-10 32x32输入）:
- Conv块1: Conv(3->64)->BN->ReLU->Conv(64->64)->BN->ReLU->MaxPool
- Conv块2: Conv(64->128)->BN->ReLU->Conv(128->128)->BN->ReLU->MaxPool
- Conv块3: Conv(128->256)->BN->ReLU->Conv(256->256)->BN->ReLU->MaxPool
- FC: 256*4*4 -> 256 -> 10

简化版ResNet结构:
- 初始卷积: Conv(3->64, 3x3, padding=1) -> BN -> ReLU
- 残差块层1: 2个残差块(64通道)
- 残差块层2: 2个残差块(128通道, stride=2下采样)
- 残差块层3: 2个残差块(256通道, stride=2下采样)
- 全局平均池化 -> FC(256 -> 10)

【要求】
1. 实现SimplifiedVGG类
2. 实现残差块ResidualBlock类和SimplifiedResNet类
3. 在CIFAR-10上分别训练两个模型（3个epoch）
4. 对比两个模型的参数量、训练精度、测试精度
5. 绘制训练损失曲线对比图
6. 打印模型参数量和精度对比表格

【提示】
- 残差块核心: out = F(x) + x, 其中F(x)是两层卷积的残差映射
- 当输入输出维度不同时，使用1x1卷积进行shortcut映射
- CIFAR-10图像大小为32x32，比ImageNet的224x224小很多
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np


# ============ 简化版 VGG ============

class SimplifiedVGG(nn.Module):
    """简化版VGG网络，适配CIFAR-10"""

    def __init__(self, num_classes=10):
        super(SimplifiedVGG, self).__init__()

        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 32->16
            # Block 2
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 16->8
            # Block 3
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 8->4
        )

        self.classifier = nn.Sequential(
            nn.Linear(256 * 4 * 4, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


# ============ 简化版 ResNet ============

class ResidualBlock(nn.Module):
    """残差块"""

    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels,
                               kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels,
                               kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

        # shortcut: 如果输入输出维度不同，使用1x1卷积调整
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        residual = self.shortcut(x)
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual  # 残差连接
        out = self.relu(out)
        return out


class SimplifiedResNet(nn.Module):
    """简化版ResNet，适配CIFAR-10"""

    def __init__(self, num_classes=10):
        super(SimplifiedResNet, self).__init__()
        self.in_channels = 64

        # 初始卷积层
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1,
                               padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)

        # 残差块层
        self.layer1 = self._make_layer(64, num_blocks=2, stride=1)
        self.layer2 = self._make_layer(128, num_blocks=2, stride=2)
        self.layer3 = self._make_layer(256, num_blocks=2, stride=2)

        # 全局平均池化 + 全连接
        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, num_classes)

    def _make_layer(self, out_channels, num_blocks, stride):
        layers = []
        layers.append(ResidualBlock(self.in_channels, out_channels, stride))
        self.in_channels = out_channels
        for _ in range(1, num_blocks):
            layers.append(ResidualBlock(out_channels, out_channels, stride=1))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.layer1(x)  # 32x32
        x = self.layer2(x)  # 16x16
        x = self.layer3(x)  # 8x8
        x = self.avg_pool(x)  # 1x1
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


def count_parameters(model):
    """计算模型参数量"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def train_model(model, train_loader, test_loader, criterion, optimizer,
                device, n_epochs=3, model_name="Model"):
    """训练模型并记录损失"""
    train_losses = []
    test_accs = []

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

        avg_loss = running_loss / len(train_loader)
        train_acc = 100. * correct / total
        train_losses.append(avg_loss)

        # 测试
        model.eval()
        test_correct = 0
        test_total = 0
        with torch.no_grad():
            for data, target in test_loader:
                data, target = data.to(device), target.to(device)
                output = model(data)
                pred = output.argmax(dim=1)
                test_correct += pred.eq(target).sum().item()
                test_total += target.size(0)

        test_acc = 100. * test_correct / test_total
        test_accs.append(test_acc)
        print(f"  [{model_name}] Epoch {epoch+1}/{n_epochs} "
              f"损失={avg_loss:.4f} 训练精度={train_acc:.2f}% "
              f"测试精度={test_acc:.2f}%")

    return train_losses, test_accs


def solve():
    device = torch.device("cpu")

    # ---- 1. 数据加载 ----
    transform = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465),
                             (0.2470, 0.2435, 0.2616)),
    ])

    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465),
                             (0.2470, 0.2435, 0.2616)),
    ])

    print("加载CIFAR-10数据集...")
    train_dataset = datasets.CIFAR10(root="./data", train=True,
                                      download=True, transform=transform)
    test_dataset = datasets.CIFAR10(root="./data", train=False,
                                     download=True, transform=test_transform)

    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True,
                              num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=100, shuffle=False,
                             num_workers=0)

    print(f"训练集: {len(train_dataset)}, 测试集: {len(test_dataset)}")

    # ---- 2. 模型初始化 ----
    vgg = SimplifiedVGG(num_classes=10).to(device)
    resnet = SimplifiedResNet(num_classes=10).to(device)

    vgg_params = count_parameters(vgg)
    resnet_params = count_parameters(resnet)

    print(f"\n模型参数量:")
    print(f"  SimplifiedVGG:  {vgg_params:,}")
    print(f"  SimplifiedResNet: {resnet_params:,}")

    # ---- 3. 训练 ----
    criterion = nn.CrossEntropyLoss()
    n_epochs = 3

    print(f"\n训练 VGG ({n_epochs} epochs)...")
    vgg_optimizer = optim.Adam(vgg.parameters(), lr=0.001)
    vgg_losses, vgg_accs = train_model(
        vgg, train_loader, test_loader, criterion,
        vgg_optimizer, device, n_epochs, "VGG"
    )

    print(f"\n训练 ResNet ({n_epochs} epochs)...")
    resnet_optimizer = optim.Adam(resnet.parameters(), lr=0.001)
    resnet_losses, resnet_accs = train_model(
        resnet, train_loader, test_loader, criterion,
        resnet_optimizer, device, n_epochs, "ResNet"
    )

    # ---- 4. 对比结果 ----
    print("\n" + "=" * 60)
    print("对比结果")
    print("=" * 60)
    print(f"{'指标':<20} {'VGG':>15} {'ResNet':>15}")
    print("-" * 52)
    print(f"{'参数量':<20} {vgg_params:>15,} {resnet_params:>15,}")
    print(f"{'最终测试精度':<20} {vgg_accs[-1]:>14.2f}% {resnet_accs[-1]:>14.2f}%")
    print(f"{'最终训练损失':<20} {vgg_losses[-1]:>15.4f} {resnet_losses[-1]:>15.4f}")


if __name__ == "__main__":
    solve()

```
