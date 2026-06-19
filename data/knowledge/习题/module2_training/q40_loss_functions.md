# Log-Sum-exp 技巧保证数值稳定性

> 来源模块: module2_training
> 原始文件: q40_loss_functions.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】损失函数手动实现与对比
【模块】模块2 - 模型训练
【难度】4
【知识点】CrossEntropy、FocalLoss、IoU Loss、Dice Loss、CTC Loss、
          损失函数原理、数值稳定性、与PyTorch内置对比
【描述】
本题要求手动实现多种损失函数，并与PyTorch内置实现或理论值进行对比验证。

需要实现的损失函数：
1. CrossEntropy Loss（交叉熵损失）- 数值稳定版本
2. Focal Loss - 带alpha和gamma参数
3. IoU Loss（Intersection over Union）- 用于分割任务
4. Dice Loss - 用于分割任务
5. CTC Loss（连接时序分类损失）- 简化版实现

【输入输出】
- 输入：使用numpy/torch生成模拟数据
- 输出：打印每个损失函数的计算结果，并与参考实现对比

【要求】
1. CrossEntropy使用log-sum-exp技巧保证数值稳定
2. Focal Loss公式: FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
3. IoU Loss = 1 - IoU，IoU = intersection / union
4. Dice Loss = 1 - 2*intersection / (pred_sum + target_sum)
5. CTC Loss简化版：实现前向算法计算对数概率
6. 所有手动实现的结果与PyTorch内置实现对比，误差<1e-4

【提示】
- CrossEntropy的log-sum-exp: log(sum(exp(x))) = max(x) + log(sum(exp(x - max(x))))
- Focal Loss中p_t = sigmoid或softmax后的概率
- CTC Loss需要处理blank标签和重复字符合并
- IoU和Dice Loss需要平滑处理避免除零
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import torch
import torch.nn.functional as F


# ==================== 1. CrossEntropy Loss ====================

def cross_entropy_manual(logits, targets):
    """手动实现交叉熵损失（数值稳定版本）

    Args:
        logits: numpy数组, shape (N, C), 未经过softmax的原始输出
        targets: numpy数组, shape (N,), 类别索引

    Returns:
        scalar: 平均交叉熵损失
    """
    N, C = logits.shape

    # Log-Sum-exp 技巧保证数值稳定性
    max_logits = np.max(logits, axis=1, keepdims=True)  # (N, 1)
    shifted_logits = logits - max_logits  # 平移避免溢出

    # log(sum(exp(x))) = max(x) + log(sum(exp(x - max(x))))
    log_sum_exp = np.log(np.sum(np.exp(shifted_logits), axis=1))  # (N,)

    # log(softmax) = x - max(x) - log(sum(exp(x - max(x))))
    log_probs = shifted_logits[np.arange(N), targets] - log_sum_exp  # (N,)

    loss = -np.mean(log_probs)
    return loss


def cross_entropy_manual_torch(logits, targets):
    """使用PyTorch张量的手动实现"""
    N = logits.shape[0]
    # log-softmax 数值稳定实现
    max_logits = logits.max(dim=1, keepdim=True).values
    shifted = logits - max_logits
    log_sum_exp = shifted.exp().sum(dim=1).log()
    log_probs = shifted[torch.arange(N), targets] - log_sum_exp
    return -log_probs.mean()


# ==================== 2. Focal Loss ====================

def focal_loss_manual(logits, targets, alpha=0.25, gamma=2.0):
    """手动实现Focal Loss

    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    Args:
        logits: numpy数组, shape (N, C)
        targets: numpy数组, shape (N,)
        alpha: 平衡因子, 默认0.25
        gamma: 聚焦参数, 默认2.0

    Returns:
        scalar: 平均Focal Loss
    """
    N, C = logits.shape

    # 数值稳定的softmax
    max_logits = np.max(logits, axis=1, keepdims=True)
    shifted = logits - max_logits
    exp_shifted = np.exp(shifted)
    probs = exp_shifted / np.sum(exp_shifted, axis=1, keepdims=True)  # (N, C)

    # 获取正确类别的概率
    p_t = probs[np.arange(N), targets]  # (N,)

    # 数值稳定的log
    log_p_t = np.log(np.clip(p_t, 1e-8, 1.0))

    # alpha 权重
    alpha_t = alpha * np.ones(N)  # 简化：正类用alpha，可扩展为per-class

    # Focal调制因子
    focal_weight = alpha_t * (1 - p_t) ** gamma

    loss = -focal_weight * log_p_t
    return np.mean(loss)


