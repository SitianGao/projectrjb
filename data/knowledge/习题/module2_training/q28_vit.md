# 使用卷积实现patch提取和投影

> 来源模块: module2_training
> 原始文件: q28_vit.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】Vision Transformer图像分类
【模块】模型训练与评估
【难度】9
【知识点】Vision Transformer、Patch Embedding、Transformer Encoder、图像分类、PyTorch
【描述】
使用PyTorch从头实现Vision Transformer（ViT）模型，包括Patch Embedding、Transformer
Encoder和Classification Head。在小数据集上演示图像分类任务。

【要求】
1. 实现Patch Embedding层：将图像分割为固定大小的patch并线性投影
2. 实现Multi-Head Self-Attention机制
3. 实现Transformer Encoder Block（Attention + MLP + LayerNorm + 残差连接）
4. 实现完整的ViT模型（加入CLS token + Position Embedding）
5. 在CIFAR-10子集（或随机生成的小数据集）上训练和评估
6. 打印训练过程中损失和准确率的变化

【提示】
- 使用较小的patch_size和embed_dim以便在小数据集上快速训练
- 可使用随机生成的数据或torchvision内置数据集
- 注意维度变换的正确性
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np


# ------------------ Patch Embedding ------------------
class PatchEmbedding(nn.Module):
    """将图像分割为patches并进行线性投影"""

    def __init__(self, img_size=32, patch_size=4, in_channels=3, embed_dim=64):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.num_patches = (img_size // patch_size) ** 2
        # 使用卷积实现patch提取和投影
        self.proj = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size, stride=patch_size
        )

    def forward(self, x):
        # x: (B, C, H, W)
        x = self.proj(x)  # (B, embed_dim, H/patch_size, W/patch_size)
        x = x.flatten(2)  # (B, embed_dim, num_patches)
        x = x.transpose(1, 2)  # (B, num_patches, embed_dim)
        return x


# ------------------ Multi-Head Self-Attention ------------------
class MultiHeadSelfAttention(nn.Module):
    """多头自注意力机制"""

    def __init__(self, embed_dim=64, num_heads=4, dropout=0.1):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        assert self.head_dim * num_heads == embed_dim, "embed_dim必须能被num_heads整除"

        self.qkv = nn.Linear(embed_dim, embed_dim * 3)
        self.attn_drop = nn.Dropout(dropout)
        self.proj = nn.Linear(embed_dim, embed_dim)
        self.proj_drop = nn.Dropout(dropout)

    def forward(self, x):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, heads, N, head_dim)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # Scaled dot-product attention
        scale = self.head_dim ** -0.5
        attn = (q @ k.transpose(-2, -1)) * scale  # (B, heads, N, N)
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)

        x = (attn @ v).transpose(1, 2).reshape(B, N, C)  # (B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x


# ------------------ MLP ------------------
class MLP(nn.Module):
    """Transformer中的前馈网络"""

    def __init__(self, embed_dim=64, hidden_dim=128, dropout=0.1):
        super().__init__()
        self.fc1 = nn.Linear(embed_dim, hidden_dim)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_dim, embed_dim)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        x = self.drop(self.act(self.fc1(x)))
        x = self.drop(self.fc2(x))
        return x


