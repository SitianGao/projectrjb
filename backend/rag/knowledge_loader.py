"""
知识库数据导入脚本 —— 扫描 data/knowledge/ 目录，分块入库到 ChromaDB

设计依据：docs/design.md §4.3 + Day 7 任务
"""
import os
import re
import json
import logging
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timezone

from .embedding import default_embedding
from .vector_store import default_store

logger = logging.getLogger(__name__)

# 默认知识库目录
DEFAULT_KNOWLEDGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "knowledge"
)


def chunk_text(text: str, max_chars: int = 800, overlap_chars: int = 100) -> List[str]:
    """将长文本按段落和长度分块

    分块策略：
    1. 优先按 ## 二级标题分割
    2. 若段落仍超过 max_chars，按 ### 三级标题再分割
    3. 若仍超过，按 max_chars 截断，保留 overlap_chars 重叠

    Args:
        text: 原始 Markdown 文本
        max_chars: 每块最大字符数
        overlap_chars: 相邻块重叠字符数

    Returns:
        list of str: 文本块列表
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []

    # 按二级标题分割
    sections = re.split(r'\n(?=## )', text)
    for section in sections:
        if len(section) <= max_chars:
            if section.strip():
                chunks.append(section.strip())
        else:
            # 按三级标题再分
            subsections = re.split(r'\n(?=### )', section)
            for sub in subsections:
                if len(sub) <= max_chars:
                    if sub.strip():
                        chunks.append(sub.strip())
                else:
                    # 按字符数滑动窗口截断
                    start = 0
                    while start < len(sub):
                        end = min(start + max_chars, len(sub))
                        chunk = sub[start:end].strip()
                        if chunk:
                            chunks.append(chunk)
                        start = end - overlap_chars if end < len(sub) else end

    return chunks


def load_knowledge_dir(
    knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR,
    embedding=None,
    vector_store=None,
    clear_existing: bool = True,
) -> Dict:
    """扫描知识库目录，将所有 .md/.json 文件分词入库

    Args:
        knowledge_dir: 知识库目录路径
        embedding: 嵌入模型
        vector_store: 向量存储
        clear_existing: 是否清空已有数据后重新导入

    Returns:
        dict: {"files": int, "chunks": int, "skipped": int, "errors": list}
    """
    embedder = embedding or default_embedding
    store = vector_store or default_store

    if clear_existing and store.count() > 0:
        store.delete_collection()
        logger.info("已清空现有集合")

    stats = {"files": 0, "chunks": 0, "skipped": 0, "errors": []}

    if not os.path.isdir(knowledge_dir):
        stats["errors"].append(f"知识库目录不存在: {knowledge_dir}")
        return stats

    # 收集所有知识文件
    knowledge_files = []
    for root, _dirs, files in os.walk(knowledge_dir):
        for f in files:
            if f.endswith(('.md', '.json')) and f != 'exercises.json':
                knowledge_files.append(os.path.join(root, f))

    logger.info(f"发现 {len(knowledge_files)} 个知识文件")

    for filepath in knowledge_files:
        try:
            relpath = os.path.relpath(filepath, knowledge_dir)
            filename = os.path.basename(filepath)

            # 读取文件内容
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                stats["skipped"] += 1
                continue

            # 提取标题（取第一个 # 标题）
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else filename.replace('.md', '').replace('.json', '')

            # 如果是 .json，特殊处理
            if filepath.endswith('.json'):
                chunks = _load_json_as_chunks(content, title, max_chars=800)
            else:
                chunks = chunk_text(content, max_chars=800, overlap_chars=100)

            if not chunks:
                stats["skipped"] += 1
                continue

            # 批量生成 ID、嵌入向量、元数据
            ids = []
            documents = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(f"{relpath}:{i}".encode()).hexdigest()[:12]
                ids.append(f"kb_{chunk_id}")
                documents.append(chunk)
                metadatas.append({
                    "source": relpath,
                    "title": title,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "char_count": len(chunk),
                    "file_type": os.path.splitext(filename)[1],
                    "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                })

            # 批量转向量（比逐条快）
            embeddings = embedder.embed_batch(documents)

            # 入库
            store.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

            stats["files"] += 1
            stats["chunks"] += len(chunks)
            logger.info(f"  [{stats['files']}] {relpath}: {len(chunks)} chunks")

        except Exception as e:
            err_msg = f"{os.path.basename(filepath)}: {str(e)}"
            stats["errors"].append(err_msg)
            logger.error(f"  导入失败: {err_msg}")

    logger.info(
        f"知识库导入完成: {stats['files']} 个文件 -> {stats['chunks']} 个文本块, "
        f"跳过 {stats['skipped']}, 错误 {len(stats['errors'])}"
    )
    return stats


def _load_json_as_chunks(content: str, title: str, max_chars: int = 800) -> List[str]:
    """将 JSON 格式知识转为文本块（exercises.json 等）"""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    chunks = []
    if isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                text_parts = [f"# {title} (第{i+1}题)"]
                for key, val in item.items():
                    text_parts.append(f"**{key}**: {val}")
                chunks.append("\n".join(text_parts))
    elif isinstance(data, dict):
        text = json.dumps(data, ensure_ascii=False, indent=2)
        chunks = chunk_text(text, max_chars=max_chars)
    return chunks


# ---- 便捷函数 ----

def quick_load(clear: bool = True) -> Dict:
    """一键导入默认知识库目录的所有文件"""
    return load_knowledge_dir(clear_existing=clear)


if __name__ == "__main__":
    # 直接运行此脚本：导入知识库
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
    stats = quick_load()
    print(f"\n导入完成: {stats}")
