# 类别0: 科技类新闻, 类别1: 体育类新闻

> 来源模块: module2_training
> 原始文件: q27_bert_finetune.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】BERT文本分类微调
【模块】模型训练与评估
【难度】9
【知识点】BERT、transformers库、文本分类、Tokenizer、Dataset构建、微调训练、评估指标
【描述】
使用transformers库加载预训练BERT模型（bert-base-chinese），在小样本中文文本数据上
进行微调，完成文本分类任务。要求完整实现tokenizer处理、自定义Dataset构建、训练循环
和模型评估。

【要求】
1. 使用transformers的BertTokenizer和BertForSequenceClassification加载预训练模型
2. 构建自定义PyTorch Dataset类处理文本数据
3. 实现完整的训练循环（前向传播、损失计算、反向传播、参数更新）
4. 实现评估函数，计算准确率、精确率、召回率、F1值
5. 使用小样本数据（约40条）演示完整流程，包含2个类别
6. 训练结束后展示分类报告

【提示】
- 使用transformers库的AdamW优化器
- 注意GPU/CPU设备的兼容处理
- 可以构造模拟的中文文本数据用于演示
=============================
"""

# ========== 参考答案 ==========

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report


# ------------------ 自定义数据集 ------------------
class TextClassificationDataset(Dataset):
    """BERT文本分类数据集"""

    def __init__(self, texts, labels, tokenizer, max_length=128):
        """
        Args:
            texts: 文本列表
            labels: 标签列表
            tokenizer: BERT tokenizer
            max_length: 最大序列长度
        """
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "token_type_ids": encoding.get("token_type_ids", torch.zeros(self.max_length, dtype=torch.long)),
            "labels": torch.tensor(label, dtype=torch.long),
        }


# ------------------ 评估函数 ------------------
def compute_metrics(predictions, labels):
    """计算分类评估指标"""
    acc = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="weighted", zero_division=0
    )
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def evaluate(model, dataloader, device):
    """评估模型"""
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            token_type_ids = batch["token_type_ids"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
            )

            logits = outputs.logits
            preds = torch.argmax(logits, dim=-1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    metrics = compute_metrics(all_preds, all_labels)
    return metrics, all_preds, all_labels


# ------------------ 训练函数 ------------------
def train_epoch(model, dataloader, optimizer, device):
    """训练一个epoch"""
    model.train()
    total_loss = 0
    num_batches = 0

    for batch in dataloader:
        optimizer.zero_grad()

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        token_type_ids = batch["token_type_ids"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            labels=labels,
        )

        loss = outputs.loss
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return total_loss / num_batches


# ------------------ 主函数 ------------------
def solve():
    """BERT文本分类微调完整流程"""
    # 设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # ---- 构造模拟中文文本数据 ----
    # 类别0: 科技类新闻, 类别1: 体育类新闻
    train_texts = [
        "人工智能技术正在改变我们的生活方式",
        "深度学习模型在图像识别领域取得突破",
        "5G网络将带来更快的互联网体验",
        "量子计算机有望解决复杂计算问题",
        "自动驾驶技术依赖传感器和AI算法",
        "区块链技术在金融领域有广泛应用",
        "云计算平台为企业提供弹性计算资源",
        "芯片制造工艺不断突破物理极限",
        "机器学习算法可以从数据中自动学习规律",
        "物联网设备连接了数十亿终端设备",
        "虚拟现实技术正在改变娱乐产业格局",
        "大数据分析帮助企业做出精准决策",
        "自然语言处理让计算机理解人类语言",
        "计算机视觉技术在安防领域广泛应用",
        "人脸识别技术已经非常成熟",
        "智能音箱成为家庭中常见的AI设备",
        "新能源汽车带动电池技术快速发展",
        "机器人技术在制造业中大量使用",
        "编程教育在中小学逐渐普及",
        "数据科学家是当今最热门的职业之一",
    ]
    train_labels = [0] * 20

    train_texts += [
        "中国男篮在亚洲杯上获得冠军",
        "足球世界杯每四年举办一次",
        "奥运会是全世界最重要的体育盛会",
        "乒乓球是中国的国球",
        "马拉松比赛需要长期耐力训练",
        "游泳是一项很好的全身运动",
        "篮球运动需要团队合作和技巧",
        "网球大满贯赛事吸引全球关注",
        "田径比赛中百米飞人大战最激动人心",
        "冬奥会包括滑雪滑冰等冰雪项目",
        "羽毛球双打需要默契的配合",
        "体育锻炼有助于增强体质和免疫力",
        "足球比赛的战术体系非常复杂",
        "举重运动员需要强大的力量",
        "跳水是中国在奥运会上的优势项目",
        "体操比赛对运动员柔韧性要求很高",
        "排球比赛中拦网是重要的防守技术",
        "拳击运动需要速度和力量的结合",
        "射箭比赛考验运动员的专注力",
        "短跑运动员需要爆发力训练",
    ]
    train_labels += [1] * 20

    # 测试数据
    test_texts = [
        "深度神经网络在语音识别中表现出色",
        "新一代处理器性能大幅提升",
        "冬奥会中国代表团获得多枚金牌",
        "足球比赛中进球是最令人兴奋的时刻",
    ]
    test_labels = [0, 0, 1, 1]

    print(f"训练样本数: {len(train_texts)}, 测试样本数: {len(test_texts)}")
    print(f"类别分布 - 训练集: {dict(zip(*np.unique(train_labels, return_counts=True)))}")

    # ---- 加载tokenizer和模型 ----
    model_name = "bert-base-chinese"
    print(f"\n加载预训练模型: {model_name}")

    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
    )
    model.to(device)

    # ---- 构建数据集和数据加载器 ----
    train_dataset = TextClassificationDataset(train_texts, train_labels, tokenizer, max_length=64)
    test_dataset = TextClassificationDataset(test_texts, test_labels, tokenizer, max_length=64)

    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=4, shuffle=False)

    # ---- 训练配置 ----
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, eps=1e-8)
    num_epochs = 3

    print("\n开始训练...")
    print("-" * 50)

    for epoch in range(num_epochs):
        avg_loss = train_epoch(model, train_loader, optimizer, device)
        metrics, _, _ = evaluate(model, test_loader, device)
        print(
            f"Epoch {epoch + 1}/{num_epochs} | "
            f"损失: {avg_loss:.4f} | "
            f"精度: {metrics['accuracy']:.4f} | "
            f"F1: {metrics['f1']:.4f}"
        )

    # ---- 最终评估 ----
    print("\n" + "=" * 50)
    print("最终评估结果:")
    print("=" * 50)

    final_metrics, preds, labels = evaluate(model, test_loader, device)
    print(f"准确率: {final_metrics['accuracy']:.4f}")
    print(f"精确率: {final_metrics['precision']:.4f}")
    print(f"召回率: {final_metrics['recall']:.4f}")
    print(f"F1值:   {final_metrics['f1']:.4f}")

    print("\n分类报告:")
    print(classification_report(labels, preds, target_names=["科技", "体育"]))

    # ---- 推理演示 ----
    print("=" * 50)
    print("推理演示:")
    print("=" * 50)

    infer_texts = ["智能手机芯片性能不断提升", "游泳健将打破世界纪录"]
    model.eval()
    for text in infer_texts:
        encoding = tokenizer(
            text,
            max_length=64,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        with torch.no_grad():
            outputs = model(
                input_ids=encoding["input_ids"].to(device),
                attention_mask=encoding["attention_mask"].to(device),
            )
        pred = torch.argmax(outputs.logits, dim=-1).item()
        label_name = "科技" if pred == 0 else "体育"
        print(f"文本: '{text}' -> 预测类别: {label_name}")


if __name__ == "__main__":
    solve()

```
