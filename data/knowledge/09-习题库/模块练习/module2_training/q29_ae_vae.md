# 编码器

> 来源模块: module2_training
> 原始文件: q29_ae_vae.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】自编码器AE与变分自编码器VAE
【模块】模型训练与评估
【难度】7
【知识点】自编码器、变分自编码器、重建损失、KL散度、MNIST、PyTorch
【描述】
使用PyTorch实现普通自编码器（AE）和变分自编码器（VAE），在MNIST数据集上训练，
对比两者的重建质量，并演示VAE的生成能力（从隐空间采样生成新图像）。

【要求】
1. 实现AE（Encoder + Decoder），使用全连接层
2. 实现VAE（Encoder输出均值和方差 + 重参数化技巧 + Decoder）
3. AE使用MSE重建损失，VAE使用重建损失 + KL散度
4. 在MNIST上训练两个模型，对比重建效果
5. 使用VAE从隐空间随机采样生成新图像
6. 可视化重建结果和VAE生成结果

【提示】
- VAE使用重参数化技巧：z = mu + std * epsilon
- KL散度公式：-0.5 * sum(1 + log_var - mu^2 - exp(log_var))
- 使用torchvision加载MNIST数据集
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os


# ------------------ 自编码器 AE ------------------
class Autoencoder(nn.Module):
    """普通自编码器"""

    def __init__(self, input_dim=784, hidden_dim=256, latent_dim=32):
        super().__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )
        self.fc_latent = nn.Linear(hidden_dim // 2, latent_dim)

        # Decoder
        self.decoder_input = nn.Linear(latent_dim, hidden_dim // 2)
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
            nn.Sigmoid(),
        )

    def encode(self, x):
        h = self.encoder(x)
        z = self.fc_latent(h)
        return z

    def decode(self, z):
        h = self.decoder_input(z)
        x_recon = self.decoder(h)
        return x_recon

    def forward(self, x):
        z = self.encode(x)
        x_recon = self.decode(z)
        return x_recon, z


# ------------------ 变分自编码器 VAE ------------------
class VariationalAutoencoder(nn.Module):
    """变分自编码器"""

    def __init__(self, input_dim=784, hidden_dim=256, latent_dim=32):
        super().__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )
        self.fc_mu = nn.Linear(hidden_dim // 2, latent_dim)
        self.fc_log_var = nn.Linear(hidden_dim // 2, latent_dim)

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
            nn.Sigmoid(),
        )

    def encode(self, x):
        h = self.encoder(x)
        mu = self.fc_mu(h)
        log_var = self.fc_log_var(h)
        return mu, log_var

    def reparameterize(self, mu, log_var):
        """重参数化技巧"""
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        z = mu + eps * std
        return z

    def decode(self, z):
        return self.decoder(z)

    def forward(self, x):
        mu, log_var = self.encode(x)
        z = self.reparameterize(mu, log_var)
        x_recon = self.decode(z)
        return x_recon, mu, log_var, z

    def loss_function(self, x_recon, x, mu, log_var):
        """VAE损失 = 重建损失 + KL散度"""
        # 重建损失（BCE）
        recon_loss = F.binary_cross_entropy(x_recon, x, reduction="sum")
        # KL散度
        kl_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())
        total_loss = recon_loss + kl_loss
        return total_loss, recon_loss, kl_loss


# ------------------ 训练函数 ------------------
def train_ae(model, train_loader, num_epochs=10, lr=1e-3, device="cpu"):
    """训练自编码器"""
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    print("AE 训练开始:")
    for epoch in range(num_epochs):
        total_loss = 0
        num_batches = 0
        for batch_x, _ in train_loader:
            batch_x = batch_x.view(batch_x.size(0), -1).to(device)

            optimizer.zero_grad()
            x_recon, _ = model(batch_x)
            loss = criterion(x_recon, batch_x)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"  Epoch [{epoch + 1}/{num_epochs}] Loss: {avg_loss:.6f}")

    return model


def train_vae(model, train_loader, num_epochs=10, lr=1e-3, device="cpu"):
    """训练变分自编码器"""
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    print("VAE 训练开始:")
    for epoch in range(num_epochs):
        total_loss = 0
        total_recon = 0
        total_kl = 0
        num_batches = 0

        for batch_x, _ in train_loader:
            batch_x = batch_x.view(batch_x.size(0), -1).to(device)

            optimizer.zero_grad()
            x_recon, mu, log_var, _ = model(batch_x)
            loss, recon_loss, kl_loss = model.loss_function(x_recon, batch_x, mu, log_var)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            total_recon += recon_loss.item()
            total_kl += kl_loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        avg_recon = total_recon / num_batches
        avg_kl = total_kl / num_batches

        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(
                f"  Epoch [{epoch + 1}/{num_epochs}] "
                f"Loss: {avg_loss:.1f} | Recon: {avg_recon:.1f} | KL: {avg_kl:.1f}"
            )

    return model


# ------------------ 可视化函数 ------------------
def visualize_reconstruction(model_ae, model_vae, test_loader, device, save_path="ae_vae_reconstruction.png"):
    """可视化AE和VAE的重建结果"""
    model_ae.eval()
    model_vae.eval()

    # 获取一批测试数据
    images, _ = next(iter(test_loader))
    images_flat = images.view(images.size(0), -1).to(device)
    n = min(8, images.size(0))

    with torch.no_grad():
        ae_recon, _ = model_ae(images_flat[:n])
        vae_recon, _, _, _ = model_vae(images_flat[:n])

    ae_recon = ae_recon.cpu().view(-1, 28, 28).numpy()
    vae_recon = vae_recon.cpu().view(-1, 28, 28).numpy()
    originals = images[:n].numpy()

    fig, axes = plt.subplots(3, n, figsize=(2 * n, 6))
    for i in range(n):
        axes[0, i].imshow(originals[i][0], cmap="gray")
        axes[0, i].axis("off")
        if i == 0:
            axes[0, i].set_title("原始", fontsize=10)

        axes[1, i].imshow(ae_recon[i], cmap="gray")
        axes[1, i].axis("off")
        if i == 0:
            axes[1, i].set_title("AE重建", fontsize=10)

        axes[2, i].imshow(vae_recon[i], cmap="gray")
        axes[2, i].axis("off")
        if i == 0:
            axes[2, i].set_title("VAE重建", fontsize=10)

    plt.suptitle("AE vs VAE 重建对比", fontsize=14)
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"重建对比图已保存: {save_path}")


