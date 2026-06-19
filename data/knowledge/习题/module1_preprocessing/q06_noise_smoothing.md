# 确定窗口边界（边界处自动截断）

> 来源模块: module1_preprocessing
> 原始文件: q06_noise_smoothing.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】噪声信号平滑处理
【模块】数据预处理
【难度】3
【知识点】移动平均、中值滤波、Savitzky-Golay滤波、scipy.signal
【描述】
传感器采集的数据通常含有噪声，需要通过滤波平滑处理。
本题对一段含噪声的正弦信号分别使用以下方法进行平滑：
1. 移动平均（Moving Average）：用滑动窗口内数据的均值替代
2. 中值滤波（Median Filter）：用滑动窗口内数据的中位数替代
3. Savitzky-Golay滤波：基于局部多项式最小二乘拟合的平滑方法

【要求】
1. 生成一段含高斯噪声的正弦信号（采样点≥200）
2. 实现手动移动平均滤波
3. 实现手动中值滤波
4. 使用scipy的savgol_filter进行S-G滤波
5. 计算各方法的均方误差（MSE）和信噪比（SNR），对比平滑效果

【提示】
- 移动平均窗口越大，平滑效果越强，但信号失真也越大
- 中值滤波对脉冲噪声效果特别好
- S-G滤波在平滑的同时能较好地保留信号形状
=============================
"""

# ========== 参考答案 ==========

import numpy as np
from scipy.signal import savgol_filter


def generate_signal(n_points=300, noise_level=0.5, seed=42):
    """
    生成含噪声的正弦信号。

    参数:
        n_points: 采样点数
        noise_level: 噪声强度
        seed: 随机种子

    返回:
        t: 时间轴
        clean: 干净信号
        noisy: 含噪信号
    """
    np.random.seed(seed)
    t = np.linspace(0, 4 * np.pi, n_points)
    clean = np.sin(t) + 0.5 * np.sin(2 * t)
    noise = noise_level * np.random.randn(n_points)
    noisy = clean + noise
    return t, clean, noisy


def moving_average(signal, window_size=5):
    """
    手动实现移动平均滤波。

    参数:
        signal: 一维信号
        window_size: 窗口大小（奇数）

    返回:
        smoothed: 平滑后的信号
    """
    signal = np.array(signal, dtype=np.float64)
    n = len(signal)
    smoothed = np.zeros(n)

    half_w = window_size // 2

    for i in range(n):
        # 确定窗口边界（边界处自动截断）
        start = max(0, i - half_w)
        end = min(n, i + half_w + 1)
        smoothed[i] = np.mean(signal[start:end])

    return smoothed


def median_filter(signal, window_size=5):
    """
    手动实现中值滤波。

    参数:
        signal: 一维信号
        window_size: 窗口大小（奇数）

    返回:
        smoothed: 平滑后的信号
    """
    signal = np.array(signal, dtype=np.float64)
    n = len(signal)
    smoothed = np.zeros(n)

    half_w = window_size // 2

    for i in range(n):
        start = max(0, i - half_w)
        end = min(n, i + half_w + 1)
        smoothed[i] = np.median(signal[start:end])

    return smoothed


def calc_mse(signal1, signal2):
    """计算均方误差。"""
    return np.mean((signal1 - signal2) ** 2)


def calc_snr(clean, noisy):
    """计算信噪比（dB）。"""
    signal_power = np.mean(clean ** 2)
    noise_power = np.mean((noisy - clean) ** 2)
    if noise_power == 0:
        return float('inf')
    return 10 * np.log10(signal_power / noise_power)


def solve():
    """主函数：演示三种噪声平滑方法。"""
    # ========== 1. 生成信号 ==========
    t, clean, noisy = generate_signal(n_points=300, noise_level=0.5)

    print("=== 原始信号与噪声信息 ===")
    print(f"采样点数: {len(t)}")
    print(f"含噪信号范围: [{noisy.min():.3f}, {noisy.max():.3f}]")
    print(f"干净信号范围: [{clean.min():.3f}, {clean.max():.3f}]")
    print(f"原始噪声MSE: {calc_mse(clean, noisy):.6f}")
    print(f"原始信噪比: {calc_snr(clean, noisy):.2f} dB")

    # ========== 2. 移动平均滤波 ==========
    window_sizes = [5, 11, 21]
    print("\n" + "=" * 60)
    print("移动平均滤波")
    print("=" * 60)

    for ws in window_sizes:
        smoothed = moving_average(noisy, window_size=ws)
        mse = calc_mse(clean, smoothed)
        snr = calc_snr(clean, smoothed)
        print(f"  窗口={ws:2d}: MSE={mse:.6f}, SNR={snr:.2f} dB")

    # ========== 3. 中值滤波 ==========
    print("\n" + "=" * 60)
    print("中值滤波")
    print("=" * 60)

    for ws in window_sizes:
        smoothed = median_filter(noisy, window_size=ws)
        mse = calc_mse(clean, smoothed)
        snr = calc_snr(clean, smoothed)
        print(f"  窗口={ws:2d}: MSE={mse:.6f}, SNR={snr:.2f} dB")

    # ========== 4. Savitzky-Golay滤波 ==========
    print("\n" + "=" * 60)
    print("Savitzky-Golay滤波")
    print("=" * 60)

    sg_configs = [
        (11, 2),   # 窗口11, 多项式阶数2
        (21, 3),   # 窗口21, 多项式阶数3
        (31, 3),   # 窗口31, 多项式阶数3
    ]

    for ws, poly in sg_configs:
        smoothed = savgol_filter(noisy, window_length=ws, polyorder=poly)
        mse = calc_mse(clean, smoothed)
        snr = calc_snr(clean, smoothed)
        print(f"  窗口={ws:2d}, 阶数={poly}: MSE={mse:.6f}, SNR={snr:.2f} dB")

    # ========== 5. 最佳方法对比 ==========
    print("\n" + "=" * 60)
    print("最佳方法对比（窗口=11）")
    print("=" * 60)

    sm_ma = moving_average(noisy, window_size=11)
    sm_med = median_filter(noisy, window_size=11)
    sm_sg = savgol_filter(noisy, window_length=11, polyorder=3)

    methods = {
        '含噪信号': noisy,
        '移动平均': sm_ma,
        '中值滤波': sm_med,
        'S-G滤波': sm_sg
    }

    print(f"\n{'方法':<12} {'MSE':<12} {'SNR(dB)':<12}")
    print("-" * 36)
    for name, signal in methods.items():
        mse = calc_mse(clean, signal)
        snr = calc_snr(clean, signal)
        print(f"{name:<12} {mse:<12.6f} {snr:<12.2f}")

    print("\n说明: MSE越小、SNR越高，平滑效果越好。")
    print("S-G滤波通常在平滑效果和信号保真之间取得最佳平衡。")


if __name__ == "__main__":
    solve()

```
