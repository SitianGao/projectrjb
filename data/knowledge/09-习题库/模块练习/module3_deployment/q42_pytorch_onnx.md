# 创建dummy输入

> 来源模块: module3_deployment
> 原始文件: q42_pytorch_onnx.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】PyTorch模型转换为ONNX并进行推理
【模块】模块3 - 模型部署
【难度】6
【知识点】torch.onnx.export、onnxruntime推理、模型转换验证、
          动态维度、opset_version、模型一致性对比
【描述】
本题要求将一个训练好的PyTorch模型转换为ONNX格式，并使用onnxruntime进行推理，
验证转换前后的输出一致性。

步骤：
1. 定义并训练一个PyTorch全连接模型（用于MNIST风格的手写数字分类）
2. 使用torch.onnx.export将模型导出为ONNX格式
3. 使用onnxruntime加载ONNX模型进行推理
4. 对比PyTorch和ONNX Runtime的输出，验证一致性

【输入输出】
- 输入：使用sklearn生成的人工数据集模拟手写数字分类
- 输出：打印转换信息、推理结果对比和误差分析

【要求】
1. 模型结构：全连接网络 784 -> 256 -> 128 -> 10
2. 使用ReLU激活，Dropout在导出时处于eval模式
3. ONNX导出时设置opset_version=12
4. 支持动态batch维度（dynamic_axes）
5. 使用onnxruntime.InferenceSession加载模型
6. 对比PyTorch和ONNX Runtime的输出，最大误差<1e-5
7. 比较推理速度（单次推理延迟）

