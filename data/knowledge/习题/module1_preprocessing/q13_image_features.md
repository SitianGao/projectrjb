# 画一些几何图形

> 来源模块: module1_preprocessing
> 原始文件: q13_image_features.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】图像特征提取：HOG/SIFT传统特征 + CNN卷积特征
【模块】数据预处理
【难度】6
【知识点】HOG特征、SIFT特征、预训练CNN、PyTorch torchvision、特征提取
【描述】
图像特征提取是计算机视觉的核心步骤。传统方法使用手工设计的特征（HOG、SIFT），
深度学习方法使用CNN自动学习特征。

本题要求：
1. 使用OpenCV提取HOG（方向梯度直方图）特征
2. 使用OpenCV提取SIFT特征描述子
3. 使用PyTorch预训练的ResNet18提取CNN卷积特征
4. 对比不同特征维度和提取时间

【要求】
1. 生成一张模拟测试图像
2. 使用OpenCV的HOGDescriptor提取HOG特征
3. 使用OpenCV的SIFT_create检测关键点并提取描述子
4. 加载torchvision预训练的ResNet18，移除全连接层，提取卷积特征
5. 统计并对比各方法的特征维度和计算时间

【提示】
- HOG特征适用于行人检测等任务，维度与图像大小和cell大小有关
- SIFT具有尺度不变性，每个关键点生成128维描述子
- 预训练CNN特征通用性强，适合迁移学习
=============================
"""

# ========== 参考答案 ==========

import time
import numpy as np
import cv2
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image


def generate_test_image(size=224):
    """
    生成一张包含几何形状的测试图像。

    参数:
        size: 图像尺寸

    返回:
        image: BGR格式的测试图像
    """
    np.random.seed(42)
    image = np.ones((size, size, 3), dtype=np.uint8) * 240

    # 画一些几何图形
    # 矩形
    cv2.rectangle(image, (30, 30), (100, 100), (0, 0, 200), 2)
    # 圆
    cv2.circle(image, (170, 70), 40, (0, 200, 0), 2)
    # 三角形
    pts = np.array([[110, 130], [70, 200], [150, 200]], np.int32)
    cv2.fillPoly(image, [pts], (200, 100, 0))
    # 线条
    cv2.line(image, (10, 210), (210, 10), (100, 0, 255), 2)

    # 添加一些噪声
    noise = np.random.normal(0, 10, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return image


def extract_hog_features(image):
    """
    提取HOG特征。

    参数:
        image: BGR格式图像

    返回:
        hog_features: HOG特征向量
        hog_image: HOG可视化图像
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 调整图像大小为HOG标准输入
    resized = cv2.resize(gray, (128, 128))

    # HOG参数
    win_size = (128, 128)
    block_size = (16, 16)
    block_stride = (8, 8)
    cell_size = (8, 8)
    n_bins = 9

    hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, n_bins)
    hog_features = hog.compute(resized)

    # HOG可视化（简化：使用梯度幅度图）
    gx = cv2.Sobel(resized, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(resized, cv2.CV_32F, 0, 1)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    hog_vis = (mag / mag.max() * 255).astype(np.uint8)

    return hog_features.flatten(), hog_vis


def extract_sift_features(image, max_keypoints=50):
    """
    提取SIFT特征。

    参数:
        image: BGR格式图像
        max_keypoints: 最大关键点数

    返回:
        keypoints: 关键点列表
        descriptors: 描述子矩阵 (n_keypoints, 128)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 创建SIFT检测器
    sift = cv2.SIFT_create(nfeatures=max_keypoints)
    keypoints, descriptors = sift.detectAndCompute(gray, None)

    return keypoints, descriptors


def extract_cnn_features(image, model, device='cpu'):
    """
    使用预训练CNN提取卷积特征。

    参数:
        image: BGR格式图像
        model: PyTorch模型
        device: 计算设备

    返回:
        features: 特征向量（全局平均池化后）
        feature_map: 特征图（池化前）
    """
    # 预处理
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    input_tensor = transform(pil_image).unsqueeze(0).to(device)

    with torch.no_grad():
        features = model(input_tensor)

    # 全局平均池化
    if len(features.shape) == 4:
        feature_map = features
        features_pooled = torch.nn.functional.adaptive_avg_pool2d(
            features, (1, 1)
        ).squeeze()
    else:
        feature_map = None
        features_pooled = features.squeeze()

    return features_pooled.cpu().numpy(), feature_map


def create_feature_extractor():
    """创建CNN特征提取器（ResNet18，移除全连接层）。"""
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

    # 移除最后的全连接层和平均池化层，提取卷积特征
    # 保留到最后一层卷积 (layer4)
    feature_extractor = nn.Sequential(*list(model.children())[:-2])  # 去掉avgpool和fc
    feature_extractor.eval()

    return feature_extractor


def solve():
    """主函数：演示图像特征提取。"""
    device = 'cpu'

    # ========== 1. 生成测试图像 ==========
    print("=" * 60)
    print("1. 生成测试图像")
    print("=" * 60)

    image = generate_test_image(size=224)
    print(f"图像形状: {image.shape}")
    print(f"图像类型: {image.dtype}")

    # ========== 2. HOG特征提取 ==========
    print("\n" + "=" * 60)
    print("2. HOG特征提取")
    print("=" * 60)

    t0 = time.time()
    hog_features, hog_vis = extract_hog_features(image)
    t_hog = time.time() - t0

    print(f"特征维度: {hog_features.shape}")
    print(f"特征范围: [{hog_features.min():.4f}, {hog_features.max():.4f}]")
    print(f"特征均值: {hog_features.mean():.4f}")
    print(f"提取时间: {t_hog * 1000:.2f} ms")
    print(f"HOG可视化图形状: {hog_vis.shape}")

    # HOG维度计算说明
    print("\n  HOG维度计算:")
    print(f"    窗口: 128x128, Block: 16x16, Block步长: 8, Cell: 8x8, Bins: 9")
    blocks_x = (128 - 16) // 8 + 1
    blocks_y = (128 - 16) // 8 + 1
    total_blocks = blocks_x * blocks_y
    dims = total_blocks * 2 * 2 * 9  # 每个block有2x2个cell
    print(f"    总block数: {blocks_x}x{blocks_y} = {total_blocks}")
    print(f"    理论维度: {total_blocks} x 2x2x9 = {dims}")

    # ========== 3. SIFT特征提取 ==========
    print("\n" + "=" * 60)
    print("3. SIFT特征提取")
    print("=" * 60)

    t0 = time.time()
    keypoints, descriptors = extract_sift_features(image, max_keypoints=50)
    t_sift = time.time() - t0

    print(f"检测到关键点数: {len(keypoints)}")
    if descriptors is not None:
        print(f"描述子形状: {descriptors.shape}")
        print(f"每个描述子维度: {descriptors.shape[1]}")
        print(f"描述子范围: [{descriptors.min()}, {descriptors.max()}]")
    print(f"提取时间: {t_sift * 1000:.2f} ms")

    # 关键点信息
    print("\n  前5个关键点信息:")
    for i, kp in enumerate(keypoints[:5]):
        print(f"    关键点{i}: 位置({kp.pt[0]:.1f}, {kp.pt[1]:.1f}), "
              f"尺度={kp.size:.1f}, 角度={kp.angle:.1f}")

    # ========== 4. CNN特征提取 ==========
    print("\n" + "=" * 60)
    print("4. 预训练CNN (ResNet18) 特征提取")
    print("=" * 60)

    feature_extractor = create_feature_extractor()
    feature_extractor = feature_extractor.to(device)

    t0 = time.time()
    cnn_features, feature_map = extract_cnn_features(image, feature_extractor, device)
    t_cnn = time.time() - t0

    print(f"CNN特征提取器: ResNet18 (去除FC层)")
    print(f"卷积特征图形状: {feature_map.shape if feature_map is not None else 'N/A'}")
    print(f"全局平均池化后特征维度: {cnn_features.shape}")
    print(f"特征范围: [{cnn_features.min():.4f}, {cnn_features.max():.4f}]")
    print(f"特征均值: {cnn_features.mean():.4f}")
    print(f"提取时间: {t_cnn * 1000:.2f} ms")

    # ========== 5. 特征对比 ==========
    print("\n" + "=" * 60)
    print("5. 特征方法对比")
    print("=" * 60)

    sift_dim = descriptors.shape[0] * descriptors.shape[1] if descriptors is not None else 0
    cnn_dim = cnn_features.shape[0] if feature_map is not None else 0

    print(f"\n{'方法':<15} {'特征维度':<15} {'提取时间(ms)':<15} {'特点'}")
    print("-" * 70)
    print(f"{'HOG':<15} {hog_features.shape[0]:<15} {t_hog*1000:<15.2f} {'梯度方向统计，适合刚性物体'}")
    print(f"{'SIFT':<15} {sift_dim:<15} {t_sift*1000:<15.2f} {'尺度不变，适合特征匹配'}")
    print(f"{'CNN(ResNet18)':<15} {cnn_dim:<15} {t_cnn*1000:<15.2f} {'深层语义特征，通用性强'}")

    print("\n说明:")
    print("  HOG: 固定维度向量，适合分类任务")
    print("  SIFT: 可变数量的128维描述子，适合图像匹配和拼接")
    print("  CNN: 高维语义特征，适合迁移学习和端到端训练")


if __name__ == "__main__":
    solve()

```
