# 线性beta调度

> 来源模块: module2_training
> 原始文件: q31_diffusion.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】扩散模型简化实现
【模块】模型训练与评估
【难度】10
【知识点】扩散模型、前向加噪、反向去噪、U-Net、DDPM、噪声调度、PyTorch
【描述】
使用PyTorch实现简化版扩散模型（Denoising Diffusion Probabilistic Models, DDPM），
包括前向加噪过程和反向去噪过程。在2D点云数据上演示扩散模型的生成能力。

【要求】
1. 实现线性噪声调度（beta schedule）
2. 实现前向扩散过程：逐步向数据添加高斯噪声
3. 实现简化的噪声预测网络（MLP结构用于2D点云数据）
4. 实现反向去噪采样过程
5. 在2D瑞士卷(Swiss Roll)点云数据上训练
6. 可视化前向加噪过程和反向生成过程

【提示】
- 前向过程: x_t = sqrt(alpha_bar_t) * x_0 + sqrt(1 - alpha_bar_t) * noise
- 反向过程: x_{t-1} = (1/sqrt(alpha_t)) * (x_t - beta_t/sqrt(1-alpha_bar_t) * model(x_t, t)) + sigma_t * z
- alpha_t = 1 - beta_t, alpha_bar_t = cumulative product of alpha_t
- 使用简化的MLP网络而非完整U-Net
=============================
"""

# ========== 参考答案 ==========

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os


# ======================== 噪声调度器 ========================

class LinearBetaSchedule:
    """线性噪声调度"""

    def __init__(self, num_timesteps=200, beta_start=1e-4, beta_end=0.02):
        self.num_timesteps = num_timesteps

        # 线性beta调度
        self.betas = torch.linspace(beta_start, beta_end, num_timesteps)
        self.alphas = 1.0 - self.betas
        self.alpha_bars = torch.cumprod(self.alphas, dim=0)

        # 预计算常用量
        self.sqrt_alpha_bars = torch.sqrt(self.alpha_bars)
        self.sqrt_one_minus_alpha_bars = torch.sqrt(1.0 - self.alpha_bars)
        self.sqrt_recip_alphas = torch.sqrt(1.0 / self.alphas)

        # 后验方差
        self.posterior_variance = (
            self.betas * (1.0 - torch.cat([torch.tensor([1.0]), self.alpha_bars[:-1]]))
            / (1.0 - self.alpha_bars)
        )


# ======================== 噪声预测网络 ========================

class SinusoidalTimeEmbedding(nn.Module):
    """正弦时间嵌入"""

    def __init__(self, dim):
        super().__init__()
        self.dim = dim

    def forward(self, t):
        device = t.device
        half_dim = self.dim // 2
        emb = np.log(10000) / (half_dim - 1)
        emb = torch.exp(torch.arange(half_dim, device=device, dtype=torch.float32) * -emb)
        emb = t.float().unsqueeze(-1) * emb.unsqueeze(0)
        emb = torch.cat([torch.sin(emb), torch.cos(emb)], dim=-1)
        return emb


class NoisePredictor(nn.Module):
    """用于2D点云的噪声预测网络（简化版）"""

    def __init__(self, data_dim=2, hidden_dim=128, time_dim=64):
        super().__init__()

        self.time_mlp = nn.Sequential(
            SinusoidalTimeEmbedding(time_dim),
            nn.Linear(time_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

        self.input_proj = nn.Linear(data_dim, hidden_dim)

        self.net = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, data_dim),
        )

    def forward(self, x, t):
        """
        Args:
            x: (B, data_dim) 带噪声的数据
            t: (B,) 时间步
        Returns:
            预测的噪声 (B, data_dim)
        """
        t_emb = self.time_mlp(t)  # (B, hidden_dim)
        x_emb = self.input_proj(x)  # (B, hidden_dim)
        h = torch.cat([x_emb, t_emb], dim=-1)  # (B, hidden_dim*2)
        return self.net(h)


# ======================== 扩散模型 ========================

class DiffusionModel:
    """DDPM扩散模型"""

    def __init__(self, model, schedule, data_dim=2):
        self.model = model
        self.schedule = schedule
        self.data_dim = data_dim

    def forward_process(self, x_0, t, noise=None):
        """前向扩散过程：在给定时间步t给x_0加噪"""
        if noise is None:
            noise = torch.randn_like(x_0)

        sqrt_alpha_bar_t = self.schedule.sqrt_alpha_bars[t].unsqueeze(-1).to(x_0.device)
        sqrt_one_minus_alpha_bar_t = self.schedule.sqrt_one_minus_alpha_bars[t].unsqueeze(-1).to(x_0.device)

        x_t = sqrt_alpha_bar_t * x_0 + sqrt_one_minus_alpha_bar_t * noise
        return x_t

    def train_loss(self, x_0):
        """计算训练损失"""
        batch_size = x_0.shape[0]
        device = x_0.device
        num_t = self.schedule.num_timesteps

        # 随机采样时间步
        t = torch.randint(0, num_t, (batch_size,), device=device)

        # 采样噪声
        noise = torch.randn_like(x_0)

        # 前向加噪
        x_t = self.forward_process(x_0, t, noise)

        # 预测噪声
        noise_pred = self.model(x_t, t)

        # MSE损失
        loss = F.mse_loss(noise_pred, noise)
        return loss

    @torch.no_grad()
    def sample(self, num_samples, device):
        """反向去噪采样"""
        num_t = self.schedule.num_timesteps

        # 从纯噪声开始
        x = torch.randn(num_samples, self.data_dim, device=device)

        trajectory = [x.cpu().clone()]

        # 逐步去噪
        for t_idx in reversed(range(num_t)):
            t = torch.full((num_samples,), t_idx, device=device, dtype=torch.long)

            # 预测噪声
            noise_pred = self.model(x, t)

            # 去噪步骤
            alpha_t = self.schedule.alphas[t_idx].to(device)
            alpha_bar_t = self.schedule.alpha_bars[t_idx].to(device)
            beta_t = self.schedule.betas[t_idx].to(device)

            # 均值
            x_mean = (
                1.0 / torch.sqrt(alpha_t)
                * (x - beta_t / torch.sqrt(1.0 - alpha_bar_t) * noise_pred)
            )

            # 添加噪声（除了t=0）
            if t_idx > 0:
                noise = torch.randn_like(x)
                sigma_t = torch.sqrt(self.schedule.posterior_variance[t_idx]).to(device)
                x = x_mean + sigma_t * noise
            else:
                x = x_mean

            # 每隔一定步数记录轨迹
            if t_idx % (num_t // 10) == 0 or t_idx == 0:
                trajectory.append(x.cpu().clone())

        return x, trajectory


# ======================== 数据生成 ========================

def generate_swiss_roll(n_samples=2000, noise_std=0.05):
    """生成瑞士卷2D点云数据"""
    t = 1.5 * np.pi * (1 + 2 * np.random.rand(n_samples))
    x = t * np.cos(t) + np.random.randn(n_samples) * noise_std
    y = t * np.sin(t) + np.random.randn(n_samples) * noise_std
    data = np.stack([x, y], axis=1).astype(np.float32)
    # 归一化到[-1, 1]
    data = (data - data.mean(axis=0)) / (data.std(axis=0) + 1e-8)
    data = data / (np.abs(data).max() + 1e-8)
    return data


# ======================== 可视化 ========================

def visualize_forward_process(data, schedule, save_path="diffusion_forward.png"):
    """可视化前向加噪过程"""
    device = torch.device("cpu")
    x_0 = torch.tensor(data[:500])

    timesteps_to_show = [0, 20, 50, 100, 150, 199]
    fig, axes = plt.subplots(1, len(timesteps_to_show), figsize=(3 * len(timesteps_to_show), 3))

    for i, t_val in enumerate(timesteps_to_show):
        t = torch.full((500,), t_val, dtype=torch.long)
        noise = torch.randn_like(x_0)
        x_t = schedule.sqrt_alpha_bars[t].unsqueeze(-1) * x_0 + schedule.sqrt_one_minus_alpha_bars[t].unsqueeze(-1) * noise
        x_np = x_t.numpy()

        axes[i].scatter(x_np[:, 0], x_np[:, 1], s=1, alpha=0.5)
        axes[i].set_xlim(-3, 3)
        axes[i].set_ylim(-3, 3)
        axes[i].set_title(f"t={t_val}")
        axes[i].set_aspect("equal")

    plt.suptitle("前向加噪过程", fontsize=14)
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"前向过程可视化已保存: {save_path}")


def visualize_reverse_process(trajectory, save_path="diffusion_reverse.png"):
    """可视化反向去噪过程"""
    n_steps = len(trajectory)
    fig, axes = plt.subplots(1, n_steps, figsize=(3 * n_steps, 3))

    for i, x_t in enumerate(trajectory):
        x_np = x_t.numpy()
        axes[i].scatter(x_np[:, 0], x_np[:, 1], s=1, alpha=0.5)
        axes[i].set_xlim(-3, 3)
        axes[i].set_ylim(-3, 3)
        step_label = f"t={200 - i * (200 // max(n_steps - 1, 1))}" if i > 0 else "t=200"
        if i == n_steps - 1:
            step_label = "t=0 (生成)"
        axes[i].set_title(step_label, fontsize=10)
        axes[i].set_aspect("equal")

    plt.suptitle("反向去噪过程", fontsize=14)
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"反向过程可视化已保存: {save_path}")


# ======================== 主函数 ========================

def solve():
    """扩散模型完整演示"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    output_dir = os.path.dirname(__file__) or "."

    # ---- 超参数 ----
    num_timesteps = 200
    batch_size = 256
    num_epochs = 100
    learning_rate = 3e-4
    hidden_dim = 128

    # ---- 生成数据 ----
    print("\n生成瑞士卷点云数据...")
    np.random.seed(42)
    data = generate_swiss_roll(n_samples=3000)
    data_tensor = torch.tensor(data)
    print(f"数据形状: {data.shape}")

    # ---- 噪声调度 ----
    schedule = LinearBetaSchedule(num_timesteps=num_timesteps, beta_start=1e-4, beta_end=0.02)

    # 可视化前向过程
    visualize_forward_process(data, schedule, save_path=os.path.join(output_dir, "diffusion_forward.png"))

    # ---- 构建模型 ----
    model = NoisePredictor(data_dim=2, hidden_dim=hidden_dim, time_dim=64).to(device)
    diffusion = DiffusionModel(model, schedule, data_dim=2)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n模型参数量: {total_params:,}")
    print(f"扩散步数: {num_timesteps}")

    # ---- 训练 ----
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    print("\n开始训练扩散模型...")
    print("=" * 50)

    dataset = torch.utils.data.TensorDataset(data_tensor)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    for epoch in range(num_epochs):
        epoch_loss = 0.0
        num_batches = 0
        for (batch_x,) in dataloader:
            batch_x = batch_x.to(device)
            loss = diffusion.train_loss(batch_x)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            num_batches += 1

        avg_loss = epoch_loss / num_batches
        if (epoch + 1) % 20 == 0 or epoch == 0:
            print(f"Epoch [{epoch + 1:3d}/{num_epochs}] Loss: {avg_loss:.6f}")

    print("=" * 50)

    # ---- 采样生成 ----
    print("\n开始采样生成...")
    model.eval()
    samples, trajectory = diffusion.sample(num_samples=1000, device=device)
    samples_np = samples.cpu().numpy()

    # ---- 可视化生成结果 ----
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 原始数据
    axes[0].scatter(data[:, 0], data[:, 1], s=1, alpha=0.5, c="blue")
    axes[0].set_title("原始瑞士卷数据")
    axes[0].set_xlim(-3, 3)
    axes[0].set_ylim(-3, 3)
    axes[0].set_aspect("equal")

    # 生成数据
    axes[1].scatter(samples_np[:, 0], samples_np[:, 1], s=1, alpha=0.5, c="red")
    axes[1].set_title("扩散模型生成数据")
    axes[1].set_xlim(-3, 3)
    axes[1].set_ylim(-3, 3)
    axes[1].set_aspect("equal")

    # 对比
    axes[2].scatter(data[:, 0], data[:, 1], s=1, alpha=0.3, c="blue", label="真实")
    axes[2].scatter(samples_np[:, 0], samples_np[:, 1], s=1, alpha=0.3, c="red", label="生成")
    axes[2].set_title("真实 vs 生成 对比")
    axes[2].set_xlim(-3, 3)
    axes[2].set_ylim(-3, 3)
    axes[2].set_aspect("equal")
    axes[2].legend()

    plt.suptitle("扩散模型 (DDPM) - 瑞士卷数据生成", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "diffusion_results.png"), dpi=100, bbox_inches="tight")
    plt.close()
    print(f"生成结果已保存: {os.path.join(output_dir, 'diffusion_results.png')}")

    # 可视化反向过程
    visualize_reverse_process(trajectory, save_path=os.path.join(output_dir, "diffusion_reverse.png"))

    print("\n扩散模型演示完成。")


if __name__ == "__main__":
    solve()

```