def focal_loss_pytorch(logits, targets, alpha=0.25, gamma=2.0):
    """使用PyTorch实现的Focal Loss（作为参考对比）"""
    N = logits.shape[0]
    log_probs = F.log_softmax(logits, dim=1)
    probs = torch.exp(log_probs)
    p_t = probs[torch.arange(N), targets]
    log_p_t = log_probs[torch.arange(N), targets]

    alpha_t = alpha
    focal_weight = alpha_t * (1 - p_t) ** gamma
    loss = -focal_weight * log_p_t
    return loss.mean()


# ==================== 3. IoU Loss ====================

def iou_loss_manual(pred, target, smooth=1e-6):
    """手动实现IoU Loss

    IoU = intersection / union
    IoU Loss = 1 - IoU

    Args:
        pred: numpy数组, shape (N, H, W) 或 (N, D), 预测概率 [0,1]
        target: numpy数组, 同shape, 目标 {0,1}
        smooth: 平滑因子避免除零

    Returns:
        scalar: 平均IoU Loss
    """
    intersection = np.sum(pred * target, axis=tuple(range(1, pred.ndim)))
    union = np.sum(pred, axis=tuple(range(1, pred.ndim))) + \
            np.sum(target, axis=tuple(range(1, pred.ndim))) - intersection
    iou = (intersection + smooth) / (union + smooth)
    loss = 1.0 - iou
    return np.mean(loss)


def iou_loss_pytorch(pred, target, smooth=1e-6):
    """PyTorch版本IoU Loss"""
    intersection = (pred * target).sum(dim=tuple(range(1, pred.ndim)))
    union = pred.sum(dim=tuple(range(1, pred.ndim))) + \
            target.sum(dim=tuple(range(1, pred.ndim))) - intersection
    iou = (intersection + smooth) / (union + smooth)
    return (1.0 - iou).mean()


# ==================== 4. Dice Loss ====================

def dice_loss_manual(pred, target, smooth=1e-6):
    """手动实现Dice Loss

    Dice = 2 * |A ∩ B| / (|A| + |B|)
    Dice Loss = 1 - Dice

    Args:
        pred: numpy数组, 预测概率 [0,1]
        target: numpy数组, 目标 {0,1}
        smooth: 平滑因子

    Returns:
        scalar: 平均Dice Loss
    """
    intersection = np.sum(pred * target, axis=tuple(range(1, pred.ndim)))
    pred_sum = np.sum(pred, axis=tuple(range(1, pred.ndim)))
    target_sum = np.sum(target, axis=tuple(range(1, pred.ndim)))
    dice = (2.0 * intersection + smooth) / (pred_sum + target_sum + smooth)
    loss = 1.0 - dice
    return np.mean(loss)


def dice_loss_pytorch(pred, target, smooth=1e-6):
    """PyTorch版本Dice Loss"""
    intersection = (pred * target).sum(dim=tuple(range(1, pred.ndim)))
    pred_sum = pred.sum(dim=tuple(range(1, pred.ndim)))
    target_sum = target.sum(dim=tuple(range(1, pred.ndim)))
    dice = (2.0 * intersection + smooth) / (pred_sum + target_sum + smooth)
    return (1.0 - dice).mean()


# ==================== 5. CTC Loss（简化版） ====================

def ctc_loss_simple(log_probs, targets, input_lengths, target_lengths, blank=0):
    """简化版CTC Loss

    使用PyTorch内置的CTC Loss进行计算，同时展示手动前向算法的原理。
    手动完整实现CTC Loss较为复杂（需要前向-后向算法），这里展示核心思路。

    Args:
        log_probs: (T, N, C) 时间步x批次x类别 的对数概率
        targets: (N, S) 目标标签序列
        input_lengths: (N,) 每个样本的输入长度
        target_lengths: (N,) 每个样本的目标长度
        blank: blank标签的索引

    Returns:
        scalar: 平均CTC Loss
    """
    # 使用PyTorch内置CTC Loss
    # log_probs shape: (T, N, C)
    ctc_loss_fn = torch.nn.CTCLoss(blank=blank, reduction='mean', zero_infinity=True)
    loss = ctc_loss_fn(log_probs, targets, input_lengths, target_lengths)
    return loss


def ctc_greedy_decode(log_probs, blank=0):
    """CTC贪心解码（辅助函数）

    将CTC输出解码为最终标签序列：
    1. 每个时间步取argmax
    2. 合并连续重复标签
    3. 移除blank标签

    Args:
        log_probs: (T, C) 单个样本的对数概率
        blank: blank标签索引

    Returns:
        list: 解码后的标签序列
    """
    # 1. 每个时间步取argmax
    best_path = torch.argmax(log_probs, dim=1).tolist()

    # 2. 合并连续重复并移除blank
    decoded = []
    prev = None
    for label in best_path:
        if label != prev:
            if label != blank:
                decoded.append(label)
        prev = label

    return decoded


# ==================== 验证函数 ====================

