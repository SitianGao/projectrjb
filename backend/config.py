"""
EduAgent 配置文件
"""
import os
from pathlib import Path


def _load_env_files():
    """Load shared project env first, then backend-local overrides."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    load_dotenv(project_root / ".env")
    load_dotenv(backend_dir / ".env", override=True)


_load_env_files()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eduagent.db")

# ── LLM 主模型配置（Spark HTTP API） ──────────────────
LLM_PRIMARY = os.getenv("LLM_PRIMARY", "spark")          # spark / deepseek
SPARK_API_PASSWORD = os.getenv("SPARK_API_PASSWORD", "")  # API 密码（Bearer token）
SPARK_API_URL = os.getenv(
    "SPARK_API_URL",
    "https://spark-api-open.xf-yun.com/v1/chat/completions",
)
SPARK_MODEL = os.getenv("SPARK_MODEL", "4.0Ultra")

# ── 备选 LLM ────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── LLM 调用配置 ────────────────────────────────────
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# 画像达到该完整度后，才允许进入学习路径生成阶段。
# ProfileService 与 PlannerService 必须共享同一门槛，避免出现画像停止追问、
# 但路径仍无法生成的业务断层。
PROFILE_READY_THRESHOLD = 0.85

# 向量库配置
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

# 嵌入模型配置
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2"
)

# 启动时是否给空库导入固定演示数据
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "true").lower() not in {
    "0",
    "false",
    "no",
    "off",
}