def visualize_vae_generation(model_vae, device, n_samples=16, save_path="vae_generation.png"):
    """从VAE隐空间采样生成新图像"""
    model_vae.eval()
    latent_dim = model_vae.fc_mu.out_features

    with torch.no_grad():
        z = torch.randn(n_samples, latent_dim).to(device)
        generated = model_vae.decode(z).cpu().view(-1, 28, 28).numpy()

    n_rows = int(np.ceil(np.sqrt(n_samples)))
    n_cols = int(np.ceil(n_samples / n_rows))

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(2 * n_cols, 2 * n_rows))
    for idx in range(n_samples):
        r, c = idx // n_cols, idx % n_cols
        if n_rows == 1:
            ax = axes[c]
        elif n_cols == 1:
            ax = axes[r]
        else:
            ax = axes[r, c]
        ax.imshow(generated[idx], cmap="gray")
        ax.axis("off")

    plt.suptitle("VAE 随机采样生成", fontsize=14)
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"VAE生成图已保存: {save_path}")


def visualize_latent_space(model_vae, test_loader, device, save_path="vae_latent_space.png"):
    """可视化VAE隐空间（使用前2个维度）"""
    model_vae.eval()
    all_mu = []
    all_labels = []

    with torch.no_grad():
        for images, labels in test_loader:
            images_flat = images.view(images.size(0), -1).to(device)
            mu, _ = model_vae.encode(images_flat)
            all_mu.append(mu.cpu().numpy())
            all_labels.append(labels.numpy())

    all_mu = np.concatenate(all_mu, axis=0)
    all_labels = np.concatenate(all_labels, axis=0)

    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(all_mu[:, 0], all_mu[:, 1], c=all_labels, cmap="tab10", alpha=0.5, s=1)
    plt.colorbar(scatter, label="数字类别")
    plt.xlabel("隐变量维度1")
    plt.ylabel("隐变量维度2")
    plt.title("VAE 隐空间可视化")
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"隐空间图已保存: {save_path}")


# ------------------ 主函数 ------------------
def solve():
    """AE与VAE完整演示"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # ---- 超参数 ----
    batch_size = 128
    num_epochs = 10
    learning_rate = 1e-3
    latent_dim = 32

    # ---- 加载MNIST数据 ----
    transform = transforms.Compose([transforms.ToTensor()])

    data_root = os.path.join(os.path.dirname(__file__), "mnist_data")
    train_dataset = datasets.MNIST(root=data_root, train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root=data_root, train=False, download=True, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    print(f"训练集大小: {len(train_dataset)}, 测试集大小: {len(test_dataset)}")

    # ---- 构建并训练AE ----
    print("\n" + "=" * 50)
    ae_model = Autoencoder(input_dim=784, hidden_dim=256, latent_dim=latent_dim)
    ae_params = sum(p.numel() for p in ae_model.parameters())
    print(f"AE参数量: {ae_params:,}")
    ae_model = train_ae(ae_model, train_loader, num_epochs=num_epochs, lr=learning_rate, device=device)

    # ---- 构建并训练VAE ----
    print("\n" + "=" * 50)
    vae_model = VariationalAutoencoder(input_dim=784, hidden_dim=256, latent_dim=latent_dim)
    vae_params = sum(p.numel() for p in vae_model.parameters())
    print(f"VAE参数量: {vae_params:,}")
    vae_model = train_vae(vae_model, train_loader, num_epochs=num_epochs, lr=learning_rate, device=device)

    # ---- 计算重建误差对比 ----
    print("\n" + "=" * 50)
    print("重建误差对比:")
    ae_model.eval()
    vae_model.eval()
    ae_errors = []
    vae_errors = []

    with torch.no_grad():
        for images, _ in test_loader:
            images_flat = images.view(images.size(0), -1).to(device)
            ae_recon, _ = ae_model(images_flat)
            vae_recon, _, _, _ = vae_model(images_flat)

            ae_err = F.mse_loss(ae_recon, images_flat).item()
            vae_err = F.mse_loss(vae_recon, images_flat).item()
            ae_errors.append(ae_err)
            vae_errors.append(vae_err)

    print(f"  AE 平均重建MSE:  {np.mean(ae_errors):.6f}")
    print(f"  VAE 平均重建MSE: {np.mean(vae_errors):.6f}")

    # ---- 可视化 ----
    output_dir = os.path.dirname(__file__) or "."
    visualize_reconstruction(
        ae_model, vae_model, test_loader, device,
        save_path=os.path.join(output_dir, "ae_vae_reconstruction.png"),
    )
    visualize_vae_generation(
        vae_model, device, n_samples=16,
        save_path=os.path.join(output_dir, "vae_generation.png"),
    )
    visualize_latent_space(
        vae_model, test_loader, device,
        save_path=os.path.join(output_dir, "vae_latent_space.png"),
    )

    print("\n演示完成。AE与VAE的训练、重建对比和VAE生成均已展示。")


if __name__ == "__main__":
    solve()

```
