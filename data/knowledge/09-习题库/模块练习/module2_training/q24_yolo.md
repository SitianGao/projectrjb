# (3, 224, 224) -> (64, 112, 112)

> 来源模块: module2_training
> 原始文件: q24_yolo.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】YOLO目标检测简化版：PyTorch实现
【模块】模型训练与评估
【难度】8
【知识点】YOLO、目标检测、网格划分、锚框、置信度预测、边界框回归、
         非极大值抑制(NMS)、IoU、损失函数
【描述】
YOLO(You Only Look Once)是一种经典的单阶段目标检测算法。它将图像划分为
SxS网格，每个网格预测B个边界框及其置信度和类别概率。
本题要求用PyTorch实现YOLO检测头的简化版本，包含核心组件。

简化版YOLO设计：
- 输入: 3x224x224图像
- 骨干网络: 简单卷积层提取特征
- 检测头: 7x7网格划分，每格预测2个框
- 每个预测: [x, y, w, h, confidence, class1_prob, ..., classN_prob]

【要求】
1. 实现简化版YOLO骨干网络（几层卷积）
2. 实现YOLO检测头，输出7x7网格的预测
3. 实现边界框解码：将网络输出转换为实际坐标
4. 实现IoU计算函数
5. 实现非极大值抑制(NMS)后处理
6. 实现YOLO风格的损失函数（坐标损失+置信度损失+分类损失）
7. 在随机生成的模拟数据上演示完整流程

【提示】
- 网络输出需要reshape为 (batch, S, S, B*5+C) 的格式
- 坐标预测x,y是相对于网格单元的偏移，w,h是相对于图像的归一化值
- NMS: 按置信度排序，依次移除与最高置信度框IoU>阈值的框
- YOLO损失 = lambda_coord * coord_loss + lambda_noobj * noobj_loss + obj_loss + class_loss
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


# ============ 1. 骨干网络 ============

class SimpleBackbone(nn.Module):
    """简单骨干网络提取特征"""

    def __init__(self):
        super(SimpleBackbone, self).__init__()
        self.features = nn.Sequential(
            # (3, 224, 224) -> (64, 112, 112)
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.1),
            nn.MaxPool2d(2, 2),  # (64, 56, 56)

            # -> (128, 28, 28)
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.1),
            nn.MaxPool2d(2, 2),  # (128, 14, 14)

            # -> (256, 14, 14)
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.1),

            # -> (512, 7, 7)
            nn.Conv2d(256, 512, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.1),
        )

    def forward(self, x):
        return self.features(x)


# ============ 2. YOLO检测头 ============

class YOLODetectionHead(nn.Module):
    """YOLO检测头"""

    def __init__(self, in_channels=512, S=7, B=2, num_classes=4):
        """
        S: 网格大小 (SxS)
        B: 每个网格预测的边界框数量
        num_classes: 类别数
        """
        super(YOLODetectionHead, self).__init__()
        self.S = S
        self.B = B
        self.C = num_classes
        # 每个网格的输出维度: B * (5 + C) = B * 5 + B * C
        # 但标准YOLO每格只预测一组类别概率: B * 5 + C
        self.output_dim = B * 5 + num_classes  # 2*5+4 = 14

        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, 256, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.1),
            nn.Conv2d(256, self.output_dim, kernel_size=1),
        )

    def forward(self, x):
        """
        输入: (batch, in_channels, S, S)
        输出: (batch, S, S, B*5+C)
        """
        x = self.conv(x)  # (batch, output_dim, S, S)
        x = x.permute(0, 2, 3, 1)  # (batch, S, S, output_dim)
        return x


# ============ 3. 完整YOLO模型 ============

class SimpleYOLO(nn.Module):
    """简化版YOLO模型"""

    def __init__(self, S=7, B=2, num_classes=4):
        super(SimpleYOLO, self).__init__()
        self.S = S
        self.B = B
        self.C = num_classes
        self.backbone = SimpleBackbone()
        self.head = YOLODetectionHead(512, S, B, num_classes)

    def forward(self, x):
        features = self.backbone(x)
        predictions = self.head(features)
        return predictions


# ============ 4. 工具函数 ============

def compute_iou(box1, box2):
    """
    计算两组边界框之间的IoU
    box1, box2: (..., 4) 格式为 [x_center, y_center, width, height]
    """
    # 转换为角坐标
    def to_corners(box):
        x_min = box[..., 0] - box[..., 2] / 2
        y_min = box[..., 1] - box[..., 3] / 2
        x_max = box[..., 0] + box[..., 2] / 2
        y_max = box[..., 1] + box[..., 3] / 2
        return x_min, y_min, x_max, y_max

    x1_min, y1_min, x1_max, y1_max = to_corners(box1)
    x2_min, y2_min, x2_max, y2_max = to_corners(box2)

    # 交集
    inter_xmin = torch.max(x1_min, x2_min)
    inter_ymin = torch.max(y1_min, y2_min)
    inter_xmax = torch.min(x1_max, x2_max)
    inter_ymax = torch.min(y1_max, y2_max)

    inter_area = torch.clamp(inter_xmax - inter_xmin, min=0) * \
                 torch.clamp(inter_ymax - inter_ymin, min=0)

    # 并集
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = area1 + area2 - inter_area

    iou = inter_area / (union_area + 1e-6)
    return iou


