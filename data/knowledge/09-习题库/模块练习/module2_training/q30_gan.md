# 输入: (B, latent_dim, 1, 1)

> 来源模块: module2_training
> 原始文件: q30_gan.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】GAN生成对抗网络
【模块】模型训练与评估
【难度】9
【知识点】GAN、DCGAN、生成器、判别器、对抗训练、MNIST生成、PyTorch
【描述】
使用PyTorch实现DCGAN（深度卷积生成对抗网络），在MNIST数据集上训练，生成手写数字
图像。要求实现Generator和Discriminator网络，使用Binary Cross Entropy损失进行
对抗训练。

【要求】
1. 实现Generator：将随机噪声通过转置卷积层生成28x28的图像
2. 实现Discriminator：使用卷积层判断输入图像是真实的还是生成的
3. 实现DCGAN的训练循环（先训练D，再训练G）
4. 使用MNIST数据集训练
5. 定期保存生成的图像，展示训练过程中生成质量的提升
6. 使用BatchNorm和LeakyReLU等DCGAN推荐技巧

【提示】
- Generator使用ConvTranspose2d（转置卷积）
- Discriminator使用Conv2d + LeakyReLU
- 使用Adam优化器，lr=2e-4, beta1=0.5
- 权重初始化使用均值为0、标准差为0.02的正态分布
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.utils import save_image, make_grid
import numpy as np
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ------------------ 权重初始化 ------------------
def weights_init(m):
    """DCGAN权重初始化"""
    classname = m.__class__.__name__
    if classname.find("Conv") != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find("BatchNorm") != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)


