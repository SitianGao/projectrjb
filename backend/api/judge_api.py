"""
在线代码判题 API
- POST /api/judge/submit       提交代码判题
- GET  /api/judge/problems      获取编程题库列表
- GET  /api/judge/problems/{id} 获取题目详情（不含隐藏测试用例答案）
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.openapi_examples import json_responses
from api.response import ApiError, ok
from database import SessionLocal, get_db
from services.judge_service import (
    JudgeConfig,
    LANG_CONFIG,
    default_sandbox,
    default_experiment_runner,
)
from services.evaluate_service import EvaluateService
from models.evaluation import LearningRecord

logger = logging.getLogger(__name__)
router = APIRouter()

# ── 知识库编程题路径 ──
PROBLEMS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge" / "11-编程题库"


# ══════════════════════════════════════════════════════════
# Pydantic Models
# ══════════════════════════════════════════════════════════

class JudgeSubmitRequest(BaseModel):
    student_id: str = Field(..., examples=["demo-student-01"])
    problem_id: str = Field(..., examples=["prog-01"])
    language: str = Field(..., examples=["python"])
    code: str = Field(..., examples=["print('hello world')"])
    resource_id: Optional[str] = None


class JudgeSubmitResponse(BaseModel):
    submission_id: str
    status: str
    passed: int
    total: int
    score: int
    results: list = []
    compile_error: Optional[str] = None
    total_time_ms: float = 0


class ProblemSummary(BaseModel):
    id: str
    title: str
    difficulty: str
    tags: list = []
    solved_count: int = 0
    total_submissions: int = 0


# ══════════════════════════════════════════════════════════
# Helper: 从知识库加载题目
# ══════════════════════════════════════════════════════════

def _load_problem(problem_id: str) -> Optional[dict]:
    """从 11-编程题库/ 加载编程题"""
    if not PROBLEMS_DIR.is_dir():
        return None
    problem_file = PROBLEMS_DIR / f"{problem_id}.md"
    if not problem_file.exists():
        return None

    content = problem_file.read_text(encoding="utf-8")

    # 解析 Markdown 格式的编程题
    result = {"id": problem_id, "test_cases": []}

    # 提取标题
    title_match = content.split("\n")[0].strip()
    if title_match.startswith("# "):
        result["title"] = title_match[2:]
    else:
        result["title"] = problem_id

    # 提取各字段
    sections = _parse_markdown_sections(content)

    result["description"] = sections.get("## 题目描述", "")
    result["input_format"] = sections.get("## 输入格式", "")
    result["output_format"] = sections.get("## 输出格式", "")
    result["difficulty"] = sections.get("## 难度", "中等").strip()

    tags_raw = sections.get("## 标签", "")
    result["tags"] = [t.strip() for t in tags_raw.replace("，", ",").split(",") if t.strip()]

    suggestions = sections.get("## 建议时间", "20 分钟").strip()
    result["suggested_minutes"] = suggestions

    # 提取样例
    result["sample_input"] = _extract_code_block(sections.get("## 输入样例", ""))
    result["sample_output"] = _extract_code_block(sections.get("## 输出样例", ""))

    # 提取测试用例（隐藏，不返回给前端）
    tc_json = sections.get("## 测试用例", "")
    if tc_json:
        try:
            # 从 ```json ... ``` 或纯 JSON 中提取
            json_match = _extract_code_block(tc_json)
            if json_match:
                result["test_cases"] = json.loads(json_match)
            else:
                result["test_cases"] = json.loads(tc_json)
        except json.JSONDecodeError:
            result["test_cases"] = []

    return result


def _load_all_problems() -> list:
    """加载所有编程题"""
    if not PROBLEMS_DIR.is_dir():
        return []
    problems = []
    for f in sorted(PROBLEMS_DIR.glob("prog-*.md")):
        pid = f.stem
        problem = _load_problem(pid)
        if problem:
            problems.append({
                "id": pid,
                "title": problem.get("title", pid),
                "difficulty": problem.get("difficulty", "中等"),
                "tags": problem.get("tags", []),
            })
    return problems


def _parse_markdown_sections(content: str) -> dict:
    """将 Markdown 内容按 ## 标题分段"""
    import re
    sections = {}
    current_section = ""
    current_content: list[str] = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line.strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def _extract_code_block(text: str) -> str:
    """从 Markdown 代码块中提取内容"""
    import re
    m = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


# ══════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════

