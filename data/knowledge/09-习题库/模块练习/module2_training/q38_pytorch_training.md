# 转为PyTorch张量

> 来源模块: module2_training
> 原始文件: q38_pytorch_training.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】PyTorch完整训练流程实践
【模块】模块2 - 模型训练
【难度】5
【知识点】nn.Module构建网络、nn.Sequential构建网络、SGD/Adam优化器、StepLR学习率调度、
          state_dict保存加载、torch.save/load、训练循环、验证循环
【描述】
本题要求使用PyTorch完成一个完整的模型训练流程，包括网络构建、优化器配置、
学习率调度、模型训练与验证、以及模型的保存与加载。

给定一个二分类任务（使用sklearn生成的人工数据集），需要：

1. 分别使用 nn.Module 和 nn.Sequential 两种方式构建相同结构的全连接网络
2. 使用 SGD 和 Adam 两种优化器分别训练
3. 使用 StepLR 学习率调度器
4. 记录每个epoch的训练损失和验证准确率
5. 使用 state_dict 方式保存和加载模型
6. 使用完整模型方式（torch.save/load）保存和加载
7. 验证加载后的模型输出与原模型一致

【输入输出】
- 输入：sklearn.datasets.make_classification生成的二分类数据，1000个样本，20个特征
- 输出：打印训练过程信息，最终验证加载模型的输出一致性结果

【要求】
1. 实现 ModuleNet(nn.Module) 和 SequentialNet 两个网络类，结构为 20->64->32->2
2. 使用ReLU激活函数，隐藏层之间使用Dropout(0.2)
3. 训练epoch数为10，batch_size=32
4. StepLR初始lr=0.01，step_size=3，gamma=0.5
5. 加载模型后验证输出与原模型完全一致（误差<1e-6）
6. 代码需完整可运行

【提示】
- 使用torch.no_grad()进行推理
- 保存时可用 torch.save(model.state_dict(), path) 和 torch.save(model, path)
- 加载state_dict时需要先创建模型实例再调用load_state_dict
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split


# ---------- 方式一：nn.Module 构建网络 ----------
class ModuleNet(nn.Module):
    """使用 nn.Module 方式构建的全连接网络"""

    def __init__(self, input_dim=20, hidden1=64, hidden2=32, num_classes=2):
        super(ModuleNet, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden1)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.2)
        self.fc2 = nn.Linear(hidden1, hidden2)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.2)
        self.fc3 = nn.Linear(hidden2, num_classes)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.dropout1(x)
        x = self.fc2(x)
        x = self.relu2(x)
        x = self.dropout2(x)
        x = self.fc3(x)
        return x


# ---------- 方式二：nn.Sequential 构建网络 ----------
class SequentialNet(nn.Module):
    """使用 nn.Sequential 方式构建的全连接网络"""

    def __init__(self, input_dim=20, hidden1=64, hidden2=32, num_classes=2):
        super(SequentialNet, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden1),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden2, num_classes),
        )

    def forward(self, x):
        return self.net(x)