# ------------------ 生成器 Generator ------------------
class Generator(nn.Module):
    """DCGAN生成器：将随机噪声生成28x28的图像"""

    def __init__(self, latent_dim=100, img_channels=1, base_features=64):
        super().__init__()
        # 输入: (B, latent_dim, 1, 1)
        # 目标: (B, 1, 28, 28)

        self.main = nn.Sequential(
            # -> (B, base_features*4, 4, 4)
            nn.ConvTranspose2d(latent_dim, base_features * 4, 4, 1, 0, bias=False),
            nn.BatchNorm2d(base_features * 4),
            nn.ReLU(True),

            # -> (B, base_features*2, 8, 8)
            nn.ConvTranspose2d(base_features * 4, base_features * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(base_features * 2),
            nn.ReLU(True),

            # -> (B, base_features, 16, 16)
            nn.ConvTranspose2d(base_features * 2, base_features, 4, 2, 1, bias=False),
            nn.BatchNorm2d(base_features),
            nn.ReLU(True),

            # -> (B, img_channels, 28, 28) -- 使用kernel=4,stride=1,padding=3: (16-1)*1-2*3+4=14? 不对
            # 使用kernel=3,stride=2,padding=1,output_padding=1: (16-1)*2-2*1+3+1=32? 不对
            # 直接用合适的参数: (16-1)*2-2*1+4+1 = 33? 也不对
            # 用 adaptive 或者直接调整: kernel=4, stride=2, padding=1 -> (16-1)*2-2+4=32 不对
            # 重新计算: output = (input-1)*stride - 2*padding + kernel_size + output_padding
            # (16-1)*2 - 2*1 + 4 + 1 = 30 - 2 + 4 + 1 = 33, 不对
            # 使用 nn.ConvTranspose2d(base_features, img_channels, 4, 2, 1) -> 32 不对
            # 直接使用: kernel=3, stride=1, padding=0 -> (16-1)*1-0+3 = 18 不对
            # 使用 kernel=4, stride=2, padding=1 -> (16-1)*2 - 2*1 + 4 = 32 不对
            # 方案：先到32x32再crop到28x28
            nn.ConvTranspose2d(base_features, img_channels, 4, 2, 1, bias=False),
            # 输出 32x32, 裁剪到 28x28
            nn.Tanh(),
        )

    def forward(self, z):
        # z: (B, latent_dim) -> (B, latent_dim, 1, 1)
        if z.dim() == 2:
            z = z.unsqueeze(-1).unsqueeze(-1)
        img = self.main(z)
        # 裁剪到28x28
        img = img[:, :, 2:30, 2:30]
        return img


# ------------------ 判别器 Discriminator ------------------
class Discriminator(nn.Module):
    """DCGAN判别器：判断图像是真实的还是生成的"""

    def __init__(self, img_channels=1, base_features=64):
        super().__init__()
        self.main = nn.Sequential(
            # (B, 1, 28, 28) -> (B, base_features, 14, 14)
            nn.Conv2d(img_channels, base_features, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),

            # -> (B, base_features*2, 7, 7)
            nn.Conv2d(base_features, base_features * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(base_features * 2),
            nn.LeakyReLU(0.2, inplace=True),

            # -> (B, base_features*4, 3, 3)
            nn.Conv2d(base_features * 2, base_features * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(base_features * 4),
            nn.LeakyReLU(0.2, inplace=True),

            # -> (B, 1, 1, 1)
            nn.Conv2d(base_features * 4, 1, 3, 1, 0, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, img):
        output = self.main(img)
        return output.view(-1)


# ------------------ 训练函数 ------------------
def train_gan(
    generator,
    discriminator,
    train_loader,
    num_epochs=20,
    latent_dim=100,
    lr=2e-4,
    beta1=0.5,
    device="cpu",
    save_dir="gan_outputs",
):
    """训练DCGAN"""
    os.makedirs(save_dir, exist_ok=True)

    # 损失函数
    criterion = nn.BCELoss()

    # 优化器
    opt_g = optim.Adam(generator.parameters(), lr=lr, betas=(beta1, 0.999))
    opt_d = optim.Adam(discriminator.parameters(), lr=lr, betas=(beta1, 0.999))

    # 固定噪声用于可视化训练过程
    fixed_noise = torch.randn(64, latent_dim, device=device)

    g_losses = []
    d_losses = []

    print("DCGAN 训练开始")
    print("=" * 60)

    for epoch in range(num_epochs):
        epoch_g_loss = 0.0
        epoch_d_loss = 0.0
        num_batches = 0

        for i, (real_imgs, _) in enumerate(train_loader):
            batch_size = real_imgs.size(0)
            real_imgs = real_imgs.to(device)

            # 真实和假标签
            real_labels = torch.ones(batch_size, device=device)
            fake_labels = torch.zeros(batch_size, device=device)

            # ==================== 训练判别器 ====================
            opt_d.zero_grad()

            # 真实图像的损失
            output_real = discriminator(real_imgs)
            loss_d_real = criterion(output_real, real_labels)

            # 生成假图像的损失
            noise = torch.randn(batch_size, latent_dim, device=device)
            fake_imgs = generator(noise)
            output_fake = discriminator(fake_imgs.detach())
            loss_d_fake = criterion(output_fake, fake_labels)

            loss_d = loss_d_real + loss_d_fake
            loss_d.backward()
            opt_d.step()

            # ==================== 训练生成器 ====================
            opt_g.zero_grad()

            # 生成器希望判别器将假图像判断为真
            output_fake = discriminator(fake_imgs)
            loss_g = criterion(output_fake, real_labels)
            loss_g.backward()
            opt_g.step()

            epoch_g_loss += loss_g.item()
            epoch_d_loss += loss_d.item()
            num_batches += 1

        avg_g_loss = epoch_g_loss / num_batches
        avg_d_loss = epoch_d_loss / num_batches
        g_losses.append(avg_g_loss)
        d_losses.append(avg_d_loss)

        # 保存生成图像
        if (epoch + 1) % 2 == 0 or epoch == 0:
            with torch.no_grad():
                fake_samples = generator(fixed_noise)
            save_path = os.path.join(save_dir, f"epoch_{epoch + 1:03d}.png")
            save_image(fake_samples[:16], save_path, nrow=4, normalize=True, value_range=(-1, 1))

            print(
                f"Epoch [{epoch + 1:2d}/{num_epochs}] | "
                f"D Loss: {avg_d_loss:.4f} | G Loss: {avg_g_loss:.4f}"
            )

    # ---- 训练损失曲线 ----
    plt.figure(figsize=(8, 4))
    plt.plot(g_losses, label="Generator Loss")
    plt.plot(d_losses, label="Discriminator Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("DCGAN Training Loss")
    plt.legend()
    plt.savefig(os.path.join(save_dir, "training_loss.png"), dpi=100, bbox_inches="tight")
    plt.close()

    # ---- 最终生成结果 ----
    with torch.no_grad():
        final_samples = generator(fixed_noise)
    grid = make_grid(final_samples[:64], nrow=8, normalize=True, value_range=(-1, 1))
    plt.figure(figsize=(8, 8))
    plt.imshow(grid.cpu().permute(1, 2, 0).squeeze(), cmap="gray")
    plt.axis("off")
    plt.title("DCGAN最终生成结果")
    plt.savefig(os.path.join(save_dir, "final_generation.png"), dpi=100, bbox_inches="tight")
    plt.close()

    print(f"\n生成结果已保存到: {save_dir}/")
    print(f"训练损失曲线: {save_dir}/training_loss.png")

    return generator, discriminator, g_losses, d_losses


# ------------------ 主函数 ------------------
def solve():
    """DCGAN完整演示"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # ---- 超参数 ----
    latent_dim = 100
    batch_size = 128
    num_epochs = 20
    lr = 2e-4
    base_features = 64

    # ---- 加载MNIST ----
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5]),  # 归一化到[-1, 1]
    ])

    data_root = os.path.join(os.path.dirname(__file__), "mnist_data")
    dataset = datasets.MNIST(root=data_root, train=True, download=True, transform=transform)
    train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    print(f"MNIST训练集大小: {len(dataset)}")

    # ---- 构建模型 ----
    generator = Generator(latent_dim=latent_dim, img_channels=1, base_features=base_features).to(device)
    discriminator = Discriminator(img_channels=1, base_features=base_features).to(device)

    # 权重初始化
    generator.apply(weights_init)
    discriminator.apply(weights_init)

    g_params = sum(p.numel() for p in generator.parameters())
    d_params = sum(p.numel() for p in discriminator.parameters())
    print(f"\nGenerator参数量: {g_params:,}")
    print(f"Discriminator参数量: {d_params:,}")

    # ---- 验证模型维度 ----
    test_noise = torch.randn(1, latent_dim).to(device)
    test_output = generator(test_noise)
    print(f"Generator输出形状: {test_output.shape}")  # 应为 (1, 1, 28, 28)

    test_disc = discriminator(test_output)
    print(f"Discriminator输出形状: {test_disc.shape}")  # 应为 (1,)

    # ---- 训练 ----
    save_dir = os.path.join(os.path.dirname(__file__), "gan_outputs")
    generator, discriminator, g_losses, d_losses = train_gan(
        generator, discriminator, train_loader,
        num_epochs=num_epochs, latent_dim=latent_dim,
        lr=lr, device=device, save_dir=save_dir,
    )

    # ---- 插值演示 ----
    print("\n隐空间插值演示:")
    with torch.no_grad():
        z1 = torch.randn(1, latent_dim, device=device)
        z2 = torch.randn(1, latent_dim, device=device)
        # 在两个随机噪声之间做线性插值
        n_interp = 8
        interpolations = []
        for t in np.linspace(0, 1, n_interp):
            z_interp = z1 * (1 - t) + z2 * t
            interp_img = generator(z_interp)
            interpolations.append(interp_img)

        interp_tensor = torch.cat(interpolations, dim=0)
        grid = make_grid(interp_tensor, nrow=n_interp, normalize=True, value_range=(-1, 1))
        plt.figure(figsize=(12, 2))
        plt.imshow(grid.cpu().permute(1, 2, 0).squeeze(), cmap="gray")
        plt.axis("off")
        plt.title("隐空间线性插值")
        plt.savefig(os.path.join(save_dir, "interpolation.png"), dpi=100, bbox_inches="tight")
        plt.close()
        print(f"插值结果已保存: {save_dir}/interpolation.png")

    print("\nDCGAN演示完成。")


if __name__ == "__main__":
    solve()

```