@router.post("/submit", responses=json_responses("JUDGE_FAILED"))
async def submit_code(request: JudgeSubmitRequest):
    """提交代码进行判题"""
    if request.language not in LANG_CONFIG:
        raise ApiError("BAD_REQUEST", f"不支持的语言: {request.language}。支持: {', '.join(LANG_CONFIG.keys())}")

    if not request.code.strip():
        raise ApiError("BAD_REQUEST", "代码不能为空")

    # 加载题目和测试用例
    problem = _load_problem(request.problem_id)
    if not problem:
        raise ApiError("NOT_FOUND", f"编程题不存在: {request.problem_id}")

    test_cases = problem.get("test_cases", [])
    if not test_cases:
        raise ApiError("BAD_REQUEST", "该题目没有配置测试用例")

    # 执行判题
    judge_result = await default_sandbox.run(
        code=request.code,
        language=request.language,
        test_cases=test_cases,
        config=JudgeConfig(),
    )

    submission_id = f"sub_{uuid.uuid4().hex[:8]}"
    score = round(judge_result.passed / max(judge_result.total, 1) * 100)

    # 保存学习记录
    db = SessionLocal()
    try:
        record_id = str(uuid.uuid4())
        db.add(LearningRecord(
            id=record_id,
            student_id=request.student_id,
            resource_id=request.resource_id,
            action="code_submit",
            topic=problem.get("title", request.problem_id),
            score=score / 100.0,
        ))
        db.commit()
    except Exception as exc:
        logger.warning(f"保存学习记录失败: {exc}")
    finally:
        db.close()

    return ok({
        "submission_id": submission_id,
        "status": judge_result.status,
        "passed": judge_result.passed,
        "total": judge_result.total,
        "score": score,
        "results": judge_result.results,
        "compile_error": judge_result.compile_error,
        "total_time_ms": judge_result.total_time_ms,
    })


@router.get("/problems", responses=json_responses())
async def list_problems(
    difficulty: Optional[str] = Query(None, description="按难度筛选: 简单/中等/困难"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
):
    """获取编程题库列表"""
    all_problems = _load_all_problems()

    if difficulty:
        all_problems = [p for p in all_problems if p.get("difficulty") == difficulty]
    if tag:
        all_problems = [p for p in all_problems if tag in p.get("tags", [])]

    return ok({
        "problems": all_problems,
        "total": len(all_problems),
        "languages": list(LANG_CONFIG.keys()),
    })


@router.get("/problems/{problem_id}", responses=json_responses("NOT_FOUND"))
async def get_problem(problem_id: str):
    """获取编程题详情（含描述、输入输出格式、样例，不含隐藏测试用例）"""
    problem = _load_problem(problem_id)
    if not problem:
        raise ApiError("NOT_FOUND", f"编程题不存在: {problem_id}")

    # 返回给学生时不暴露完整测试用例
    student_view = {
        "id": problem_id,
        "title": problem.get("title", ""),
        "description": problem.get("description", ""),
        "input_format": problem.get("input_format", ""),
        "output_format": problem.get("output_format", ""),
        "difficulty": problem.get("difficulty", "中等"),
        "tags": problem.get("tags", []),
        "sample_input": problem.get("sample_input", ""),
        "sample_output": problem.get("sample_output", ""),
        "suggested_minutes": problem.get("suggested_minutes", "20 分钟"),
        "supported_languages": list(LANG_CONFIG.keys()),
        "test_case_count": len(problem.get("test_cases", [])),
    }
    return ok(student_view)


@router.get("/languages", responses=json_responses())
async def supported_languages():
    """返回支持的编程语言列表"""
    return ok({
        "languages": [
            {"key": k, "label": {"c": "C", "cpp": "C++", "java": "Java", "python": "Python"}[k]}
            for k in LANG_CONFIG.keys()
        ]
    })


# ══════════════════════════════════════════════════════════
# 交互式代码实验
# ══════════════════════════════════════════════════════════

class ExperimentRunRequest(BaseModel):
    """实验运行请求"""
    code: str = Field(..., examples=["import numpy as np\nprint('hello')"])
    student_id: Optional[str] = Field(default=None, examples=["demo-student-01"])
    experiment_id: Optional[str] = None
    parameters: Optional[dict] = Field(default=None, description="参数覆盖，如 {learning_rate: 0.1}")
    time_limit_sec: int = Field(default=30, ge=5, le=120)


@router.post("/experiment", responses=json_responses("EXPERIMENT_FAILED"))
async def run_experiment(request: ExperimentRunRequest):
    """运行交互式代码实验（非判题，返回结构化结果）"""
    if not request.code.strip():
        raise ApiError("BAD_REQUEST", "代码不能为空")

    # 如果有参数覆盖，将代码中的默认值替换
    code = request.code
    if request.parameters:
        for param_name, param_value in request.parameters.items():
            # 简单替换：将 parameter_name = old_value 替换为 parameter_name = new_value
            # 支持 "learning_rate = 0.01" 和 "learning_rate=0.01" 两种格式
            import re as _re
            pattern = rf'({_re.escape(param_name)}\s*=\s*)([^\s\n#]+)'
            replacement = rf'\g<1>{param_value}'
            code = _re.sub(pattern, replacement, code, count=1)

    result = await default_experiment_runner.run(
        code=code,
        time_limit_sec=request.time_limit_sec,
    )

    # 保存学习记录（如有 student_id）
    if request.student_id:
        db = SessionLocal()
        try:
            record_id = str(uuid.uuid4())
            db.add(LearningRecord(
                id=record_id,
                student_id=request.student_id,
                resource_id=request.experiment_id,
                action="code_experiment_run",
                topic=f"experiment:{request.experiment_id or 'free'}",
                score=1.0 if result.status == "success" else 0.0,
            ))
            db.commit()
        except Exception as exc:
            logger.warning(f"保存实验记录失败: {exc}")
        finally:
            db.close()

    return ok({
        "status": result.status,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "metrics": result.metrics,
        "chart_data": result.chart_data,
        "observations": result.observations,
        "execution_time_ms": result.execution_time_ms,
    })
