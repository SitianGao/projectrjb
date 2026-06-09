# 深度学习基础

## 基本概念
- 神经网络由多层线性变换与非线性激活函数组成，能拟合复杂函数。
- 常用激活函数：ReLU、Sigmoid、Tanh、Softmax（分类输出）。

## 常见结构
- 前馈网络（MLP）、卷积神经网络（CNN，适合图像）、循环神经网络（RNN、LSTM，适合序列）
- 现代架构：Transformer（NLP 与多模态广泛使用）

## 训练要点
- 损失函数选择（分类用交叉熵，回归用 MSE）
- 批归一化（BatchNorm）、Dropout、优化器（Adam、SGD+momentum）
- 学习率调度、梯度裁剪、权重初始化

## 多模态与生成
- 多模态（图文/语音/视频）融合需要对不同模态做特征提取与对齐
- 生成模型（GAN、VAE、Autoregressive）在内容生成场景常见
