# 1. 置信度过滤

> 来源模块: module3_deployment
> 原始文件: q48_postprocess_detection.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】检测与文本后处理算法实现
【模块】模块3 - 模型部署
【难度】4
【知识点】NMS（非极大值抑制）、Soft-NMS、Beam Search解码、CTC贪心解码、
          边界框处理、置信度过滤
【描述】
本题要求实现目标检测和文本识别中常见的后处理算法。

目标检测后处理：
1. NMS（Non-Maximum Suppression）- 标准非极大值抑制
2. Soft-NMS - 改进版NMS，不直接删除重叠框而是衰减置信度

文本识别后处理：
3. CTC贪心解码 - 将CTC输出转为文本
4. Beam Search解码 - 带宽度限制的搜索算法

【输入输出】
- 输入：模拟的检测结果（边界框+置信度）和文本模型输出（概率序列）
- 输出：打印各算法的处理结果

【要求】
1. NMS: IoU阈值默认0.5，置信度阈值默认0.5
2. Soft-NMS: 支持线性衰减和高斯衰减两种策略
3. CTC贪心解码: 移除blank，合并连续重复字符
4. Beam Search: beam_width=3，支持任意字符集
5. NMS需返回保留的边界框索引和对应的置信度
6. 所有算法使用纯numpy实现

【提示】
- IoU计算：intersection / union，注意边界框格式(x1,y1,x2,y2)
- NMS核心：按置信度排序，依次取最高分的框，删除与其IoU>阈值的框
- Soft-NMS线性衰减: score *= 1 - IoU (当IoU < threshold)
- CTC解码: argmax -> 去重复 -> 去blank
- Beam Search: 维护beam_width个候选序列，每步扩展并保留top-k
=============================
"""

# ========== 参考答案 ==========

import numpy as np


# ==================== 1. IoU计算 ====================

def compute_iou(box1, box2):
    """计算两个边界框的IoU

    Args:
        box1: [x1, y1, x2, y2]
        box2: [x1, y1, x2, y2]

    Returns:
        float: IoU值
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def compute_iou_batch(boxes, box):
    """计算一组框与单个框的IoU

    Args:
        boxes: (N, 4) numpy数组
        box: (4,) numpy数组

    Returns:
        (N,) numpy数组
    """
    x1 = np.maximum(boxes[:, 0], box[0])
    y1 = np.maximum(boxes[:, 1], box[1])
    x2 = np.minimum(boxes[:, 2], box[2])
    y2 = np.minimum(boxes[:, 3], box[3])

    intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)

    area_boxes = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    area_box = (box[2] - box[0]) * (box[3] - box[1])
    union = area_boxes + area_box - intersection

    return np.where(union > 0, intersection / union, 0.0)


# ==================== 2. NMS（标准非极大值抑制） ====================

def nms(boxes, scores, iou_threshold=0.5, score_threshold=0.5):
    """标准NMS算法

    步骤：
    1. 过滤低于score_threshold的框
    2. 按置信度降序排列
    3. 依次取最高分的框作为选中框
    4. 删除与选中框IoU > iou_threshold的剩余框
    5. 重复3-4直到无剩余框

    Args:
        boxes: (N, 4) numpy数组, 格式 [x1, y1, x2, y2]
        scores: (N,) numpy数组, 置信度
        iou_threshold: IoU阈值
        score_threshold: 置信度阈值

    Returns:
        keep_indices: 保留的框索引列表
        keep_scores: 保留的置信度列表
    """
    # 1. 置信度过滤
    mask = scores >= score_threshold
    boxes = boxes[mask]
    scores = scores[mask]
    original_indices = np.where(mask)[0]

    if len(scores) == 0:
        return [], []

    # 2. 按置信度降序排列
    order = scores.argsort()[::-1]
    boxes = boxes[order]
    scores = scores[order]
    original_indices = original_indices[order]

    keep_indices = []
    keep_scores = []

    while len(boxes) > 0:
        # 3. 取最高分的框
        keep_indices.append(original_indices[0])
        keep_scores.append(scores[0])

        if len(boxes) == 1:
            break

        # 4. 计算与当前框的IoU
        ious = compute_iou_batch(boxes[1:], boxes[0])

        # 5. 保留IoU < 阈值的框
        remaining = np.where(ious < iou_threshold)[0]
        boxes = boxes[remaining + 1]
        scores = scores[remaining + 1]
        original_indices = original_indices[remaining + 1]

    return keep_indices, keep_scores


