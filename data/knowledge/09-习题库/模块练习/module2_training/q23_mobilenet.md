# 逐通道卷积: 每个通道独立卷积

> 来源模块: module2_training
> 原始文件: q23_mobilenet.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】MobileNet深度可分离卷积：PyTorch实现
【模块】模型训练与评估
【难度】7
【知识点】深度可分离卷积、逐通道卷积(Depthwise)、逐点卷积(Pointwise)、
         MobileNet、计算量优化、参数量对比
【描述】
MobileNet通过深度可分离卷积(Depthwise Separable Convolution)大幅减少
计算量和参数量。深度可分离卷积将标准卷积分解为：
1. Depthwise卷积：每个输入通道独立卷积
2. Pointwise卷积(1x1卷积)：通道间信息融合

标准卷积计算量: H*W * C_in * C_out * K*K
深度可分离卷积计算量: H*W * C_in * K*K + H*W * C_in * C_out

本题要求用PyTorch实现深度可分离卷积模块，构建简化版MobileNet，
并与标准卷积网络对比参数量和精度。

【要求】
1. 实现DepthwiseSeparableConv类（包含Depthwise + Pointwise + BN + ReLU）
2. 构建简化版MobileNet（4层深度可分离卷积 + 全连接层）
3. 构建相同通道数的标准卷积网络作为对照
4. 对比两个网络的参数量和FLOPs（浮点运算量）
5. 在CIFAR-10上训练两个模型（3个epoch），对比精度
6. 打印参数量对比表格

【提示】
- Depthwise卷积: groups=in_channels, out_channels=in_channels
- Pointwise卷积: kernel_size=1, 负责通道融合
- 使用thop或手动计算FLOPs
- MobileNet的核心思想是用深度可分离卷积替代标准卷积
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


class DepthwiseSeparableConv(nn.Module):
    """深度可分离卷积模块"""

    def __init__(self, in_channels, out_channels, stride=1):
        super(DepthwiseSeparableConv, self).__init__()
        # 逐通道卷积: 每个通道独立卷积
        self.depthwise = nn.Conv2d(
            in_channels, in_channels,
            kernel_size=3, stride=stride, padding=1,
            groups=in_channels, bias=False
        )
        self.bn1 = nn.BatchNorm2d(in_channels)
        # 逐点卷积: 1x1卷积融合通道
        self.pointwise = nn.Conv2d(
            in_channels, out_channels,
            kernel_size=1, stride=1, padding=0, bias=False
        )
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU6(inplace=True)

    def forward(self, x):
        x = self.relu(self.bn1(self.depthwise(x)))
        x = self.relu(self.bn2(self.pointwise(x)))
        return x


class StandardConv(nn.Module):
    """标准卷积模块（用于对比）"""

    def __init__(self, in_channels, out_channels, stride=1):
        super(StandardConv, self).__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels,
            kernel_size=3, stride=stride, padding=1, bias=False
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU6(inplace=True)

    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))


class SimpleMobileNet(nn.Module):
    """简化版MobileNet"""

    def __init__(self, num_classes=10):
        super(SimpleMobileNet, self).__init__()
        self.features = nn.Sequential(
            # 初始标准卷积
            StandardConv(3, 32, stride=1),       # 32x32
            DepthwiseSeparableConv(32, 64, stride=1),   # 32x32
            DepthwiseSeparableConv(64, 128, stride=2),  # 16x16
            DepthwiseSeparableConv(128, 128, stride=1), # 16x16
            DepthwiseSeparableConv(128, 256, stride=2), # 8x8
            DepthwiseSeparableConv(256, 256, stride=1), # 8x8
        )
        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = self.avg_pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


class StandardConvNet(nn.Module):
    """标准卷积网络（与MobileNet相同通道配置，用于对比）"""

    def __init__(self, num_classes=10):
        super(StandardConvNet, self).__init__()
        self.features = nn.Sequential(
            StandardConv(3, 32, stride=1),
            StandardConv(32, 64, stride=1),
            StandardConv(64, 128, stride=2),
            StandardConv(128, 128, stride=1),
            StandardConv(128, 256, stride=2),
            StandardConv(256, 256, stride=1),
        )
        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = self.avg_pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


