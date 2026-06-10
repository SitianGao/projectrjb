"""
EduAgent 配置文件
"""
import os
from pathlib import Path

# 自动加载项目根目录的 .env 文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eduagent.db")

# ── LLM 主模型配置（Spark HTTP API） ──────────────────
LLM_PRIMARY = os.getenv("LLM_PRIMARY", "spark")          # spark / deepseek
SPARK_API_PASSWORD = os.getenv("SPARK_API_PASSWORD", "")  # API 密码（Bearer token）
SPARK_API_URL = os.getenv(
    "SPARK_API_URL",
    "https://spark-api-open.xf-yun.com/agent/v1/chat/completions",
)
SPARK_MODEL = os.getenv("SPARK_MODEL", "spark-2.0-flash")  # spark-2.0-flash / spark-2.0 / ...

# ── 备选 LLM ────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── LLM 调用配置 ────────────────────────────────────
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# 向量库配置
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

# 嵌入模型配置
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2"
)
