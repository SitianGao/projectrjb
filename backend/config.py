"""
EduAgent 配置文件
"""
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eduagent.db")

# LLM API 配置
SPARK_API_KEY = os.getenv("SPARK_API_KEY", "")
SPARK_API_SECRET = os.getenv("SPARK_API_SECRET", "")
SPARK_APP_ID = os.getenv("SPARK_APP_ID", "")

# 备选 LLM
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# LLM 调用配置
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# 向量库配置
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

# 嵌入模型配置
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2"
)
