# 蓝桥杯AI题库 - README.md

> 来源模块: README.md
> 原始文件: README.md

## 题目代码

```python
# 蓝桥杯 AI 应用备课题目

基于第十七届蓝桥杯大赛人工智能赛（人工智能应用）竞赛大纲，49 道编程实现题，覆盖全部考点。

## 题目索引

### 模块 1：数据预处理

| # | 文件 | 题目 | 难度 | 知识点 |
|---|------|------|:----:|--------|
| 01 | q01_minmax_normalization.py | Min-Max归一化实现与验证 | 1 | Min-Max归一化、numpy、sklearn MinMaxScaler |
| 02 | q02_zscore_maxabs.py | Z-Score标准化与MaxAbs标准化 | 2 | Z-Score、MaxAbsScaler、StandardScaler |
| 03 | q03_log_l2_normalize.py | Log/Logistic归一化与L2向量单位化 | 2 | 对数归一化、Logistic归一化、L2-normalize |
| 04 | q04_missing_values.py | 缺失值处理：均值/中位数/众数/插值 | 3 | pandas缺失值、均值/中位数/众数填充、线性插值 |
| 05 | q05_duplicate_handling.py | 重复值检测与处理 | 2 | duplicated、drop_duplicates、重复值分析 |
| 06 | q06_noise_smoothing.py | 噪声信号平滑处理 | 3 | 移动平均、中值滤波、Savitzky-Golay滤波 |
| 07 | q07_outlier_detection.py | 异常值检测：IQR与Z-Score | 5 | IQR四分位距法、Z-Score方法、箱线图 |
| 08 | q08_text_cleaning_jieba.py | 中文文本清洗与jieba分词 | 3 | 正则去噪、HTML/URL去除、jieba分词、停用词 |
| 09 | q09_encoding_conversion.py | 统一编码处理 | 3 | UTF-8校验、大小写转换、繁简映射 |
| 10 | q10_image_cleaning.py | 图像数据清洗 | 4 | OpenCV、Pillow、缺失插值、噪声平滑、颜色空间、尺寸统一 |
| 11 | q11_tfidf_feature.py | TF-IDF特征提取 | 3 | TF-IDF原理、词频、逆文档频率、TfidfVectorizer |
| 12 | q12_word2vec.py | Word2Vec Skip-gram | 5 | Skip-gram、词向量、负采样、PyTorch |
| 13 | q13_image_features.py | 图像特征提取：传统+CNN | 6 | HOG、SIFT、预训练CNN、torchvision |
| 14 | q14_pca_lda_svd.py | 降维与特征选择 | 5 | PCA、LDA、SVD、卡方检验、sklearn降维 |

### 模块 2：模型训练与评估

| # | 文件 | 题目 | 难度 | 知识点 |
|---|------|------|:----:|--------|
| 15 | q15_linear_models.py | 线性模型全家桶 | 3 | OLS、Ridge、Lasso、多项式回归、MSE、R² |
| 16 | q16_logistic_regression.py | 逻辑回归手动实现 | 3 | 梯度下降、Sigmoid、交叉熵、二分类 |
| 17 | q17_decision_tree_random_forest.py | 决策树与随机森林 | 4 | 决策树、随机森林、特征重要性、交叉验证 |
| 18 | q18_adaboost_xgboost.py | AdaBoost与XGBoost | 5 | AdaBoost、XGBoost、集成学习、学习曲线 |
| 19 | q19_naive_bayes.py | 朴素贝叶斯文本分类 | 5 | 多项式NB、词袋模型、拉普拉斯平滑 |
| 20 | q20_clustering.py | 聚类算法对比 | 4 | K-Means(手动)、层次聚类、DBSCAN、轮廓系数 |
| 21 | q21_lenet5.py | LeNet-5 CNN | 4 | CNN、卷积层、池化层、MNIST、PyTorch |
| 22 | q22_vgg_resnet.py | VGG和ResNet | 6 | VGG、ResNet、残差块、批归一化、CIFAR-10 |
| 23 | q23_mobilenet.py | MobileNet深度可分离卷积 | 7 | 深度可分离卷积、Depthwise、Pointwise |
| 24 | q24_yolo.py | YOLO目标检测简化版 | 8 | YOLO、网格划分、锚框、置信度、边界框回归、NMS |
| 25 | q25_rnn_birnn.py | RNN/Bi-RNN | 6 | RNN、双向RNN、序列预测、隐藏状态、梯度裁剪 |
| 26 | q26_lstm_gru.py | LSTM/GRU文本分类 | 7 | LSTM、GRU、门控机制、词嵌入、情感分析 |
| 27 | q27_bert_finetune.py | BERT文本分类微调 | 9 | BERT、transformers、Tokenizer、微调训练 |
| 28 | q28_vit.py | Vision Transformer | 9 | ViT、Patch Embedding、Transformer Encoder |
| 29 | q29_ae_vae.py | 自编码器AE与VAE | 7 | AE、VAE、重建损失、KL散度、MNIST生成 |
| 30 | q30_gan.py | GAN生成对抗网络 | 9 | DCGAN、生成器、判别器、对抗训练 |
| 31 | q31_diffusion.py | 扩散模型 | 10 | DDPM、前向加噪、反向去噪、噪声调度 |
| 32 | q32_qlearning_dqn.py | Q-Learning/SARSA/DQN | 6 | Q-Learning、SARSA、DQN、经验回放 |
| 33 | q33_ppo.py | PPO策略优化 | 8 | PPO、Actor-Critic、策略梯度、GAE |
| 34 | q34_genetic_pso.py | 遗传算法与粒子群优化 | 8 | 遗传算法、PSO、适应度函数、函数优化 |
| 35 | q35_pipeline_gridsearch.py | sklearn Pipeline与调参 | 4 | Pipeline、GridSearchCV、RandomizedSearchCV |
| 36 | q36_model_persistence.py | 模型持久化与特征选择 | 4 | joblib、pickle、SelectKBest、RFE |
| 37 | q37_pytorch_basics.py | PyTorch基础 | 3 | Tensor、Dataset、DataLoader、autograd |
| 38 | q38_pytorch_training.py | PyTorch完整训练流程 | 5 | nn.Module、nn.Sequential、SGD/Adam、StepLR、state_dict |
| 39 | q39_evaluation_metrics.py | 评估指标全面实现 | 3 | accuracy/precision/recall/F1/AUC/R²/MSE/RMSE/MAE/MAPE |
| 40 | q40_loss_functions.py | 损失函数手动实现 | 4 | CrossEntropy、FocalLoss、IoU/Dice/CTC Loss |
| 41 | q41_imbalanced_sampling.py | 不均衡数据采样 | 5 | 过采样、欠采样、WeightedRandomSampler |

### 模块 3：模型应用部署

| # | 文件 | 题目 | 难度 | 知识点 |
|---|------|------|:----:|--------|
| 42 | q42_pytorch_onnx.py | PyTorch→ONNX转换 | 6 | torch.onnx.export、onnxruntime推理 |
| 43 | q43_sklearn_onnx.py | sklearn→ONNX转换 | 5 | skl2onnx、Pipeline转换、onnxruntime验证 |
| 44 | q44_pruning.py | 模型剪枝 | 8 | 非结构化剪枝、通道剪枝、稀疏度分析 |
| 45 | q45_quantization.py | 模型量化 | 7 | 动态量化、静态量化、INT8校准 |
| 46 | q46_flask_deploy.py | Flask模型部署 | 5 | Flask路由、模型单例、懒加载、批量处理 |
| 47 | q47_postprocess_classification.py | 分类/回归后处理 | 3 | Softmax、Top-K、反归一化、模型融合 |
| 48 | q48_postprocess_detection.py | 检测与文本后处理 | 4 | NMS、Soft-NMS、Beam Search、CTC解码 |
| 49 | q49_opencv_inference.py | OpenCV DNN推理 | 6 | cv2.dnn、ONNX模型加载与推理 |

## 使用方法

```bash
# 运行单道题
python exam_questions/module1_preprocessing/q01_minmax_normalization.py

# 批量验证
for f in exam_questions/**/*.py; do python "$f"; done
```

```