def decode_predictions(predictions, S=7, B=2, num_classes=4,
                       conf_threshold=0.3):
    """
    解码YOLO预测输出为边界框列表
    predictions: (S, S, B*5+C)
    """
    boxes = []
    for i in range(S):
        for j in range(S):
            cell_pred = predictions[i, j]
            for b in range(B):
                offset = b * 5
                x = (cell_pred[offset + 0].item() + j) / S
                y = (cell_pred[offset + 1].item() + i) / S
                w = cell_pred[offset + 2].item()
                h = cell_pred[offset + 3].item()
                conf = torch.sigmoid(cell_pred[offset + 4]).item()

                if conf < conf_threshold:
                    continue

                # 类别概率
                class_probs = torch.softmax(
                    cell_pred[B * 5:B * 5 + num_classes], dim=0
                )
                class_conf, class_idx = torch.max(class_probs, dim=0)
                final_conf = conf * class_conf.item()

                boxes.append({
                    "x": x, "y": y, "w": w, "h": h,
                    "confidence": final_conf,
                    "class_id": class_idx.item(),
                })
    return boxes


def nms(boxes, iou_threshold=0.5):
    """
    非极大值抑制 (NMS)
    boxes: list of dict with keys: x, y, w, h, confidence, class_id
    """
    if not boxes:
        return []

    # 按置信度排序
    boxes = sorted(boxes, key=lambda b: b["confidence"], reverse=True)
    result = []

    while boxes:
        best = boxes.pop(0)
        result.append(best)

        remaining = []
        best_box = torch.tensor([best["x"], best["y"], best["w"], best["h"]])
        for box in boxes:
            if box["class_id"] != best["class_id"]:
                remaining.append(box)
                continue
            cur_box = torch.tensor([box["x"], box["y"], box["w"], box["h"]])
            iou = compute_iou(best_box, cur_box).item()
            if iou < iou_threshold:
                remaining.append(box)
        boxes = remaining

    return result


# ============ 5. YOLO损失函数 ============

class YOLOLoss(nn.Module):
    """简化版YOLO损失函数"""

    def __init__(self, S=7, B=2, num_classes=4):
        super(YOLOLoss, self).__init__()
        self.S = S
        self.B = B
        self.C = num_classes
        self.lambda_coord = 5.0
        self.lambda_noobj = 0.5

    def forward(self, predictions, targets):
        """
        predictions: (batch, S, S, B*5+C)
        targets: (batch, S, S, B*5+C) 格式相同的标注
        简化处理: targets中objectness=1表示该网格有目标
        """
        # 分离预测的各个部分
        # 第一个框的坐标和置信度
        pred_box1 = predictions[..., 0:5]    # (batch, S, S, 5)
        pred_box2 = predictions[..., 5:10]   # (batch, S, S, 5)
        pred_class = predictions[..., 10:]   # (batch, S, S, C)

        # 标注
        target_box = targets[..., 0:5]
        obj_mask = targets[..., 4]  # objectness mask: (batch, S, S)
        target_class = targets[..., 10:]

        # 简化: 使用box1负责预测有目标的网格
        obj_mask_bool = (obj_mask > 0.5)

        # 坐标损失 (只有有目标的网格)
        if obj_mask_bool.sum() > 0:
            coord_loss = F.mse_loss(
                pred_box1[..., :4][obj_mask_bool],
                target_box[..., :4][obj_mask_bool]
            )
        else:
            coord_loss = torch.tensor(0.0, device=predictions.device)

        # 置信度损失
        pred_conf1 = torch.sigmoid(pred_box1[..., 4])
        obj_conf_loss = F.mse_loss(
            pred_conf1[obj_mask_bool],
            target_box[..., 4][obj_mask_bool]
        ) if obj_mask_bool.sum() > 0 else torch.tensor(0.0, device=predictions.device)

        noobj_mask = ~obj_mask_bool
        noobj_conf_loss = F.mse_loss(
            pred_conf1[noobj_mask],
            torch.zeros_like(pred_conf1[noobj_mask])
        ) if noobj_mask.sum() > 0 else torch.tensor(0.0, device=predictions.device)

        # 分类损失
        if obj_mask_bool.sum() > 0:
            class_loss = F.cross_entropy(
                pred_class[obj_mask_bool],
                target_class[obj_mask_bool].argmax(dim=-1)
            )
        else:
            class_loss = torch.tensor(0.0, device=predictions.device)

        total_loss = (self.lambda_coord * coord_loss +
                      obj_conf_loss +
                      self.lambda_noobj * noobj_conf_loss +
                      class_loss)
        return total_loss


