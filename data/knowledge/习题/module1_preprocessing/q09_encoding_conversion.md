# 常见繁简对照表（简化版）

> 来源模块: module1_preprocessing
> 原始文件: q09_encoding_conversion.py
> 来源: 蓝桥杯人工智能应用赛练习题库

## 题目代码

```python
"""
=============================
【题目】统一编码处理
【模块】数据预处理
【难度】3
【知识点】UTF-8编码校验、大小写转换、繁简映射、Python字符串编码
【描述】
在处理多来源文本数据时，常遇到编码不一致的问题。本题要求：
1. 检测和校验字符串的UTF-8编码
2. 处理不同编码的转换（模拟）
3. 统一英文字母大小写
4. 实现简单的繁体中文到简体中文的映射

【要求】
1. 实现UTF-8编码校验函数，检测字符串是否为有效UTF-8
2. 实现统一大小写转换（英文转小写）
3. 实现简单的繁简映射（使用字典映射常见繁简字对）
4. 对混合文本进行统一的编码规范化处理
5. 处理编码异常情况

【提示】
- Python 3中字符串默认为Unicode，bytes类型需decode
- 繁简映射可使用字典实现，更完善的方案可用opencc库
- chardet库可用于自动检测编码（本题手动实现简化版）
=============================
"""

# ========== 参考答案 ==========

import re


# 常见繁简对照表（简化版）
TRADITIONAL_TO_SIMPLIFIED = {
    '國': '国', '語': '语', '學': '学', '習': '习', '電': '电',
    '腦': '脑', '網': '网', '絡': '络', '資': '资', '訊': '讯',
    '機': '机', '器': '器', '學': '学', '術': '术', '開': '开',
    '發': '发', '數': '数', '據': '据', '處': '处', '理': '理',
    '網': '网', '頁': '页', '軟': '软', '件': '件', '程': '程',
    '序': '序', '設': '设', '計': '计', '測': '测', '試': '试',
    '問': '问', '題': '题', '種': '种', '類': '类', '過': '过',
    '濟': '济', '認': '认', '識': '识', '體': '体', '系': '系',
    '統': '统', '記': '记', '錄': '录', '實': '实', '現': '现',
    '問': '问', '響': '响', '點': '点', '擊': '击', '選': '选',
    '擇': '择', '獲': '获', '取': '取', '運': '运', '營': '营',
    '灣': '湾', '華': '华', '東': '东', '區': '区', '歲': '岁',
    '見': '见', '經': '经', '驗': '验', '車': '车', '書': '书',
    '劃': '划', '產': '产', '業': '业', '結': '结', '構': '构',
    '構': '构', '關': '关', '鍵': '键', '讀': '读', '寫': '写',
    '將': '将', '為': '为', '這': '这', '個': '个', '們': '们',
    '時': '时', '間': '间', '說': '说', '話': '话', '對': '对',
    '進': '进', '行': '行', '長': '长', '與': '与', '從': '从',
    '來': '来', '還': '还', '進': '进', '點': '点', '裡': '里',
    '帶': '带', '動': '动', '標': '标', '準': '准', '確': '确',
    '歷': '历', '史': '史', '條': '条', '件': '件', '沒': '没',
    '複': '复', '雜': '杂', '聯': '联', '網': '网', '轉': '转',
    '換': '换', '總': '总', '結': '结', '報': '报', '告': '告',
    '傳': '传', '統': '统', '資': '资', '料': '料', '庫': '库',
    '機': '机', '學': '学', '圖': '图', '片': '片', '視': '视',
    '頻': '频', '導': '导', '航': '航', '環': '环', '境': '境',
}


def validate_utf8(data):
    """
    校验bytes数据是否为有效UTF-8编码。

    参数:
        data: bytes类型数据

    返回:
        (is_valid, error_msg): 校验结果和错误信息
    """
    if isinstance(data, str):
        return True, "字符串已经是Unicode，无需UTF-8校验"

    if not isinstance(data, bytes):
        return False, f"输入类型应为bytes，实际为{type(data).__name__}"

    try:
        data.decode('utf-8')
        return True, "有效的UTF-8编码"
    except UnicodeDecodeError as e:
        return False, f"无效的UTF-8编码: {e}"


def try_decode(data, encodings=None):
    """
    尝试用多种编码解码bytes数据。

    参数:
        data: bytes类型数据
        encodings: 编码列表

    返回:
        decoded_text: 解码后的字符串
        used_encoding: 使用的编码
    """
    if encodings is None:
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin-1']

    for enc in encodings:
        try:
            decoded = data.decode(enc)
            return decoded, enc
        except (UnicodeDecodeError, LookupError):
            continue

    # latin-1永远不会失败，所以到这里说明输入不是bytes
    return None, None


def normalize_case(text):
    """统一大小写：英文转小写。"""
    if not isinstance(text, str):
        text = str(text)
    return text.lower()


def traditional_to_simplified(text, mapping=None):
    """
    将繁体中文转换为简体中文。

    参数:
        text: 输入文本
        mapping: 繁简映射字典

    返回:
        converted: 转换后的文本
    """
    if mapping is None:
        mapping = TRADITIONAL_TO_SIMPLIFIED

    result = []
    for char in text:
        result.append(mapping.get(char, char))
    return ''.join(result)


def normalize_text(text):
    """
    完整的文本编码规范化流程：
    1. UTF-8校验
    2. 大小写统一
    3. 繁简转换
    4. 去除多余空白
    """
    # 如果是bytes，先解码
    if isinstance(text, bytes):
        is_valid, msg = validate_utf8(text)
        if is_valid:
            text = text.decode('utf-8')
        else:
            text, _ = try_decode(text)

    # 统一大小写
    text = normalize_case(text)

    # 繁简转换（只转中文字符部分）
    text = traditional_to_simplified(text)

    # 去除多余空白
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def solve():
    """主函数：演示统一编码处理。"""
    # ========== 1. UTF-8编码校验 ==========
    print("=" * 60)
    print("1. UTF-8编码校验")
    print("=" * 60)

    test_bytes = [
        ("有效UTF-8", "你好世界".encode('utf-8')),
        ("无效UTF-8", b'\xff\xfe\x00\x00\x48\x00'),
        ("纯ASCII", b"Hello World"),
    ]

    for name, data in test_bytes:
        is_valid, msg = validate_utf8(data)
        print(f"  {name}: {msg}")

    # ========== 2. 多编码解码 ==========
    print("\n" + "=" * 60)
    print("2. 多编码自动解码")
    print("=" * 60)

    original = "蓝桥杯AI竞赛"
    for enc in ['utf-8', 'gbk', 'big5']:
        try:
            encoded = original.encode(enc)
            decoded, used = try_decode(encoded)
            print(f"  编码 {enc}: {encoded[:20]}... -> 解码({used}): {decoded}")
        except UnicodeEncodeError:
            print(f"  编码 {enc}: 无法编码该文本")

    # ========== 3. 大小写统一 ==========
    print("\n" + "=" * 60)
    print("3. 大小写统一")
    print("=" * 60)

    mixed_cases = [
        "Python Machine LEARNING",
        "NLP Natural Language Processing",
        "BlueBridge Cup AI Competition 2024"
    ]

    for text in mixed_cases:
        normalized = normalize_case(text)
        print(f"  原文: {text}")
        print(f"  转换: {normalized}")

    # ========== 4. 繁简转换 ==========
    print("\n" + "=" * 60)
    print("4. 繁体中文 -> 简体中文")
    print("=" * 60)

    traditional_texts = [
        "電腦程式設計",
        "資料庫與網路開發",
        "機器學習與深度學習",
        "這是一個測試",
        "藍橋杯軟體大賽"
    ]

    for text in traditional_texts:
        simplified = traditional_to_simplified(text)
        print(f"  繁體: {text}")
        print(f"  简体: {simplified}")

    # ========== 5. 完整规范化流水线 ==========
    print("\n" + "=" * 60)
    print("5. 完整规范化流水线")
    print("=" * 60)

    test_texts = [
        b"PYTHON Programming   \xe8\x93\x9d\xe6\xa1\xa5\xe6\x9d\xaf",
        "NLP自然語言處理  Machine LEARNING",
        b"Deep Learning  \xe6\xb7\xb1\xe5\xba\xa6\xe5\xad\xb8\xe7\xbf\x92"
    ]

    for text in test_texts:
        if isinstance(text, bytes):
            display = text.decode('utf-8', errors='replace')
        else:
            display = text
        print(f"\n  输入: {display!r}")
        result = normalize_text(text)
        print(f"  输出: {result}")


if __name__ == "__main__":
    solve()

```