# ------------------ Transformer Encoder Block ------------------
class TransformerEncoderBlock(nn.Module):
    """Transformer Encoder Block"""

    def __init__(self, embed_dim=64, num_heads=4, mlp_hidden_dim=128, dropout=0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadSelfAttention(embed_dim, num_heads, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.mlp = MLP(embed_dim, mlp_hidden_dim, dropout)

    def forward(self, x):
        # 残差连接 + LayerNorm (Pre-Norm)
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x


# ------------------ Vision Transformer ------------------
class VisionTransformer(nn.Module):
    """完整的Vision Transformer模型"""

    def __init__(
        self,
        img_size=32,
        patch_size=4,
        in_channels=3,
        num_classes=10,
        embed_dim=64,
        num_heads=4,
        num_layers=4,
        mlp_hidden_dim=128,
        dropout=0.1,
    ):
        super().__init__()
        self.patch_embed = PatchEmbedding(img_size, patch_size, in_channels, embed_dim)
        num_patches = self.patch_embed.num_patches

        # CLS token
        self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim) * 0.02)
        # 位置编码
        self.pos_embed = nn.Parameter(torch.randn(1, num_patches + 1, embed_dim) * 0.02)
        self.pos_drop = nn.Dropout(dropout)

        # Transformer Encoder
        self.blocks = nn.ModuleList([
            TransformerEncoderBlock(embed_dim, num_heads, mlp_hidden_dim, dropout)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(embed_dim)

        # Classification Head
        self.head = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        B = x.shape[0]

        # Patch embedding
        x = self.patch_embed(x)  # (B, num_patches, embed_dim)

        # 添加CLS token
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)  # (B, num_patches+1, embed_dim)

        # 添加位置编码
        x = self.pos_drop(x + self.pos_embed)

        # Transformer Encoder blocks
        for block in self.blocks:
            x = block(x)

        # LayerNorm
        x = self.norm(x)

        # 使用CLS token做分类
        cls_output = x[:, 0]  # (B, embed_dim)
        logits = self.head(cls_output)  # (B, num_classes)
        return logits


# ------------------ 训练与评估 ------------------
def train_model(model, train_loader, test_loader, num_epochs=10, lr=1e-3, device="cpu"):
    """训练和评估ViT模型"""
    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    criterion = nn.CrossEntropyLoss()

    print("Vision Transformer 训练开始")
    print("=" * 60)

    for epoch in range(num_epochs):
        # ---- 训练阶段 ----
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()

        avg_train_loss = train_loss / train_total
        train_acc = train_correct / train_total

        # ---- 评估阶段 ----
        model.eval()
        test_loss = 0.0
        test_correct = 0
        test_total = 0

        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)

                test_loss += loss.item() * images.size(0)
                _, predicted = outputs.max(1)
                test_total += labels.size(0)
                test_correct += predicted.eq(labels).sum().item()

        avg_test_loss = test_loss / test_total
        test_acc = test_correct / test_total

        print(
            f"Epoch [{epoch + 1:2d}/{num_epochs}] | "
            f"Train Loss: {avg_train_loss:.4f} Acc: {train_acc:.4f} | "
            f"Test Loss: {avg_test_loss:.4f} Acc: {test_acc:.4f}"
        )

    print("=" * 60)
    print(f"最终测试准确率: {test_acc:.4f}")
    return model


def generate_synthetic_data(num_samples=1000, img_size=32, num_classes=10):
    """生成合成数据用于演示（模拟CIFAR-10风格）"""
    np.random.seed(42)
    torch.manual_seed(42)

    # 为每个类别生成不同模式的图像
    images = []
    labels = []
    for cls in range(num_classes):
        for _ in range(num_samples // num_classes):
            # 每个类别有独特的颜色模式
            img = np.random.randn(3, img_size, img_size).astype(np.float32) * 0.1
            # 添加类别特定的模式
            img[cls % 3] += 0.5
            if cls >= 3:
                img[:, :img_size // 2, :] += 0.3
            images.append(img)
            labels.append(cls)

    images = torch.tensor(np.array(images))
    labels = torch.tensor(labels, dtype=torch.long)
    return images, labels


def solve():
    """Vision Transformer完整演示"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # ---- 参数设置 ----
    img_size = 32
    patch_size = 4
    in_channels = 3
    num_classes = 10
    embed_dim = 64
    num_heads = 4
    num_layers = 4
    mlp_hidden_dim = 128
    batch_size = 64
    num_epochs = 10
    lr = 1e-3

    print(f"\n模型参数:")
    print(f"  图像大小: {img_size}x{img_size}, Patch大小: {patch_size}x{patch_size}")
    print(f"  Patches数量: {(img_size // patch_size) ** 2}")
    print(f"  嵌入维度: {embed_dim}, 注意力头数: {num_heads}, 层数: {num_layers}")

    # ---- 生成数据 ----
    print("\n生成合成数据...")
    images, labels = generate_synthetic_data(num_samples=1000, img_size=img_size, num_classes=num_classes)

    # 划分训练集和测试集
    num_train = 800
    train_dataset = TensorDataset(images[:num_train], labels[:num_train])
    test_dataset = TensorDataset(images[num_train:], labels[num_train:])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    print(f"训练集: {len(train_dataset)}, 测试集: {len(test_dataset)}")

    # ---- 构建模型 ----
    model = VisionTransformer(
        img_size=img_size,
        patch_size=patch_size,
        in_channels=in_channels,
        num_classes=num_classes,
        embed_dim=embed_dim,
        num_heads=num_heads,
        num_layers=num_layers,
        mlp_hidden_dim=mlp_hidden_dim,
    )

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n模型总参数量: {total_params:,}")
    print(f"可训练参数量: {trainable_params:,}")

    # ---- 训练 ----
    model = train_model(model, train_loader, test_loader, num_epochs, lr, device)

    # ---- 验证模型结构 ----
    print("\n模型结构验证:")
    dummy_input = torch.randn(1, 3, 32, 32).to(device)
    with torch.no_grad():
        output = model(dummy_input)
    print(f"输入形状: {dummy_input.shape}")
    print(f"输出形状: {output.shape}")
    print(f"输出类别预测: {torch.argmax(output, dim=1).item()}")


if __name__ == "__main__":
    solve()

```