def solve():
    device = torch.device("cpu")
    S = 7
    B = 2
    num_classes = 4

    # ---- 1. 创建模型 ----
    model = SimpleYOLO(S=S, B=B, num_classes=num_classes).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print("=" * 60)
    print("简化版YOLO目标检测模型")
    print("=" * 60)
    print(f"网格大小: {S}x{S}")
    print(f"每格预测框数: {B}")
    print(f"类别数: {num_classes}")
    print(f"模型参数量: {total_params:,}")

    # ---- 2. 前向传播演示 ----
    dummy_input = torch.randn(2, 3, 224, 224).to(device)
    model.eval()
    with torch.no_grad():
        output = model(dummy_input)
    print(f"\n输入形状: {dummy_input.shape}")
    print(f"输出形状: {output.shape}")
    print(f"预期: (2, {S}, {S}, {B*5+num_classes})")

    # ---- 3. IoU计算演示 ----
    print("\n" + "=" * 60)
    print("IoU计算演示")
    print("=" * 60)
    box1 = torch.tensor([0.5, 0.5, 0.3, 0.3])  # 中心(0.5,0.5), 宽高(0.3,0.3)
    box2 = torch.tensor([0.6, 0.6, 0.3, 0.3])  # 中心(0.6,0.6), 宽高(0.3,0.3)
    iou = compute_iou(box1, box2)
    print(f"Box1: 中心(0.5,0.5), 尺寸0.3x0.3")
    print(f"Box2: 中心(0.6,0.6), 尺寸0.3x0.3")
    print(f"IoU: {iou.item():.4f}")

    # ---- 4. NMS演示 ----
    print("\n" + "=" * 60)
    print("NMS (非极大值抑制) 演示")
    print("=" * 60)
    test_boxes = [
        {"x": 0.5, "y": 0.5, "w": 0.2, "h": 0.2, "confidence": 0.9, "class_id": 0},
        {"x": 0.52, "y": 0.51, "w": 0.2, "h": 0.2, "confidence": 0.7, "class_id": 0},
        {"x": 0.51, "y": 0.52, "w": 0.2, "h": 0.2, "confidence": 0.6, "class_id": 0},
        {"x": 0.8, "y": 0.8, "w": 0.15, "h": 0.15, "confidence": 0.8, "class_id": 1},
        {"x": 0.81, "y": 0.79, "w": 0.15, "h": 0.15, "confidence": 0.5, "class_id": 1},
    ]
    print(f"NMS前: {len(test_boxes)} 个框")
    for b in test_boxes:
        print(f"  ({b['x']:.2f},{b['y']:.2f}) {b['w']:.2f}x{b['h']:.2f} "
              f"conf={b['confidence']:.2f} class={b['class_id']}")

    filtered = nms(test_boxes, iou_threshold=0.5)
    print(f"\nNMS后: {len(filtered)} 个框")
    for b in filtered:
        print(f"  ({b['x']:.2f},{b['y']:.2f}) {b['w']:.2f}x{b['h']:.2f} "
              f"conf={b['confidence']:.2f} class={b['class_id']}")

    # ---- 5. 损失函数与训练演示 ----
    print("\n" + "=" * 60)
    print("损失函数与训练演示")
    print("=" * 60)
    model.train()
    criterion = YOLOLoss(S=S, B=B, num_classes=num_classes)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # 生成模拟训练数据
    for step in range(5):
        images = torch.randn(4, 3, 224, 224)
        targets = torch.zeros(4, S, S, B * 5 + num_classes)
        # 在(3,3)网格放入一个目标
        for b in range(4):
            targets[b, 3, 3, 0:4] = torch.tensor([0.43, 0.43, 0.1, 0.1])
            targets[b, 3, 3, 4] = 1.0  # objectness
            targets[b, 3, 3, 10 + (b % num_classes)] = 1.0  # class

        predictions = model(images)
        loss = criterion(predictions, targets)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        print(f"  Step {step+1}: Loss = {loss.item():.4f}")

    # ---- 6. 解码预测演示 ----
    print("\n" + "=" * 60)
    print("预测解码演示")
    print("=" * 60)
    model.eval()
    with torch.no_grad():
        test_img = torch.randn(1, 3, 224, 224)
        pred = model(test_img)[0]  # (S, S, B*5+C)
        raw_boxes = decode_predictions(pred, S=S, B=B,
                                       num_classes=num_classes,
                                       conf_threshold=0.2)
        final_boxes = nms(raw_boxes, iou_threshold=0.5)
        print(f"解码得到 {len(raw_boxes)} 个候选框")
        print(f"NMS后保留 {len(final_boxes)} 个框")
        for i, b in enumerate(final_boxes[:5]):
            print(f"  框{i+1}: ({b['x']:.3f},{b['y']:.3f}) "
                  f"{b['w']:.3f}x{b['h']:.3f} "
                  f"conf={b['confidence']:.3f} class={b['class_id']}")


if __name__ == "__main__":
    solve()

```