# ==================== 3. Soft-NMS ====================

def soft_nms(boxes, scores, iou_threshold=0.5, score_threshold=0.01,
             method="linear", sigma=0.5):
    """Soft-NMS算法

    不直接删除重叠框，而是衰减其置信度。

    线性衰减: score *= 1 - IoU  (当IoU > threshold时)
    高斯衰减: score *= exp(-IoU^2 / sigma)

    Args:
        boxes: (N, 4) numpy数组
        scores: (N,) numpy数组
        iou_threshold: IoU阈值
        score_threshold: 衰减后的最低置信度
        method: "linear" 或 "gaussian"
        sigma: 高斯衰减参数

    Returns:
        keep_indices: 保留的框索引列表
        keep_scores: 保留的置信度列表
    """
    boxes = boxes.copy().astype(float)
    scores = scores.copy().astype(float)
    original_indices = np.arange(len(scores))

    keep_indices = []
    keep_scores = []

    while len(scores) > 0:
        # 取最高分的框
        max_idx = np.argmax(scores)
        keep_indices.append(original_indices[max_idx])
        keep_scores.append(scores[max_idx])

        if len(scores) == 1:
            break

        # 移除当前框
        current_box = boxes[max_idx]
        mask = np.ones(len(scores), dtype=bool)
        mask[max_idx] = False
        boxes_remaining = boxes[mask]
        scores_remaining = scores[mask]
        indices_remaining = original_indices[mask]

        # 计算IoU
        ious = compute_iou_batch(boxes_remaining, current_box)

        # 衰减置信度
        if method == "linear":
            # IoU > threshold 时衰减
            decay = np.where(ious >= iou_threshold, 1.0 - ious, np.ones_like(ious))
            scores_remaining *= decay
        elif method == "gaussian":
            scores_remaining *= np.exp(-(ious ** 2) / sigma)

        # 过滤低分框
        valid = scores_remaining >= score_threshold
        boxes = boxes_remaining[valid]
        scores = scores_remaining[valid]
        original_indices = indices_remaining[valid]

    return keep_indices, keep_scores


# ==================== 4. CTC贪心解码 ====================

def ctc_greedy_decode(log_probs, blank=0):
    """CTC贪心解码

    步骤：
    1. 每个时间步取argmax得到最佳路径
    2. 合并连续重复的标签
    3. 移除blank标签

    Args:
        log_probs: (T, C) numpy数组, 每个时间步的对数概率
        blank: blank标签索引

    Returns:
        list: 解码后的标签序列
    """
    # 1. 最佳路径
    best_path = np.argmax(log_probs, axis=1).tolist()

    # 2. 合并重复 + 3. 移除blank
    decoded = []
    prev = None
    for label in best_path:
        if label != prev:
            if label != blank:
                decoded.append(label)
        prev = label

    return decoded


def ctc_greedy_decode_with_chars(log_probs, char_map, blank=0):
    """CTC贪心解码（带字符映射）

    Args:
        log_probs: (T, C) numpy数组
        char_map: dict, {index: char}
        blank: blank标签索引

    Returns:
        str: 解码后的文本
    """
    indices = ctc_greedy_decode(log_probs, blank)
    text = "".join([char_map.get(idx, "") for idx in indices])
    return text


# ==================== 5. Beam Search解码 ====================

