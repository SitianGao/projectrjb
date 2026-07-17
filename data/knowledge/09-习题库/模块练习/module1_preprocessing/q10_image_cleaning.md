# 生成渐变图像

> 来源模块: module1_preprocessing
> 原始文件: q10_image_cleaning.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】图像数据清洗
【模块】数据预处理
【难度】4
【知识点】OpenCV图像处理、Pillow图像操作、缺失像素插值、噪声平滑、颜色空间转换、尺寸统一
【描述】
在计算机视觉任务中，原始图像数据通常需要进行清洗和标准化处理。本题要求：
1. 对图像进行缺失像素（模拟坏点）插值修复
2. 使用高斯滤波平滑噪声
3. 颜色空间转换（BGR/RGB/Gray/HSV）
4. 将不同尺寸图像统一到指定大小

【要求】
1. 使用numpy生成一张模拟图像（带噪声和坏点）
2. 实现坏点检测与插值修复（使用邻域均值）
3. 使用OpenCV的高斯滤波平滑噪声
4. 实现BGR->RGB、BGR->Gray、BGR->HSV颜色空间转换
5. 实现图像缩放到统一尺寸（支持等比缩放和直接缩放）

【提示】
- OpenCV默认读取为BGR格式，matplotlib显示需要RGB
- 高斯滤波使用cv2.GaussianBlur()
- 坏点可通过检测像素值与邻域均值的偏差来识别
- cv2.resize()可指定插值方法
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import cv2


def generate_test_image(height=200, width=300, seed=42):
    """
    生成一张模拟测试图像，含渐变色彩、噪声和坏点。

    参数:
        height: 图像高度
        width: 图像宽度
        seed: 随机种子

    返回:
        image: BGR格式的模拟图像 (uint8)
        image_clean: 无噪声的原始图像 (uint8)
    """
    np.random.seed(seed)

    # 生成渐变图像
    b = np.linspace(50, 200, width, dtype=np.float64)
    g = np.linspace(100, 255, width, dtype=np.float64)
    r = np.linspace(150, 200, width, dtype=np.float64)

    B = np.tile(b, (height, 1))
    G = np.tile(g, (height, 1))
    R = np.tile(r, (height, 1))

    # 添加垂直渐变
    v_grad = np.linspace(0.7, 1.3, height).reshape(-1, 1)
    B = B * v_grad
    G = G * v_grad
    R = R * v_grad

    image_clean = np.stack([B, G, R], axis=-1)
    image_clean = np.clip(image_clean, 0, 255).astype(np.uint8)

    # 添加高斯噪声
    noise = np.random.normal(0, 15, image_clean.shape)
    image = image_clean.astype(np.float64) + noise

    # 添加坏点（将随机像素设为极端值）
    n_dead = int(height * width * 0.01)  # 1%坏点
    dead_y = np.random.randint(0, height, n_dead)
    dead_x = np.random.randint(0, width, n_dead)
    for y, x in zip(dead_y, dead_x):
        image[y, x] = np.random.choice([0, 255], size=3)

    image = np.clip(image, 0, 255).astype(np.uint8)
    return image, image_clean


def detect_dead_pixels(image, threshold=50):
    """
    检测坏点（与邻域均值差异过大的像素）。

    参数:
        image: 输入图像
        threshold: 坏点判定阈值

    返回:
        dead_mask: 坏点掩码 (bool)
    """
    # 计算每个像素与邻域均值的差异
    kernel = np.ones((3, 3), dtype=np.float64) / 9.0
    blurred = cv2.filter2D(image.astype(np.float64), -1, kernel)
    diff = np.abs(image.astype(np.float64) - blurred)
    diff_gray = np.mean(diff, axis=-1)

    dead_mask = diff_gray > threshold
    return dead_mask


def repair_dead_pixels(image, dead_mask):
    """
    使用邻域均值修复坏点。

    参数:
        image: 输入图像
        dead_mask: 坏点掩码

    返回:
        repaired: 修复后的图像
    """
    repaired = image.copy().astype(np.float64)
    h, w = image.shape[:2]

    # 使用3x3邻域均值修复
    for y, x in zip(*np.where(dead_mask)):
        y_min = max(0, y - 1)
        y_max = min(h, y + 2)
        x_min = max(0, x - 1)
        x_max = min(w, x + 2)
        neighborhood = image[y_min:y_max, x_min:x_max].astype(np.float64)
        repaired[y, x] = np.mean(neighborhood, axis=(0, 1))

    return np.clip(repaired, 0, 255).astype(np.uint8)


def smooth_image(image, kernel_size=5):
    """
    使用高斯滤波平滑图像噪声。

    参数:
        image: 输入图像
        kernel_size: 高斯核大小

    返回:
        smoothed: 平滑后的图像
    """
    smoothed = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    return smoothed