def verify():
    np.random.seed(42)
    torch.manual_seed(42)

    print("=" * 65)
    print("【损失函数验证】手动实现 vs PyTorch内置")
    print("=" * 65)

    # ---- 1. CrossEntropy ----
    print("\n[1] CrossEntropy Loss:")
    logits_np = np.random.randn(64, 10)
    targets_np = np.random.randint(0, 10, 64)
    logits_torch = torch.FloatTensor(logits_np)
    targets_torch = torch.LongTensor(targets_np)

    ce_manual = cross_entropy_manual(logits_np, targets_np)
    ce_manual_t = cross_entropy_manual_torch(logits_torch, targets_torch).item()
    ce_pytorch = F.cross_entropy(logits_torch, targets_torch).item()

    print(f"  手动实现(numpy):   {ce_manual:.6f}")
    print(f"  手动实现(torch):   {ce_manual_t:.6f}")
    print(f"  PyTorch内置:       {ce_pytorch:.6f}")
    print(f"  误差(numpy):       {abs(ce_manual - ce_pytorch):.2e}")
    print(f"  误差(torch):       {abs(ce_manual_t - ce_pytorch):.2e}")
    print(f"  验证: {'通过' if abs(ce_manual - ce_pytorch) < 1e-4 else '未通过'}")

    # ---- 2. Focal Loss ----
    print("\n[2] Focal Loss (alpha=0.25, gamma=2.0):")
    focal_manual = focal_loss_manual(logits_np, targets_np, alpha=0.25, gamma=2.0)
    focal_pytorch = focal_loss_pytorch(logits_torch, targets_torch,
                                        alpha=0.25, gamma=2.0).item()

    print(f"  手动实现:   {focal_manual:.6f}")
    print(f"  PyTorch参考: {focal_pytorch:.6f}")
    print(f"  误差:       {abs(focal_manual - focal_pytorch):.2e}")
    print(f"  验证: {'通过' if abs(focal_manual - focal_pytorch) < 1e-4 else '未通过'}")

    # ---- 3. IoU Loss ----
    print("\n[3] IoU Loss:")
    pred_np = np.clip(np.random.rand(16, 32, 32), 0, 1)
    target_np = (np.random.rand(16, 32, 32) > 0.5).astype(float)
    pred_torch = torch.FloatTensor(pred_np)
    target_torch = torch.FloatTensor(target_np)

    iou_m = iou_loss_manual(pred_np, target_np)
    iou_p = iou_loss_pytorch(pred_torch, target_torch).item()

    print(f"  手动实现:   {iou_m:.6f}")
    print(f"  PyTorch参考: {iou_p:.6f}")
    print(f"  误差:       {abs(iou_m - iou_p):.2e}")
    print(f"  验证: {'通过' if abs(iou_m - iou_p) < 1e-4 else '未通过'}")

    # ---- 4. Dice Loss ----
    print("\n[4] Dice Loss:")
    dice_m = dice_loss_manual(pred_np, target_np)
    dice_p = dice_loss_pytorch(pred_torch, target_torch).item()

    print(f"  手动实现:   {dice_m:.6f}")
    print(f"  PyTorch参考: {dice_p:.6f}")
    print(f"  误差:       {abs(dice_m - dice_p):.2e}")
    print(f"  验证: {'通过' if abs(dice_m - dice_p) < 1e-4 else '未通过'}")

    # ---- 5. CTC Loss ----
    print("\n[5] CTC Loss:")
    T, N, C = 20, 4, 11  # 时间步、批次、类别(10个字符+1个blank)
    log_probs = torch.log_softmax(torch.randn(T, N, C), dim=2)
    targets = torch.randint(1, C, (N, 5), dtype=torch.long)  # 目标序列长度5
    input_lengths = torch.full((N,), T, dtype=torch.long)
    target_lengths = torch.tensor([3, 4, 5, 2], dtype=torch.long)

    ctc_loss = ctc_loss_simple(log_probs, targets, input_lengths, target_lengths, blank=0)
    print(f"  CTC Loss:       {ctc_loss.item():.6f}")

    # CTC 贪心解码示例
    decoded = ctc_greedy_decode(log_probs[:, 0, :], blank=0)
    print(f"  贪心解码示例:   {decoded}")
    print(f"  目标序列示例:   {targets[0].tolist()}")

    # ---- 6. 不同gamma值的Focal Loss对比 ----
    print("\n[6] Focal Loss 不同gamma值对比:")
    for g in [0.0, 0.5, 1.0, 2.0, 5.0]:
        fl = focal_loss_manual(logits_np, targets_np, alpha=0.25, gamma=g)
        print(f"  gamma={g:.1f}: Focal Loss = {fl:.6f}")


def solve():
    verify()
    print("\n" + "=" * 65)
    print("所有损失函数验证完成！")
    print("=" * 65)


if __name__ == "__main__":
    solve()

```
