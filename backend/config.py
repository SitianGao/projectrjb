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

# ── LLM 主模型配置 ───────────────────────────────────
LLM_PRIMARY = os.getenv("LLM_PRIMARY", "spark")          # spark / deepseek
SPARK_PROTOCOL = os.getenv("SPARK_PROTOCOL", "http")     # http（X2 OpenAI 兼容）
SPARK_ENABLED = os.getenv("SPARK_ENABLED", "true").lower() in {
    "1", "true", "yes", "on",
}
SPARK_API_PASSWORD = os.getenv("SPARK_API_PASSWORD", "")  # API 密码（Bearer token）
# 兼容旧变量名 SPARK_API_BASE，新变量 SPARK_BASE_URL 优先
# 默认 v1 接口（X2 需要新 APIPassword，配置后切换）
SPARK_BASE_URL = os.getenv(
    "SPARK_BASE_URL",
    os.getenv("SPARK_API_BASE", "https://spark-api-open.xf-yun.com/v1/"),
)
SPARK_API_URL = os.getenv(
    "SPARK_API_URL",
    "https://spark-api-open.xf-yun.com/v1/chat/completions",
)
SPARK_MODEL = os.getenv("SPARK_MODEL", "4.0Ultra")

# ── 备选 LLM ────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 讯飞在线语音合成（与星火大模型密码不是同一组凭证）。
XFYUN_TTS_APP_ID = os.getenv("XFYUN_TTS_APP_ID", "")
XFYUN_TTS_API_KEY = os.getenv("XFYUN_TTS_API_KEY", "")
XFYUN_TTS_API_SECRET = os.getenv("XFYUN_TTS_API_SECRET", "")
XFYUN_TTS_VOICE = os.getenv("XFYUN_TTS_VOICE", "xiaoyan")

# ── 星火 PPT API 配置 ───────────────────────────────────
SPARK_PPT_API_KEY = os.getenv("SPARK_PPT_API_KEY", "")
SPARK_PPT_API_URL = os.getenv(
    "SPARK_PPT_API_URL",
    "https://zwapi.xfyun.cn/api/ppt/v2",
)
SPARK_PPT_DOWNLOAD_DIR = os.getenv(
    "SPARK_PPT_DOWNLOAD_DIR",
    str(Path(__file__).resolve().parent / "storage" / "ppt"),
)
SPARK_PPT_ENABLED = os.getenv("SPARK_PPT_ENABLED", "true").lower() not in {
    "0", "false", "no", "off",
}

# ── LLM 调用配置 ────────────────────────────────────
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# 画像达到该完整度后，才允许进入学习路径生成阶段。
# ProfileService 与 PlannerService 必须共享同一门槛，避免出现画像停止追问、
# 但路径仍无法生成的业务断层。
PROFILE_READY_THRESHOLD = 0.75

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

# ── 严格模式控制 ────────────────────────────────────
LLM_STRICT_MODE = os.getenv("LLM_STRICT_MODE", "true").lower() not in {
    "0", "false", "no", "off",
}
RAG_STRICT_MODE = os.getenv("RAG_STRICT_MODE", "true").lower() not in {
    "0", "false", "no", "off",
}
RESOURCE_STRICT_MODE = os.getenv("RESOURCE_STRICT_MODE", "true").lower() not in {
    "0", "false", "no", "off",
}

# ── RAG 配置 ────────────────────────────────────────
RAG_AUTO_INIT = os.getenv("RAG_AUTO_INIT", "true").lower() not in {
    "0", "false", "no", "off",
}

# ── 认证模式 ────────────────────────────────────────
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() in {
    "1", "true", "yes", "on",
}

# ── 项目路径 ────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
