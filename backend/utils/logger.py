"""
统一日志配置 —— 控制台 + 文件双输出，兼容 logging.getLogger(__name__)

用法:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("something happened")
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "eduagent.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 单文件最大 10MB
LOG_BACKUP_COUNT = 5               # 保留最近 5 个历史文件

_initialized = False


def setup_logging(level: int = logging.DEBUG) -> None:
    """
    初始化日志系统 —— 在 app.py 启动时调用一次。
    控制台输出 INFO 及以上，文件记录 DEBUG 及以上。
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    # --- 控制台 handler：只显示 INFO 及以上 ---
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root.addHandler(console)

    # --- 文件 handler：记录 DEBUG 及以上，自动轮转 ---
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # 降低第三方库的日志噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    root.info("EduAgent 日志系统初始化完成")


def get_logger(name: str) -> logging.Logger:
    """获取模块级 logger，兼容 logging.getLogger(__name__) 用法"""
    return logging.getLogger(name)
