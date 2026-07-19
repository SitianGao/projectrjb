"""
SparkPptClient —— 星火智能 PPT API 客户端

调用讯飞星火 PPT API 生成专业课件。

API 文档: https://www.xfyun.cn/doc/spark/PPT-API.html

核心流程:
1. 调用 createPptByOutline 传入大纲 → 获得 sid
2. 轮询 queryPptStatus 查询生成进度
3. 下载 pptx 到本地存储
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

try:
    from config import SPARK_PPT_API_KEY, SPARK_PPT_API_URL, SPARK_PPT_DOWNLOAD_DIR
except ModuleNotFoundError:
    from backend.config import SPARK_PPT_API_KEY, SPARK_PPT_API_URL, SPARK_PPT_DOWNLOAD_DIR

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_TIMEOUT = 30  # 请求超时（秒）
MAX_POLL_ATTEMPTS = 120  # 最大轮询次数
POLL_INTERVAL = 5  # 轮询间隔（秒）
MAX_OUTLINE_CHAPTERS = 20  # 大纲最大章节数


class SparkPptError(Exception):
    """星火 PPT API 错误"""
    pass


class SparkPptClient:
    """星火智能 PPT API 客户端"""

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key or SPARK_PPT_API_KEY
        self.api_url = api_url or SPARK_PPT_API_URL
        self.download_dir = Path(SPARK_PPT_DOWNLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            logger.warning("SparkPptClient: SPARK_PPT_API_KEY 未配置，PPT 生成功能不可用")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def create_ppt_by_outline(
        self,
        outline: List[Dict[str, Any]],
        *,
        title: str = "",
        template_id: Optional[str] = None,
        language: str = "zh",
        search: bool = False,
        ai_image: bool = False,
        speaker_notes: bool = True,
    ) -> str:
        """
        通过大纲创建 PPT

        Args:
            outline: PPT 大纲，最多 20 个一级章节
                每个章节格式: {
                    "title": "章节标题",
                    "subtitles": [
                        {"title": "子标题", "content": "内容要点"}
                    ]
                }
            title: PPT 标题（可选）
            template_id: 模板 ID（可选）
            language: 语言（zh/en）
            search: 是否联网搜索
            ai_image: 是否 AI 配图
            speaker_notes: 是否生成演讲备注

        Returns:
            sid: PPT 任务 ID，用于查询进度和下载
        """
        if not self.api_key:
            raise SparkPptError("SPARK_PPT_API_KEY 未配置")

        # 限制章节数量
        if len(outline) > MAX_OUTLINE_CHAPTERS:
            logger.warning("大纲章节超过 %d 个，已截断", MAX_OUTLINE_CHAPTERS)
            outline = outline[:MAX_OUTLINE_CHAPTERS]

        # 构建请求体
        payload = {
            "outline": outline,
            "language": language,
            "search": search,
            "aiImage": ai_image,
            "speakerNotes": speaker_notes,
        }

        if title:
            payload["title"] = title

        if template_id:
            payload["templateId"] = template_id

        logger.info("调用星火 PPT API: title=%s, chapters=%d", title, len(outline))

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/createPptByOutline",
                    json=payload,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                # 检查响应
                if data.get("code") != 0:
                    error_msg = data.get("message", "未知错误")
                    raise SparkPptError(f"创建 PPT 失败: {error_msg}")

                sid = data.get("data", {}).get("sid")
                if not sid:
                    raise SparkPptError("创建 PPT 成功但未返回 sid")

                logger.info("PPT 创建成功: sid=%s", sid)
                return sid

            except httpx.HTTPStatusError as e:
                raise SparkPptError(f"HTTP 错误: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                raise SparkPptError(f"请求错误: {str(e)}")

    async def query_ppt_status(self, sid: str) -> Dict[str, Any]:
        """
        查询 PPT 生成状态

        Args:
            sid: PPT 任务 ID

        Returns:
            {
                "sid": "任务ID",
                "status": "processing|completed|failed",
                "progress": 0-100,
                "download_url": "下载链接（完成时）",
                "error": "错误信息（失败时）"
            }
        """
        if not self.api_key:
            raise SparkPptError("SPARK_PPT_API_KEY 未配置")

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                response = await client.get(
                    f"{self.api_url}/queryPptStatus",
                    params={"sid": sid},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") != 0:
                    error_msg = data.get("message", "未知错误")
                    raise SparkPptError(f"查询状态失败: {error_msg}")

                result = data.get("data", {})
                return {
                    "sid": sid,
                    "status": result.get("status", "unknown"),
                    "progress": result.get("progress", 0),
                    "download_url": result.get("downloadUrl"),
                    "error": result.get("error"),
                }

            except httpx.HTTPStatusError as e:
                raise SparkPptError(f"HTTP 错误: {e.response.status_code}")
            except httpx.RequestError as e:
                raise SparkPptError(f"请求错误: {str(e)}")

    async def download_ppt(self, download_url: str, filename: str) -> Path:
        """
        下载 PPT 文件

        Args:
            download_url: 下载链接
            filename: 文件名

        Returns:
            下载后的本地文件路径
        """
        if not download_url:
            raise SparkPptError("下载链接为空")

        # 确保文件名以 .pptx 结尾
        if not filename.endswith(".pptx"):
            filename = f"{filename}.pptx"

        # 清理文件名
        filename = self._sanitize_filename(filename)
        file_path = self.download_dir / filename

        logger.info("下载 PPT: %s -> %s", download_url[:50], file_path)

        async with httpx.AsyncClient(timeout=120) as client:
            try:
                response = await client.get(download_url)
                response.raise_for_status()

                # 写入文件
                file_path.write_bytes(response.content)
                logger.info("PPT 下载完成: %s (%.2f KB)", file_path, len(response.content) / 1024)

                return file_path

            except httpx.HTTPStatusError as e:
                raise SparkPptError(f"下载失败: HTTP {e.response.status_code}")
            except httpx.RequestError as e:
                raise SparkPptError(f"下载错误: {str(e)}")

    async def wait_for_completion(
        self,
        sid: str,
        max_attempts: int = MAX_POLL_ATTEMPTS,
        poll_interval: float = POLL_INTERVAL,
    ) -> Dict[str, Any]:
        """
        等待 PPT 生成完成

        Args:
            sid: PPT 任务 ID
            max_attempts: 最大轮询次数
            poll_interval: 轮询间隔（秒）

        Returns:
            完成后的状态信息
        """
        logger.info("等待 PPT 生成完成: sid=%s, max_attempts=%d", sid, max_attempts)

        for attempt in range(1, max_attempts + 1):
            status = await self.query_ppt_status(sid)

            if status["status"] == "completed":
                logger.info("PPT 生成完成: sid=%s, attempt=%d", sid, attempt)
                return status

            if status["status"] == "failed":
                error_msg = status.get("error", "未知错误")
                raise SparkPptError(f"PPT 生成失败: {error_msg}")

            # 记录进度
            if attempt % 6 == 0:  # 每 30 秒记录一次
                logger.info("PPT 生成中: sid=%s, progress=%d%%", sid, status.get("progress", 0))

            await asyncio.sleep(poll_interval)

        raise SparkPptError(f"PPT 生成超时: 已等待 {max_attempts * poll_interval} 秒")

    async def create_and_download(
        self,
        outline: List[Dict[str, Any]],
        *,
        title: str = "",
        filename: Optional[str] = None,
        template_id: Optional[str] = None,
        language: str = "zh",
        search: bool = False,
        ai_image: bool = False,
        speaker_notes: bool = True,
    ) -> Path:
        """
        一站式创建并下载 PPT

        Args:
            outline: PPT 大纲
            title: PPT 标题
            filename: 下载文件名（可选，默认使用标题）
            template_id: 模板 ID
            language: 语言
            search: 是否联网搜索
            ai_image: 是否 AI 配图
            speaker_notes: 是否生成演讲备注

        Returns:
            下载后的本地文件路径
        """
        # 1. 创建 PPT
        sid = await self.create_ppt_by_outline(
            outline,
            title=title,
            template_id=template_id,
            language=language,
            search=search,
            ai_image=ai_image,
            speaker_notes=speaker_notes,
        )

        # 2. 等待完成
        status = await self.wait_for_completion(sid)

        # 3. 下载文件
        download_url = status.get("download_url")
        if not download_url:
            raise SparkPptError("PPT 生成完成但未提供下载链接")

        if not filename:
            filename = title or f"ppt_{sid[:8]}"

        return await self.download_ppt(download_url, filename)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名，移除非法字符"""
        import re
        # 替换非法字符为下划线
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1)
            filename = name[:195] + '.' + ext
        return filename


# 全局客户端实例
spark_ppt_client = SparkPptClient()
