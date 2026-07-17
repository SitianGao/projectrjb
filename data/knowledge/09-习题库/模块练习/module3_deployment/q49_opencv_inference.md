# 评估训练准确率

> 来源模块: module3_deployment
> 原始文件: q49_opencv_inference.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】OpenCV DNN模块加载ONNX模型进行推理
【模块】模块3 - 模型部署
【难度】6
【知识点】cv2.dnn.readNetFromONNX、blobFromImage、Net.forward、
          图像预处理、ONNX推理、OpenCV DNN后端设置
【描述】
本题要求使用OpenCV的DNN模块加载ONNX模型并进行推理。

步骤：
1. 训练一个PyTorch全连接分类模型
2. 导出为ONNX格式
3. 使用cv2.dnn.readNetFromONNX加载模型
4. 使用cv2.dnn.blobFromImage进行数据预处理
5. 前向推理并解析结果
6. 与PyTorch结果对比验证

【输入输出】
- 输入：sklearn digits数据集（8x8图像）
- 输出：打印OpenCV DNN推理结果和PyTorch对比

【要求】
1. 使用cv2.dnn.readNetFromONNX加载ONNX模型
2. 数据预处理：归一化、reshape为网络输入形状
3. 使用net.setInput()和net.forward()进行推理
4. 解析输出得到预测类别和概率
5. 与PyTorch推理结果对比，验证一致性
6. 测试批量推理（多条数据逐条推理）
7. 打印模型各层信息（net.getLayerNames等）

【提示】
- cv2.dnn.blobFromImage用于图像预处理（缩放、归一化、通道交换）
- 对于非图像数据（如特征向量），可直接构造blob（numpy数组）
- blob形状为 (1, C, H, W) 或 (N, C, H, W)
- net.forward()返回numpy数组
- 可使用net.setPreferableBackend设置推理后端
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ==================== 模型定义 ====================

