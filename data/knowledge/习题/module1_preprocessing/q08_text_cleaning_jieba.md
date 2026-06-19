# 自定义停用词表

> 来源模块: module1_preprocessing
> 原始文件: q08_text_cleaning_jieba.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】中文文本清洗与jieba分词
【模块】数据预处理
【难度】3
【知识点】正则表达式、HTML标签去除、URL去除、jieba分词、停用词过滤
【描述】
自然语言处理的第一步是文本清洗和分词。本题要求对原始中文文本进行：
1. 去除HTML标签
2. 去除URL链接
3. 去除特殊字符（保留中文、英文、数字）
4. 使用jieba进行中文分词
5. 去除停用词

【要求】
1. 给定包含HTML标签、URL、特殊字符的中文文本列表
2. 实现完整的文本清洗流程（去HTML、去URL、去特殊字符）
3. 使用jieba进行中文分词（支持精确模式、全模式、搜索引擎模式）
4. 实现停用词过滤（使用自定义停用词表）
5. 输出清洗和分词的中间结果，展示各步骤效果

【提示】
- 使用re模块处理HTML标签和URL
- jieba.cut()返回生成器，可用'/'.join()查看分词结果
- 停用词表通常包含"的"、"了"、"是"、"在"等高频虚词
=============================
"""

# ========== 参考答案 ==========

import re
import pandas as pd
import jieba
import jieba.posseg as pseg


# 自定义停用词表
STOP_WORDS = set([
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
    '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会',
    '着', '没有', '看', '好', '自己', '这', '他', '她', '它', '们',
    '那', '些', '为', '与', '等', '被', '从', '对', '把', '能',
    '但', '又', '而', '或', '之', '以', '其', '及', '中', '于',
    '还', '将', '此', '可', '让', '吗', '吧', '呢', '啊', '呀',
    '嗯', '哦', '哈', '么', '什么', '怎么', '哪', '哪里', '为什么',
    '这个', '那个', '这些', '那些', '这样', '那样', '如何', '已经',
    '可以', '因为', '所以', '如果', '虽然', '但是', '不过', '然后',
    '就是', '只是', '不是', '没有', '比较', '非常', '一些', '一种',
    '进行', '通过', '使用', '关于', '对于', '根据', '目前', '我们',
    '他们', '你们', '该', '已', '更', '最', '当', '地', '得'
])


def remove_html_tags(text):
    """去除HTML标签。"""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean


def remove_urls(text):
    """去除URL链接。"""
    clean = re.sub(r'https?://\S+|www\.\S+', '', text)
    return clean


def remove_special_chars(text):
    """去除特殊字符，保留中文、英文、数字和空格。"""
    clean = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
    # 合并多余空格
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def clean_text(text):
    """完整的文本清洗流程。"""
    text = remove_html_tags(text)
    text = remove_urls(text)
    text = remove_special_chars(text)
    return text


def segment_jieba(text, mode='exact'):
    """
    使用jieba分词。

    参数:
        text: 清洗后的文本
        mode: 分词模式 ('exact', 'full', 'search')

    返回:
        words: 分词列表
    """
    if mode == 'exact':
        words = list(jieba.cut(text, cut_all=False))
    elif mode == 'full':
        words = list(jieba.cut(text, cut_all=True))
    elif mode == 'search':
        words = list(jieba.cut_for_search(text))
    else:
        words = list(jieba.cut(text, cut_all=False))

    # 过滤空字符串和纯空格
    words = [w.strip() for w in words if w.strip()]
    return words


def remove_stopwords(words, stop_words=None):
    """
    去除停用词。

    参数:
        words: 分词列表
        stop_words: 停用词集合

    返回:
        filtered: 过滤后的词列表
    """
    if stop_words is None:
        stop_words = STOP_WORDS
    return [w for w in words if w not in stop_words]


def solve():
    """主函数：演示中文文本清洗与jieba分词。"""
    # ========== 1. 准备原始文本 ==========
    raw_texts = [
        '<p>蓝桥杯是<span>全国性</span>的IT类学科竞赛，<a href="https://example.com">点击查看</a>。</p>',
        '请访问 https://www.lanqiao.cn 了解更多关于人工智能&&深度学习的内容！！！',
        'Python是一门##强大的##编程语言~~~特别适合@数据科学@和%%机器学习%%领域的应用。',
        '<div>NLP自然语言处理是AI的核心技术之一，<br/>包括文本分类、情感分析等任务。</div>',
        '2024年的蓝桥杯AI赛道将考察参赛者的机器学习&&深度学习&&NLP能力，详情见www.example.com/aib'
    ]

    print("=" * 70)
    print("中文文本清洗与jieba分词演示")
    print("=" * 70)

    for i, raw in enumerate(raw_texts):
        print(f"\n{'─' * 50}")
        print(f"原始文本 {i + 1}: {raw}")

        # 清洗
        cleaned = clean_text(raw)
        print(f"清洗后: {cleaned}")

        # 分词（精确模式）
        words_exact = segment_jieba(cleaned, mode='exact')
        print(f"精确分词: {' / '.join(words_exact)}")

        # 分词（搜索引擎模式）
        words_search = segment_jieba(cleaned, mode='search')
        print(f"搜索分词: {' / '.join(words_search)}")

        # 去停用词
        words_filtered = remove_stopwords(words_exact)
        print(f"去停用词: {' / '.join(words_filtered)}")
        print(f"词数变化: {len(words_exact)} -> {len(words_filtered)}")

    # ========== 2. 批量处理演示 ==========
    print("\n" + "=" * 70)
    print("批量文本处理流水线")
    print("=" * 70)

    results = []
    for raw in raw_texts:
        cleaned = clean_text(raw)
        words = segment_jieba(cleaned, mode='exact')
        filtered = remove_stopwords(words)
        results.append({
            'raw': raw,
            'cleaned': cleaned,
            'words': words,
            'filtered': filtered,
            'word_count': len(filtered)
        })

    summary = pd.DataFrame([{
        '原始长度': len(r['raw']),
        '清洗后长度': len(r['cleaned']),
        '分词数': len(r['words']),
        '去停用词后词数': r['word_count']
    } for r in results])

    print("\n" + summary.to_string())

    # ========== 3. 词性标注演示 ==========
    print("\n" + "=" * 70)
    print("词性标注演示（jieba.posseg）")
    print("=" * 70)

    sample = clean_text(raw_texts[0])
    print(f"\n文本: {sample}")
    words_with_pos = pseg.cut(sample)
    for word, flag in words_with_pos:
        if word.strip() and word not in STOP_WORDS:
            print(f"  {word} ({flag})")


if __name__ == "__main__":
    solve()

```