def count_params(model):
    """统计模型参数量"""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def estimate_flops(model, input_size=(1, 3, 32, 32)):
    """估算模型FLOPs（简化版，仅卷积层）"""
    total_flops = 0
    hooks = []

    def conv_hook(module, input, output):
        nonlocal total_flops
        if isinstance(module, nn.Conv2d):
            batch_size = input[0].size(0)
            output_h = output.size(2)
            output_w = output.size(3)
            kernel_h, kernel_w = module.kernel_size
            in_channels = module.in_channels // module.groups
            out_channels = module.out_channels
            flops = batch_size * output_h * output_w * in_channels * out_channels * kernel_h * kernel_w
            total_flops += flops

    for module in model.modules():
        if isinstance(module, nn.Conv2d):
            hooks.append(module.register_forward_hook(conv_hook))

    device = next(model.parameters()).device
    dummy = torch.randn(input_size).to(device)
    model.eval()
    with torch.no_grad():
        model(dummy)

    for hook in hooks:
        hook.remove()

    return total_flops


def train_and_evaluate(model, train_loader, test_loader, device,
                       n_epochs=3, name="Model"):
    """训练并评估模型"""
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(n_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for data, target in train_loader:
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

        train_acc = 100. * correct / total

    # 最终测试
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
    print(f"  [{name}] 最终测试精度: {test_acc:.2f}%")
    return test_acc


def solve():
    device = torch.device("cpu")

    # ---- 1. 数据加载 ----
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465),
                             (0.2470, 0.2435, 0.2616)),
    ])

    print("加载CIFAR-10数据集...")
    train_dataset = datasets.CIFAR10(root="./data", train=True,
                                      download=True, transform=transform)
    test_dataset = datasets.CIFAR10(root="./data", train=False,
                                     download=True, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True,
                              num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=100, shuffle=False,
                             num_workers=0)

    # ---- 2. 创建模型 ----
    mobilenet = SimpleMobileNet(num_classes=10).to(device)
    stdnet = StandardConvNet(num_classes=10).to(device)

    # ---- 3. 参数量与FLOPs对比 ----
    mobile_params, _ = count_params(mobilenet)
    std_params, _ = count_params(stdnet)
    mobile_flops = estimate_flops(mobilenet)
    std_flops = estimate_flops(stdnet)

    print("\n" + "=" * 60)
    print("参数量与计算量对比")
    print("=" * 60)
    print(f"{'指标':<25} {'MobileNet':>15} {'标准卷积':>15}")
    print("-" * 56)
    print(f"{'参数量':<25} {mobile_params:>15,} {std_params:>15,}")
    print(f"{'FLOPs(单张图片)':<25} {mobile_flops:>15,} {std_flops:>15,}")
    print(f"{'参数量压缩比':<25} {std_params/mobile_params:>14.2f}x {'---':>15}")
    print(f"{'计算量压缩比':<25} {std_flops/mobile_flops:>14.2f}x {'---':>15}")

    # ---- 4. 训练对比 ----
    print("\n训练模型中...")
    n_epochs = 3
    mobile_acc = train_and_evaluate(
        mobilenet, train_loader, test_loader, device,
        n_epochs=n_epochs, name="MobileNet"
    )
    std_acc = train_and_evaluate(
        stdnet, train_loader, test_loader, device,
        n_epochs=n_epochs, name="标准卷积网络"
    )

    # ---- 5. 最终对比 ----
    print("\n" + "=" * 60)
    print("最终对比结果")
    print("=" * 60)
    print(f"{'指标':<25} {'MobileNet':>15} {'标准卷积':>15}")
    print("-" * 56)
    print(f"{'参数量':<25} {mobile_params:>15,} {std_params:>15,}")
    print(f"{'测试精度':<25} {mobile_acc:>14.2f}% {std_acc:>14.2f}%")
    print(f"{'精度差':<25} {std_acc - mobile_acc:>14.2f}% {'---':>15}")

    # ---- 6. 深度可分离卷积单元验证 ----
    print("\n" + "=" * 60)
    print("深度可分离卷积 vs 标准卷积（单层对比）")
    print("=" * 60)
    ds_conv = DepthwiseSeparableConv(64, 128)
    st_conv = StandardConv(64, 128)
    ds_params = sum(p.numel() for p in ds_conv.parameters())
    st_params = sum(p.numel() for p in st_conv.parameters())
    print(f"  输入: 64通道, 输出: 128通道, 卷积核: 3x3")
    print(f"  深度可分离卷积参数: {ds_params:,}")
    print(f"  标准卷积参数:       {st_params:,}")
    print(f"  压缩比:             {st_params/ds_params:.2f}x")


if __name__ == "__main__":
    solve()

```