【提示】
- torch.onnx.export需要提供dummy_input
- dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}}
- onnxruntime的输入需要是numpy数组，通过input name获取
- 使用np.allclose比较输出，rtol=1e-4, atol=1e-5
=============================
"""

# ========== 参考答案 ==========

import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ==================== 模型定义 ====================

class DigitClassifier(nn.Module):
    """手写数字分类网络 784 -> 256 -> 128 -> 10"""

    def __init__(self, input_dim=64, num_classes=10):
        super(DigitClassifier, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        return self.net(x)


# ==================== 数据准备 ====================

def prepare_data():
    """使用sklearn的digits数据集准备训练数据"""
    digits = load_digits()
    X = digits.data.astype(np.float32)  # (1797, 64)
    y = digits.target.astype(np.int64)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    train_dataset = TensorDataset(
        torch.FloatTensor(X_train), torch.LongTensor(y_train)
    )
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

    return train_loader, X_test, y_test, scaler


# ==================== 训练模型 ====================

def train_model(train_loader, input_dim=64, epochs=15):
    """训练PyTorch模型"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DigitClassifier(input_dim=input_dim).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * batch_x.size(0)
            _, predicted = torch.max(outputs, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()

        if (epoch + 1) % 5 == 0:
            acc = correct / total
            print(f"  Epoch {epoch+1}/{epochs}, Loss: {total_loss/total:.4f}, "
                  f"Acc: {acc:.4f}")

    return model


# ==================== ONNX导出 ====================

def export_to_onnx(model, onnx_path, input_dim=64):
    """将PyTorch模型导出为ONNX格式

    Args:
        model: PyTorch模型
        onnx_path: ONNX文件保存路径
        input_dim: 输入维度

    Returns:
        onnx_path: 保存路径
    """
    model.eval()
    device = next(model.parameters()).device

    # 创建dummy输入
    dummy_input = torch.randn(1, input_dim).to(device)

    # 导出ONNX
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,        # 导出模型参数
        opset_version=12,          # ONNX算子集版本
        do_constant_folding=True,  # 常量折叠优化
        input_names=["input"],     # 输入名称
        output_names=["output"],   # 输出名称
        dynamic_axes={             # 动态维度
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )

    print(f"  ONNX模型已保存到: {onnx_path}")
    return onnx_path


# ==================== ONNX Runtime推理 ====================

def inference_onnx(onnx_path, X_test):
    """使用onnxruntime进行推理

    Args:
        onnx_path: ONNX模型路径
        X_test: 测试数据 (numpy数组)

    Returns:
        outputs: 模型输出 (numpy数组)
    """
    import onnxruntime as ort

    # 创建推理会话
    session = ort.InferenceSession(onnx_path)

    # 获取输入名称
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    print(f"  ONNX输入名称: {input_name}")
    print(f"  ONNX输出名称: {output_name}")
    print(f"  ONNX输入形状: {session.get_inputs()[0].shape}")
    print(f"  ONNX输出形状: {session.get_outputs()[0].shape}")

    # 推理
    outputs = session.run(
        [output_name],
        {input_name: X_test.astype(np.float32)},
    )[0]

    return outputs


# ==================== 验证与对比 ====================

def compare_outputs(model, onnx_path, X_test, y_test):
    """对比PyTorch和ONNX Runtime的输出

    Args:
        model: PyTorch模型
        onnx_path: ONNX模型路径
        X_test: 测试数据
        y_test: 测试标签
    """
    device = next(model.parameters()).device
    model.eval()

    # PyTorch推理
    with torch.no_grad():
        X_torch = torch.FloatTensor(X_test).to(device)
        start_time = time.time()
        for _ in range(100):
            pytorch_outputs = model(X_torch)
        pytorch_time = (time.time() - start_time) / 100
        pytorch_outputs = pytorch_outputs.cpu().numpy()

    # ONNX Runtime推理
    start_time = time.time()
    for _ in range(100):
        onnx_outputs = inference_onnx(onnx_path, X_test)
    onnx_time = (time.time() - start_time) / 100

    # 只取最后一次的onnx输出用于对比
    onnx_outputs = inference_onnx(onnx_path, X_test)

    # 计算误差
    abs_diff = np.abs(pytorch_outputs - onnx_outputs)
    max_diff = abs_diff.max()
    mean_diff = abs_diff.mean()

    # 预测结果一致性
    pytorch_pred = np.argmax(pytorch_outputs, axis=1)
    onnx_pred = np.argmax(onnx_outputs, axis=1)
    pred_agreement = np.mean(pytorch_pred == onnx_pred)

    # 准确率
    pytorch_acc = np.mean(pytorch_pred == y_test)
    onnx_acc = np.mean(onnx_pred == y_test)

    print("\n" + "=" * 60)
    print("【PyTorch vs ONNX Runtime 对比结果】")
    print("=" * 60)
    print(f"  最大绝对误差:      {max_diff:.2e}")
    print(f"  平均绝对误差:      {mean_diff:.2e}")
    print(f"  输出一致性(np.allclose, rtol=1e-4): "
          f"{'通过' if np.allclose(pytorch_outputs, onnx_outputs, rtol=1e-4, atol=1e-5) else '未通过'}")
    print(f"  预测结果一致率:    {pred_agreement:.4f}")
    print(f"  PyTorch准确率:     {pytorch_acc:.4f}")
    print(f"  ONNX Runtime准确率: {onnx_acc:.4f}")
    print(f"  PyTorch推理延迟:   {pytorch_time*1000:.3f} ms")
    print(f"  ONNX Runtime推理延迟: {onnx_time*1000:.3f} ms")
    print(f"  推理加速比:        {pytorch_time/onnx_time:.2f}x")

    # 验证通过条件
    passed = max_diff < 1e-5
    print(f"\n  转换验证: 最大误差 {max_diff:.2e} < 1e-5 → "
          f"{'通过' if passed else '未通过'}")

    return passed


def verify_onnx_model(onnx_path):
    """使用onnx库验证ONNX模型的有效性"""
    try:
        import onnx
        model = onnx.load(onnx_path)
        onnx.checker.check_model(model)
        print("  ONNX模型验证: 通过（模型格式正确）")

        # 打印模型信息
        print(f"  IR版本: {model.ir_version}")
        print(f"  算子集版本: {model.opset_import[0].version}")
        print(f"  生产者: {model.producer_name}")
    except ImportError:
        print("  注意: onnx库未安装，跳过模型验证")
    except Exception as e:
        print(f"  ONNX模型验证失败: {e}")


# ==================== 主函数 ====================

def solve():
    onnx_path = "/tmp/digit_classifier.onnx"
    input_dim = 64  # sklearn digits数据集特征维度

    print("=" * 60)
    print("【PyTorch -> ONNX 转换与推理验证】")
    print("=" * 60)

    # 1. 准备数据
    print("\n[步骤1] 准备数据...")
    train_loader, X_test, y_test, scaler = prepare_data()
    print(f"  训练样本数: {len(train_loader.dataset)}")
    print(f"  测试样本数: {len(X_test)}")
    print(f"  特征维度: {input_dim}")

    # 2. 训练模型
    print("\n[步骤2] 训练PyTorch模型...")
    model = train_model(train_loader, input_dim=input_dim, epochs=15)

    # 3. 导出ONNX
    print("\n[步骤3] 导出ONNX模型...")
    export_to_onnx(model, onnx_path, input_dim=input_dim)

    # 4. 验证ONNX模型
    print("\n[步骤4] 验证ONNX模型格式...")
    verify_onnx_model(onnx_path)

    # 5. 对比推理结果
    print("\n[步骤5] 对比PyTorch与ONNX Runtime推理结果...")
    compare_outputs(model, onnx_path, X_test, y_test)

    print("\n" + "=" * 60)
    print("PyTorch -> ONNX 转换验证完成！")
    print("=" * 60)


if __name__ == "__main__":
    solve()

```