def beam_search_decode(log_probs, beam_width=3, blank=0):
    """Beam Search解码（简化版，用于CTC）

    在每个时间步维护beam_width个最佳候选序列。

    Args:
        log_probs: (T, C) numpy数组
        beam_width: beam宽度
        blank: blank标签索引

    Returns:
        list: 最佳路径的标签序列
    """
    T, C = log_probs.shape

    # 初始化: (score, sequence)
    beams = [(0.0, [])]

    for t in range(T):
        new_beams = []
        for score, seq in beams:
            # 对每个可能的输出标签扩展
            for c in range(C):
                new_score = score + log_probs[t, c]

                # CTC规则：允许blank，允许不同标签切换，不允许相同标签连续
                if len(seq) > 0 and seq[-1] == c and c != blank:
                    # 相同标签，CTC中需要blank分隔才能重复
                    continue

                # 如果是blank，不添加到序列但保留分数
                if c == blank:
                    new_beams.append((new_score, seq))
                else:
                    new_beams.append((new_score, seq + [c]))

        # 保留top beam_width个候选
        new_beams.sort(key=lambda x: x[0], reverse=True)
        beams = new_beams[:beam_width]

    # 返回最佳路径
    best_score, best_seq = beams[0]
    return best_seq


def beam_search_decode_simple(log_probs, beam_width=3):
    """简化版Beam Search（非CTC，直接序列解码）

    Args:
        log_probs: (T, C) numpy数组
        beam_width: beam宽度

    Returns:
        list: 最佳路径的标签序列
    """
    T, C = log_probs.shape

    # beams: list of (cumulative_log_prob, sequence)
    beams = [(0.0, [])]

    for t in range(T):
        new_beams = []
        for cum_prob, seq in beams:
            for c in range(C):
                new_prob = cum_prob + log_probs[t, c]
                new_beams.append((new_prob, seq + [c]))

        # 保留top beam_width
        new_beams.sort(key=lambda x: x[0], reverse=True)
        beams = new_beams[:beam_width]

    best_score, best_seq = beams[0]
    return best_seq


# ==================== 验证与演示 ====================

def verify_nms():
    """验证NMS和Soft-NMS"""
    print("=" * 60)
    print("[1] NMS 与 Soft-NMS 验证")
    print("=" * 60)

    # 模拟检测结果（同一目标有多个重叠的检测框）
    boxes = np.array([
        [10, 10, 50, 50],   # 目标A - 框1 (高置信度)
        [12, 11, 52, 51],   # 目标A - 框2 (重叠)
        [11, 12, 49, 49],   # 目标A - 框3 (重叠)
        [100, 100, 150, 150],  # 目标B - 框1
        [102, 101, 152, 151],  # 目标B - 框2 (重叠)
        [200, 200, 250, 250],  # 目标C (独立)
        [80, 80, 120, 120],    # 低分检测
    ], dtype=float)

    scores = np.array([0.95, 0.85, 0.80, 0.90, 0.70, 0.88, 0.30])

    print(f"  输入: {len(boxes)}个检测框")
    for i, (box, score) in enumerate(zip(boxes, scores)):
        print(f"    框{i}: [{box[0]:.0f},{box[1]:.0f},{box[2]:.0f},{box[3]:.0f}] "
              f"score={score:.2f}")

    # 标准NMS
    keep_idx, keep_scores = nms(boxes, scores, iou_threshold=0.5, score_threshold=0.5)
    print(f"\n  标准NMS结果 (IoU阈值=0.5):")
    print(f"    保留 {len(keep_idx)} 个框:")
    for idx, score in zip(keep_idx, keep_scores):
        print(f"      框{idx}: score={score:.2f}")

    # Soft-NMS (线性)
    soft_idx, soft_scores = soft_nms(boxes, scores, method="linear")
    print(f"\n  Soft-NMS结果 (线性衰减):")
    print(f"    保留 {len(soft_idx)} 个框:")
    for idx, score in zip(soft_idx, soft_scores):
        print(f"      框{idx}: score={score:.4f}")

    # Soft-NMS (高斯)
    gauss_idx, gauss_scores = soft_nms(boxes, scores, method="gaussian", sigma=0.5)
    print(f"\n  Soft-NMS结果 (高斯衰减):")
    print(f"    保留 {len(gauss_idx)} 个框:")
    for idx, score in zip(gauss_idx, gauss_scores):
        print(f"      框{idx}: score={score:.4f}")

    # IoU计算验证
    print(f"\n  IoU计算示例:")
    for i in range(min(3, len(boxes))):
        for j in range(i + 1, min(4, len(boxes))):
            iou = compute_iou(boxes[i], boxes[j])
            print(f"    框{i} vs 框{j}: IoU = {iou:.4f}")