def convert_color_space(image, target='rgb'):
    """
    颜色空间转换。

    参数:
        image: BGR格式图像
        target: 目标空间 ('rgb', 'gray', 'hsv')

    返回:
        converted: 转换后的图像
    """
    if target == 'rgb':
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    elif target == 'gray':
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif target == 'hsv':
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    else:
        raise ValueError(f"不支持的颜色空间: {target}")


def resize_image(image, target_size=(224, 224), method='direct'):
    """
    图像尺寸统一。

    参数:
        image: 输入图像
        target_size: 目标尺寸 (width, height)
        method: 缩放方法 ('direct' 或 'keep_ratio')

    返回:
        resized: 缩放后的图像
    """
    target_w, target_h = target_size

    if method == 'direct':
        # 直接缩放到目标尺寸
        resized = cv2.resize(image, (target_w, target_h),
                             interpolation=cv2.INTER_LINEAR)

    elif method == 'keep_ratio':
        # 等比缩放并填充
        h, w = image.shape[:2]
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized_inner = cv2.resize(image, (new_w, new_h),
                                   interpolation=cv2.INTER_LINEAR)

        # 居中填充
        canvas = np.zeros((target_h, target_w, image.shape[2]), dtype=np.uint8)
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_inner
        resized = canvas

    return resized


def calc_psnr(img1, img2):
    """计算峰值信噪比PSNR。"""
    mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse == 0:
        return float('inf')
    return 10 * np.log10(255.0 ** 2 / mse)


def solve():
    """主函数：演示图像数据清洗流程。"""
    # ========== 1. 生成测试图像 ==========
    print("=" * 60)
    print("1. 生成模拟测试图像")
    print("=" * 60)

    image, image_clean = generate_test_image(height=200, width=300)
    print(f"图像形状: {image.shape}")
    print(f"数据类型: {image.dtype}")
    print(f"像素范围: [{image.min()}, {image.max()}]")

    # ========== 2. 坏点检测与修复 ==========
    print("\n" + "=" * 60)
    print("2. 坏点检测与修复")
    print("=" * 60)

    dead_mask = detect_dead_pixels(image, threshold=50)
    n_dead = dead_mask.sum()
    print(f"检测到坏点数: {n_dead} ({n_dead / dead_mask.size:.2%})")

    image_repaired = repair_dead_pixels(image, dead_mask)
    psnr_before = calc_psnr(image, image_clean)
    psnr_after = calc_psnr(image_repaired, image_clean)
    print(f"修复前PSNR: {psnr_before:.2f} dB")
    print(f"修复后PSNR: {psnr_after:.2f} dB")

    # ========== 3. 噪声平滑 ==========
    print("\n" + "=" * 60)
    print("3. 高斯滤波噪声平滑")
    print("=" * 60)

    for ks in [3, 5, 7]:
        smoothed = smooth_image(image_repaired, kernel_size=ks)
        psnr = calc_psnr(smoothed, image_clean)
        print(f"  高斯核大小={ks}: PSNR={psnr:.2f} dB")

    # 选择最佳核大小
    best_smoothed = smooth_image(image_repaired, kernel_size=5)

    # ========== 4. 颜色空间转换 ==========
    print("\n" + "=" * 60)
    print("4. 颜色空间转换")
    print("=" * 60)

    rgb = convert_color_space(best_smoothed, target='rgb')
    gray = convert_color_space(best_smoothed, target='gray')
    hsv = convert_color_space(best_smoothed, target='hsv')

    print(f"BGR -> RGB:  形状={rgb.shape}, 范围=[{rgb.min()}, {rgb.max()}]")
    print(f"BGR -> Gray: 形状={gray.shape}, 范围=[{gray.min()}, {gray.max()}]")
    print(f"BGR -> HSV:  形状={hsv.shape}, H范围=[{hsv[:,:,0].min()}, {hsv[:,:,0].max()}]")

    # ========== 5. 尺寸统一 ==========
    print("\n" + "=" * 60)
    print("5. 图像尺寸统一")
    print("=" * 60)

    # 生成不同尺寸的图像列表
    sizes = [(180, 240), (200, 300), (224, 224), (150, 250)]
    target = (224, 224)

    print(f"目标尺寸: {target}")
    for h, w in sizes:
        img, _ = generate_test_image(height=h, width=w, seed=42)

        # 直接缩放
        resized_direct = resize_image(img, target, method='direct')
        # 等比缩放
        resized_ratio = resize_image(img, target, method='keep_ratio')

        print(f"\n  原始: ({h}, {w})")
        print(f"    直接缩放 -> {resized_direct.shape}")
        print(f"    等比缩放 -> {resized_ratio.shape}")

    # ========== 6. 完整流水线总结 ==========
    print("\n" + "=" * 60)
    print("6. 完整清洗流水线总结")
    print("=" * 60)

    print("""
图像数据清洗步骤:
  (1) 坏点检测与修复 -> PSNR提升
  (2) 高斯滤波去噪  -> 进一步提升PSNR
  (3) 颜色空间转换  -> 根据任务需求选择
  (4) 尺寸统一      -> 便于批处理和模型输入
""")


if __name__ == "__main__":
    solve()

```
