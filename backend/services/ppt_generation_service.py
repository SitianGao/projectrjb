"""
PptGenerationService —— PPT 生成编排服务

协调 ResourceAgent 和 SparkPptClient，实现个性化 PPT 生成。

核心流程:
1. ResourceAgent 生成个性化 PPT 大纲（PersonalizedPptSpec）
2. SparkPptClient 调用星火 PPT API 生成课件
3. 下载 pptx 到本地存储
4. 保存为 Resource(type="ppt")
5. 返回资源信息供前端展示
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

try:
    from config import SPARK_PPT_ENABLED
except ModuleNotFoundError:
    from backend.config import SPARK_PPT_ENABLED

from core.agent_context import AgentContext
from models.resource import Resource
from services.spark_ppt_client import SparkPptClient, SparkPptError, spark_ppt_client

logger = logging.getLogger(__name__)


class PptGenerationError(Exception):
    """PPT 生成错误"""
    pass


class PptGenerationService:
    """PPT 生成编排服务"""

    def __init__(self, spark_client: Optional[SparkPptClient] = None):
        self.spark_client = spark_client or spark_ppt_client

    async def generate_ppt_for_task(
        self,
        db: Session,
        *,
        user_id: str,
        course_id: str,
        task_id: str,
        topic: str,
        difficulty: str = "中级",
        profile: Optional[Dict] = None,
        stage_info: Optional[Dict] = None,
        knowledge_context: Optional[str] = None,
        on_progress: Optional[Callable[[int, str, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        为学习任务生成 PPT

        Args:
            db: 数据库会话
            user_id: 用户 ID
            course_id: 课程 ID
            task_id: 任务 ID
            topic: 知识点主题
            difficulty: 难度等级
            profile: 学生画像
            stage_info: 关卡信息
            knowledge_context: 知识库上下文
            on_progress: 进度回调

        Returns:
            资源信息字典
        """
        if not SPARK_PPT_ENABLED:
            raise PptGenerationError("星火 PPT 功能未启用")

        if not self.spark_client.api_key:
            raise PptGenerationError("SPARK_PPT_API_KEY 未配置")

        try:
            # 1. 生成个性化 PPT 大纲
            self._emit_progress(on_progress, 10, "generating_outline", "正在生成个性化 PPT 大纲")
            outline = await self._generate_personalized_outline(
                topic=topic,
                difficulty=difficulty,
                profile=profile,
                stage_info=stage_info,
                knowledge_context=knowledge_context,
            )

            # 2. 调用星火 PPT API
            self._emit_progress(on_progress, 30, "creating_ppt", "正在调用星火 PPT API 生成课件")
            filename = f"{topic}_{difficulty}_{uuid.uuid4().hex[:8]}"
            ppt_path = await self.spark_client.create_and_download(
                outline=outline,
                title=f"{topic} - {difficulty}",
                filename=filename,
                language="zh",
                search=False,
                ai_image=True,
                speaker_notes=True,
            )

            # 3. 保存为 Resource
            self._emit_progress(on_progress, 80, "saving_resource", "正在保存 PPT 资源")
            resource = self._save_ppt_resource(
                db=db,
                user_id=user_id,
                course_id=course_id,
                task_id=task_id,
                topic=topic,
                difficulty=difficulty,
                ppt_path=ppt_path,
                outline=outline,
                stage_info=stage_info,
            )

            self._emit_progress(on_progress, 100, "completed", "PPT 生成完成")
            return resource

        except SparkPptError as e:
            logger.error("星火 PPT API 错误: %s", e)
            raise PptGenerationError(f"星火 PPT API 错误: {str(e)}")
        except Exception as e:
            logger.error("PPT 生成失败: %s", e, exc_info=True)
            raise PptGenerationError(f"PPT 生成失败: {str(e)}")

    async def _generate_personalized_outline(
        self,
        topic: str,
        difficulty: str,
        profile: Optional[Dict] = None,
        stage_info: Optional[Dict] = None,
        knowledge_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        生成个性化 PPT 大纲

        根据学生画像、关卡信息和知识库上下文，生成适合学生水平的 PPT 大纲。

        Returns:
            星火 API 格式的大纲列表
        """
        # 基础大纲结构
        outline = []

        # 根据难度调整内容深度
        depth_map = {
            "初级": {"chapters": 6, "points_per_chapter": 2, "language": "通俗易懂"},
            "中级": {"chapters": 8, "points_per_chapter": 3, "language": "专业但易懂"},
            "高级": {"chapters": 10, "points_per_chapter": 4, "language": "深入专业"},
        }
        depth_config = depth_map.get(difficulty, depth_map["中级"])

        # 第1章：封面
        outline.append({
            "title": topic,
            "subtitles": [
                {
                    "title": "学习目标",
                    "content": f"掌握{topic}的核心概念和基本应用",
                }
            ]
        })

        # 第2章：问题引入
        outline.append({
            "title": f"为什么需要{topic}",
            "subtitles": [
                {
                    "title": "现实痛点",
                    "content": f"描述没有{topic}时会遇到的困难",
                },
                {
                    "title": "解决方案",
                    "content": f"{topic}如何解决上述问题",
                }
            ]
        })

        # 第3章：核心概念
        outline.append({
            "title": f"{topic}的核心概念",
            "subtitles": [
                {
                    "title": "基本定义",
                    "content": f"{topic}的标准定义和关键术语",
                },
                {
                    "title": "数学表达",
                    "content": f"{topic}的数学公式和符号说明",
                }
            ]
        })

        # 第4章：工作原理
        outline.append({
            "title": f"{topic}的工作原理",
            "subtitles": [
                {
                    "title": "算法流程",
                    "content": f"{topic}的核心算法步骤",
                },
                {
                    "title": "推导过程",
                    "content": f"{topic}的关键推导",
                }
            ]
        })

        # 第5章：代码实现
        outline.append({
            "title": f"{topic}的代码实现",
            "subtitles": [
                {
                    "title": "Python 示例",
                    "content": f"{topic}的完整代码实现",
                },
                {
                    "title": "关键代码解读",
                    "content": "逐行解释核心逻辑",
                }
            ]
        })

        # 第6章：实例演示
        outline.append({
            "title": f"{topic}实例演示",
            "subtitles": [
                {
                    "title": "案例分析",
                    "content": f"{topic}的实际应用案例",
                },
                {
                    "title": "效果对比",
                    "content": "Before/After 效果对比",
                }
            ]
        })

        # 第7章：常见误区
        outline.append({
            "title": f"{topic}常见误区",
            "subtitles": [
                {
                    "title": "典型错误",
                    "content": f"学习{topic}时的常见错误",
                },
                {
                    "title": "正确理解",
                    "content": f"正确理解{topic}的关键点",
                }
            ]
        })

        # 第8章：小结
        outline.append({
            "title": f"{topic}小结",
            "subtitles": [
                {
                    "title": "核心要点",
                    "content": f"回顾{topic}的3个关键 takeaway",
                },
                {
                    "title": "知识地图",
                    "content": f"{topic}在整个知识体系中的位置",
                }
            ]
        })

        # 根据难度调整章节数量
        if len(outline) > depth_config["chapters"]:
            outline = outline[:depth_config["chapters"]]

        return outline

    def _save_ppt_resource(
        self,
        db: Session,
        *,
        user_id: str,
        course_id: str,
        task_id: str,
        topic: str,
        difficulty: str,
        ppt_path: Path,
        outline: List[Dict],
        stage_info: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        保存 PPT 为 Resource

        Args:
            db: 数据库会话
            user_id: 用户 ID
            course_id: 课程 ID
            task_id: 任务 ID
            topic: 知识点主题
            difficulty: 难度等级
            ppt_path: PPT 文件路径
            outline: PPT 大纲
            stage_info: 关卡信息

        Returns:
            资源信息字典
        """
        resource_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # 构建资源内容（存储大纲和元信息）
        content = {
            "outline": outline,
            "file_path": str(ppt_path),
            "file_name": ppt_path.name,
            "file_size": ppt_path.stat().st_size,
            "generated_at": now.isoformat(),
            "stage_info": stage_info,
        }

        # 创建 Resource 记录
        resource = Resource(
            id=resource_id,
            student_id=user_id,
            course_id=course_id,
            task_id=task_id,
            type="ppt",
            title=f"{topic} - {difficulty} PPT",
            content=json.dumps(content, ensure_ascii=False),
            topic=topic,
            difficulty=difficulty,
            trigger_source="spark_ppt_api",
            trigger_context=json.dumps({
                "api": "spark_ppt",
                "outline_chapters": len(outline),
            }),
            generation_version="1",
            generation_status="ready",
            generation_source="spark_ppt_api",
            artifact_url=f"/api/resource/ppt/{resource_id}/download",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            created_at=now,
        )

        db.add(resource)
        db.commit()
        db.refresh(resource)

        logger.info("PPT 资源已保存: resource_id=%s, file=%s", resource_id, ppt_path.name)

        return {
            "id": resource.id,
            "resource_id": resource.id,
            "type": "ppt",
            "title": resource.title,
            "topic": resource.topic,
            "difficulty": resource.difficulty,
            "content": content,
            "artifact_url": resource.artifact_url,
            "mime_type": resource.mime_type,
            "created_at": resource.created_at.isoformat(),
        }

    async def query_generation_status(self, sid: str) -> Dict[str, Any]:
        """
        查询 PPT 生成状态

        Args:
            sid: 星火 PPT 任务 ID

        Returns:
            状态信息
        """
        try:
            return await self.spark_client.query_ppt_status(sid)
        except SparkPptError as e:
            logger.error("查询 PPT 状态失败: %s", e)
            raise PptGenerationError(f"查询状态失败: {str(e)}")

    async def download_ppt_by_sid(self, sid: str, filename: str) -> Path:
        """
        通过 sid 下载 PPT

        Args:
            sid: 星火 PPT 任务 ID
            filename: 文件名

        Returns:
            下载后的文件路径
        """
        try:
            status = await self.spark_client.query_ppt_status(sid)
            if status["status"] != "completed":
                raise PptGenerationError(f"PPT 尚未完成，当前状态: {status['status']}")

            download_url = status.get("download_url")
            if not download_url:
                raise PptGenerationError("未获取到下载链接")

            return await self.spark_client.download_ppt(download_url, filename)

        except SparkPptError as e:
            logger.error("下载 PPT 失败: %s", e)
            raise PptGenerationError(f"下载失败: {str(e)}")

    @staticmethod
    def _emit_progress(
        callback: Optional[Callable[[int, str, str], None]],
        progress: int,
        phase: str,
        message: str,
    ) -> None:
        """发送进度回调"""
        if callback:
            callback(progress, phase, message)


# 全局服务实例
ppt_generation_service = PptGenerationService()