def get_dataloaders():
    """生成二分类数据并返回DataLoader"""
    X, y = make_classification(
        n_samples=1000, n_features=20, n_informative=10,
        n_redundant=5, random_state=42
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    # 转为PyTorch张量
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.LongTensor(y_train)
    X_val_t = torch.FloatTensor(X_val)
    y_val_t = torch.LongTensor(y_val)

    train_dataset = TensorDataset(X_train_t, y_train_t)
    val_dataset = TensorDataset(X_val_t, y_val_t)

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

    return train_loader, val_loader, X_val_t, y_val_t


def train_one_epoch(model, train_loader, criterion, optimizer, device):
    """训练一个epoch"""
    model.train()
    total_loss = 0.0
    for batch_x, batch_y in train_loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        optimizer.zero_grad()
        outputs = model(batch_x)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch_x.size(0)
    return total_loss / len(train_loader.dataset)


def evaluate(model, val_loader, device):
    """在验证集上评估准确率"""
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            outputs = model(batch_x)
            _, predicted = torch.max(outputs, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
    return correct / total


def train_model(model, train_loader, val_loader, optimizer_name="adam",
                lr=0.01, epochs=10, device="cpu"):
    """完整训练流程"""
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()

    # 选择优化器
    if optimizer_name == "sgd":
        optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    else:
        optimizer = optim.Adam(model.parameters(), lr=lr)

    # StepLR 学习率调度器
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

    history = {"train_loss": [], "val_acc": [], "lr": []}

    for epoch in range(epochs):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_acc = evaluate(model, val_loader, device)
        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["val_acc"].append(val_acc)
        history["lr"].append(current_lr)

        print(
            f"  Epoch {epoch+1:2d}/{epochs} | "
            f"Loss: {train_loss:.4f} | "
            f"Val Acc: {val_acc:.4f} | "
            f"LR: {current_lr:.6f}"
        )

    return model, history


def verify_state_dict_save_load(model, test_input, device):
    """使用 state_dict 方式保存和加载模型，并验证一致性"""
    save_path = "/tmp/model_state_dict.pt"
    model.eval()
    with torch.no_grad():
        original_output = model(test_input.to(device))

    # 保存 state_dict
    torch.save(model.state_dict(), save_path)

    # 创建新模型并加载 state_dict
    loaded_model = ModuleNet().to(device)
    loaded_model.load_state_dict(torch.load(save_path, map_location=device))
    loaded_model.eval()

    with torch.no_grad():
        loaded_output = loaded_model(test_input.to(device))

    max_diff = (original_output - loaded_output).abs().max().item()
    consistent = max_diff < 1e-6
    print(f"  state_dict 保存加载验证: 最大误差 = {max_diff:.2e}, "
          f"一致性 = {'通过' if consistent else '未通过'}")
    return consistent


def verify_full_model_save_load(model, test_input, device):
    """使用完整模型方式保存和加载，并验证一致性"""
    save_path = "/tmp/model_full.pt"
    model.eval()
    with torch.no_grad():
        original_output = model(test_input.to(device))

    # 保存完整模型
    torch.save(model, save_path)

    # 加载完整模型
    loaded_model = torch.load(save_path, map_location=device)
    loaded_model.eval()

    with torch.no_grad():
        loaded_output = loaded_model(test_input.to(device))

    max_diff = (original_output - loaded_output).abs().max().item()
    consistent = max_diff < 1e-6
    print(f"  完整模型保存加载验证: 最大误差 = {max_diff:.2e}, "
          f"一致性 = {'通过' if consistent else '未通过'}")
    return consistent


def solve():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")

    # 准备数据
    train_loader, val_loader, X_val, y_val = get_dataloaders()
    test_input = X_val[:5]  # 取5个样本用于保存加载验证

    # ========== 1. 使用 nn.Module + Adam 训练 ==========
    print("\n[1] ModuleNet + Adam 训练:")
    model_module = ModuleNet()
    model_module, hist_adam = train_model(
        model_module, train_loader, val_loader,
        optimizer_name="adam", lr=0.01, epochs=10, device=device
    )

    # ========== 2. 使用 nn.Sequential + SGD 训练 ==========
    print("\n[2] SequentialNet + SGD 训练:")
    model_seq = SequentialNet()
    model_seq, hist_sgd = train_model(
        model_seq, train_loader, val_loader,
        optimizer_name="sgd", lr=0.01, epochs=10, device=device
    )

    # ========== 3. 验证 state_dict 保存加载 ==========
    print("\n[3] 模型保存与加载验证:")
    verify_state_dict_save_load(model_module, test_input, device)

    # ========== 4. 验证完整模型保存加载 ==========
    verify_full_model_save_load(model_module, test_input, device)

    # ========== 5. 汇总结果 ==========
    print("\n" + "=" * 50)
    print("训练结果汇总:")
    print(f"  ModuleNet + Adam   最终验证准确率: {hist_adam['val_acc'][-1]:.4f}")
    print(f"  SequentialNet + SGD 最终验证准确率: {hist_sgd['val_acc'][-1]:.4f}")
    print("=" * 50)


if __name__ == "__main__":
    solve()

```