def verify_ctc_decode():
    """验证CTC贪心解码"""
    print("\n" + "=" * 60)
    print("[2] CTC 贪心解码验证")
    print("=" * 60)

    # 模拟CTC输出 (T=10, C=5: blank + 4个字符)
    np.random.seed(42)
    log_probs = np.random.randn(10, 5)
    log_probs = log_probs - log_probs.max(axis=1, keepdims=True)  # 简单归一化

    # 字符映射
    char_map = {1: "H", 2: "E", 3: "L", 4: "O"}

    print(f"  最佳路径(argmax): {np.argmax(log_probs, axis=1).tolist()}")
    print(f"  (0=blank, 1=H, 2=E, 3=L, 4=O)")

    # CTC贪心解码
    decoded_indices = ctc_greedy_decode(log_probs, blank=0)
    decoded_text = ctc_greedy_decode_with_chars(log_probs, char_map, blank=0)

    print(f"  CTC解码结果: {decoded_indices}")
    print(f"  对应文本: {decoded_text}")

    # 另一个示例：构造明确的CTC输出
    print(f"\n  构造示例:")
    manual_probs = np.zeros((8, 5))
    # 模拟 "HHEELLOO" 的路径（含重复和blank）
    manual_path = [1, 1, 0, 2, 2, 0, 3, 4]  # H H blank E E blank L O
    for t, c in enumerate(manual_path):
        manual_probs[t, c] = 10.0

    decoded_manual = ctc_greedy_decode(manual_probs, blank=0)
    text_manual = ctc_greedy_decode_with_chars(manual_probs, char_map, blank=0)
    print(f"    路径: {manual_path}")
    print(f"    解码: {decoded_manual} -> '{text_manual}'")


def verify_beam_search():
    """验证Beam Search"""
    print("\n" + "=" * 60)
    print("[3] Beam Search 解码验证")
    print("=" * 60)

    np.random.seed(42)
    log_probs = np.random.randn(8, 5)
    log_probs = log_probs - log_probs.max(axis=1, keepdims=True)

    # 简化版Beam Search
    print(f"  简化版Beam Search (beam_width=3):")
    result_simple = beam_search_decode_simple(log_probs, beam_width=3)
    print(f"    最佳路径: {result_simple}")

    # 不同beam width
    for bw in [1, 3, 5]:
        result = beam_search_decode_simple(log_probs, beam_width=bw)
        print(f"    beam_width={bw}: {result}")

    # 贪心对比 (beam_width=1 等价于贪心)
    greedy_result = np.argmax(log_probs, axis=1).tolist()
    beam_1_result = beam_search_decode_simple(log_probs, beam_width=1)
    print(f"\n  贪心argmax: {greedy_result}")
    print(f"  Beam(width=1): {beam_1_result}")
    print(f"  一致性: {greedy_result == beam_1_result}")


def solve():
    verify_nms()
    verify_ctc_decode()
    verify_beam_search()
    print("\n" + "=" * 60)
    print("检测与文本后处理验证完成！")
    print("=" * 60)


if __name__ == "__main__":
    solve()

```