class DigitClassifier(nn.Module):
    """数字分类网络"""

    def __init__(self, input_dim=64, num_classes=10):
        super(DigitClassifier, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        return self.net(x)


# ==================== 数据准备 ====================

def prepare_data():
    """准备digits数据集"""
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

    return train_loader, X_test.astype(np.float32), y_test, scaler


# ==================== 训练与导出 ====================

def train_and_export(train_loader, onnx_path, input_dim=64, epochs=15):
    """训练模型并导出ONNX"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DigitClassifier(input_dim=input_dim).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(epochs):
        model.train()
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

    # 评估训练准确率
    model.eval()
    print(f"  模型训练完成 ({epochs} epochs)")

    # 导出ONNX
    dummy_input = torch.randn(1, input_dim).to(device)
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=12,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )
    print(f"  ONNX模型已导出: {onnx_path}")
    return model


# ==================== OpenCV DNN推理 ====================

def opencv_dnn_inference(onnx_path, X_test):
    """使用OpenCV DNN模块进行推理

    Args:
        onnx_path: ONNX模型路径
        X_test: 测试数据 (N, 64) numpy float32

    Returns:
        predictions: (N,) 预测标签
        probabilities: (N, 10) 预测概率
    """
    # 加载ONNX模型
    net = cv2.dnn.readNetFromONNX(onnx_path)

    # 设置后端（使用CPU）
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    # 打印网络信息
    print(f"\n  OpenCV DNN网络信息:")
    layer_names = net.getLayerNames()
    print(f"    层数: {len(layer_names)}")
    print(f"    层名: {layer_names}")

    # 逐条推理
    all_probs = []
    for i in range(len(X_test)):
        # 构造输入blob: shape (1, 64)
        # 对于全连接网络，输入形状为 (1, input_dim)
        blob = X_test[i:i+1]  # (1, 64)

        # 设置输入
        net.setInput(blob)

        # 前向推理
        output = net.forward()  # (1, 10)

        all_probs.append(output[0])

    probabilities = np.array(all_probs)  # (N, 10)
    predictions = np.argmax(probabilities, axis=1)

    return predictions, probabilities


def opencv_dnn_batch_inference(onnx_path, X_test):
    """使用OpenCV DNN进行批量推理

    Args:
        onnx_path: ONNX模型路径
        X_test: 测试数据 (N, 64) numpy float32

    Returns:
        predictions: (N,) 预测标签
        probabilities: (N, 10) 预测概率
    """
    net = cv2.dnn.readNetFromONNX(onnx_path)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    # 批量推理
    blob = X_test  # (N, 64)
    net.setInput(blob)
    output = net.forward()  # (N, 10)

    probabilities = output
    predictions = np.argmax(probabilities, axis=1)

    return predictions, probabilities


# ==================== PyTorch推理（对比基准） ====================

def pytorch_inference(model, X_test):
    """PyTorch推理作为基准"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()
    with torch.no_grad():
        X_t = torch.FloatTensor(X_test).to(device)
        logits = model(X_t)
        probs = torch.softmax(logits, dim=1).cpu().numpy()
        preds = np.argmax(probs, axis=1)
    return preds, probs


# ==================== 验证与对比 ====================

def compare_results(X_test, y_test, model, onnx_path):
    """对比PyTorch和OpenCV DNN推理结果"""
    import time

    print("\n" + "=" * 60)
    print("【推理结果对比】")
    print("=" * 60)

    # PyTorch推理
    pt_preds, pt_probs = pytorch_inference(model, X_test)
    pt_acc = np.mean(pt_preds == y_test)

    # OpenCV DNN逐条推理
    start = time.time()
    cv_preds, cv_probs = opencv_dnn_inference(onnx_path, X_test)
    cv_time = time.time() - start
    cv_acc = np.mean(cv_preds == y_test)

    # OpenCV DNN批量推理
    start = time.time()
    cv_batch_preds, cv_batch_probs = opencv_dnn_batch_inference(onnx_path, X_test)
    cv_batch_time = time.time() - start
    cv_batch_acc = np.mean(cv_batch_preds == y_test)

    # 概率差异
    prob_diff_single = np.max(np.abs(pt_probs - cv_probs))
    prob_diff_batch = np.max(np.abs(pt_probs - cv_batch_probs))

    # 预测一致性
    agree_single = np.mean(pt_preds == cv_preds)
    agree_batch = np.mean(pt_preds == cv_batch_preds)

    print(f"\n  {'方法':<30} {'准确率':>8} {'最大概率差':>12} "
          f"{'预测一致率':>12} {'耗时':>10}")
    print(f"  {'-'*72}")
    print(f"  {'PyTorch':<30} {pt_acc:>8.4f} {'-':>12} {'-':>12} {'-':>10}")
    print(f"  {'OpenCV DNN (逐条)':<30} {cv_acc:>8.4f} "
          f"{prob_diff_single:>12.2e} {agree_single:>12.4f} {cv_time:>9.3f}s")
    print(f"  {'OpenCV DNN (批量)':<30} {cv_batch_acc:>8.4f} "
          f"{prob_diff_batch:>12.2e} {agree_batch:>12.4f} {cv_batch_time:>9.3f}s")

    # 展示几个具体样本
    print(f"\n  前5个样本预测对比:")
    print(f"  {'真实':>6} {'PyTorch':>8} {'OpenCV':>8} {'PT概率':>15} {'CV概率':>15}")
    for i in range(min(5, len(y_test))):
        pt_top = max(pt_probs[i])
        cv_top = max(cv_probs[i])
        print(f"  {y_test[i]:>6} {pt_preds[i]:>8} {cv_preds[i]:>8} "
              f"{pt_top:>15.4f} {cv_top:>15.4f}")

    # 验证通过条件
    passed = agree_single >= 0.99 and agree_batch >= 0.99
    print(f"\n  验证结果: {'通过' if passed else '未通过'} "
          f"(预测一致率 >= 99%)")


# ==================== 主函数 ====================

def solve():
    onnx_path = "/tmp/digit_cv2dnn.onnx"
    input_dim = 64

    print("=" * 60)
    print("【OpenCV DNN 加载 ONNX 模型推理】")
    print("=" * 60)

    # 1. 准备数据
    print("\n[步骤1] 准备数据...")
    train_loader, X_test, y_test, scaler = prepare_data()
    print(f"  训练样本: {len(train_loader.dataset)}")
    print(f"  测试样本: {len(X_test)}")
    print(f"  特征维度: {input_dim}")

    # 2. 训练并导出
    print("\n[步骤2] 训练模型并导出ONNX...")
    model = train_and_export(train_loader, onnx_path, input_dim=input_dim)

    # 3. OpenCV DNN推理与对比
    print("\n[步骤3] OpenCV DNN推理...")
    compare_results(X_test, y_test, model, onnx_path)

    # 4. 单样本推理示例
    print("\n[步骤4] 单样本推理示例...")
    net = cv2.dnn.readNetFromONNX(onnx_path)
    sample = X_test[0:1]  # 取第一个测试样本
    net.setInput(sample)
    output = net.forward()

    # Softmax计算概率
    exp_out = np.exp(output[0] - np.max(output[0]))
    probs = exp_out / exp_out.sum()
    pred_class = np.argmax(probs)

    print(f"  输入形状: {sample.shape}")
    print(f"  输出形状: {output.shape}")
    print(f"  预测类别: {pred_class} (真实: {y_test[0]})")
    print(f"  预测概率: {probs[pred_class]:.4f}")

    # 5. 模型文件信息
    import os
    if os.path.exists(onnx_path):
        size_kb = os.path.getsize(onnx_path) / 1024
        print(f"\n  ONNX模型文件大小: {size_kb:.2f} KB")

    print("\n" + "=" * 60)
    print("OpenCV DNN推理验证完成！")
    print("=" * 60)


if __name__ == "__main__":
    solve()

```
