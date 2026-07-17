"""
Online Judge Service — 代码编译执行与判题

支持 C / C++ / Java / Python 四种语言。
Docker 沙箱模式（生产）+ Subprocess 降级模式（开发/演示）。
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from config import PROJECT_ROOT
except ModuleNotFoundError:
    from backend.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# ── 语言配置 ──────────────────────────────────────────
LANG_CONFIG: Dict[str, Dict[str, Any]] = {
    "c": {
        "image": "eduagent-judge-c",
        "ext": ".c",
        "dockerfile": "docker/judge/Dockerfile.c",
        "monaco_lang": "c",
    },
    "cpp": {
        "image": "eduagent-judge-cpp",
        "ext": ".cpp",
        "dockerfile": "docker/judge/Dockerfile.cpp",
        "monaco_lang": "cpp",
    },
    "java": {
        "image": "eduagent-judge-java",
        "ext": ".java",
        "dockerfile": "docker/judge/Dockerfile.java",
        "monaco_lang": "java",
    },
    "python": {
        "image": "eduagent-judge-py",
        "ext": ".py",
        "dockerfile": "docker/judge/Dockerfile.py",
        "monaco_lang": "python",
    },
}

# 判题结果状态
STATUS_AC = "Accepted"
STATUS_WA = "WrongAnswer"
STATUS_TLE = "TimeLimitExceeded"
STATUS_RE = "RuntimeError"
STATUS_CE = "CompileError"


@dataclass
class JudgeConfig:
    time_limit_sec: int = 2       # 每题时间限制（秒）
    memory_limit_mb: int = 256    # 内存限制（MB）
    max_code_len: int = 65536     # 代码最大长度（字节）
    max_output_len: int = 10240   # 输出最大长度（字节）


@dataclass
class TestCaseResult:
    case_id: int
    status: str                    # Accepted | WrongAnswer | TimeLimitExceeded | RuntimeError
    time_ms: float
    memory_kb: int
    expected: str = ""
    actual: str = ""


@dataclass
class JudgeResult:
    status: str                    # Accepted | WrongAnswer | CompileError | TimeLimitExceeded | RuntimeError
    passed: int
    total: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    compile_error: Optional[str] = None
    total_time_ms: float = 0
    max_memory_kb: int = 0


# ── 安全过滤：拦截明显恶意代码 ──
FORBIDDEN_PATTERNS = {
    "c": [
        r"#include\s*<\s*unistd\.h\s*>",     # fork/exec
        r"#include\s*<\s*sys/socket\.h\s*>",  # socket
        r"#include\s*<\s*netinet/in\.h\s*>",  # network
        r"\bfork\s*\(\)",
        r"\bexec[lvpe]*\s*\(",
        r"\bsystem\s*\(",
    ],
    "cpp": [
        r"#include\s*<\s*unistd\.h\s*>",
        r"#include\s*<\s*sys/socket\.h\s*>",
        r"#include\s*<\s*netinet/in\.h\s*>",
        r"\bfork\s*\(\)",
        r"\bexec[lvpe]*\s*\(",
        r"\bsystem\s*\(",
        r"\bstd::system\s*\(",
    ],
    "java": [
        r"\bRuntime\.getRuntime\(\)\.exec\s*\(",
        r"\bProcessBuilder\b",
        r"\bjava\.net\.Socket\b",
        r"\bjava\.net\.URL\b",
        r"\bjava\.io\.File\(",
        r"\bFileWriter\b",
        r"\bFileOutputStream\b",
        r"\bFiles\.write\b",
        r"\bFiles\.delete\b",
    ],
    "python": [
        r"\b__import__\s*\(\s*['\"]os['\"]\s*\)",
        r"\bexec\s*\(",
        r"\beval\s*\(",
        r"\bopen\s*\(.*['\"][wa]",
        r"\b__builtins__\b",
        r"\bctypes\b",
    ],
}


class SandboxService:
    """代码沙箱执行 —— Docker 优先 + subprocess 降级"""

    def __init__(self, use_docker: Optional[bool] = None):
        self.use_docker = use_docker if use_docker is not None else self._detect_docker()

    @staticmethod
    def _detect_docker() -> bool:
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            logger.warning("Docker 不可用，切换到 Subprocess 沙箱模式")
            return False

    # ── 公共入口 ────────────────────────────────────────

    async def run(
        self,
        code: str,
        language: str,
        test_cases: List[dict],
        config: Optional[JudgeConfig] = None,
    ) -> JudgeResult:
        """执行代码判题"""
        cfg = config or JudgeConfig()
        lang_cfg = LANG_CONFIG.get(language)
        if not lang_cfg:
            raise ValueError(f"不支持的语言: {language}")

        # 安全检查
        safety_error = self._check_safety(code, language, cfg)
        if safety_error:
            return JudgeResult(
                status=STATUS_CE,
                passed=0,
                total=len(test_cases),
                compile_error=safety_error,
            )

        if self.use_docker:
            return await self._run_docker(code, language, test_cases, cfg, lang_cfg)
        else:
            return await self._run_subprocess(code, language, test_cases, cfg, lang_cfg)

    # ── Docker 沙箱 ─────────────────────────────────────

    async def _run_docker(
        self, code: str, language: str, test_cases: list,
        cfg: JudgeConfig, lang_cfg: dict,
    ) -> JudgeResult:
        work_dir = Path(tempfile.mkdtemp(prefix="eduagent_judge_"))
        try:
            # 写入代码文件
            code_file = work_dir / f"Main{lang_cfg['ext']}"
            code_file.write_text(code, encoding="utf-8")

            # 写入测试用例
            for i, tc in enumerate(test_cases):
                (work_dir / f"input_{i}.txt").write_text(
                    tc.get("input", ""), encoding="utf-8"
                )
                (work_dir / f"expected_{i}.txt").write_text(
                    str(tc.get("expected_output", tc.get("output", ""))), encoding="utf-8"
                )

            # 构建并运行 Docker
            image = lang_cfg["image"]
            judge_script = str(Path(PROJECT_ROOT) / "docker" / "judge" / "judge.sh")

            cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                f"--memory={cfg.memory_limit_mb}m",
                "--cpus=0.5",
                "--pids-limit=50",
                "--read-only",
                f"--tmpfs=/tmp:rw,noexec,nosuid,size=128m",
                "-v", f"{work_dir}:/work:ro",
                "-v", f"{judge_script}:/judge.sh:ro",
                "--entrypoint", "/bin/bash",
                image, "/judge.sh",
                language, f"/work/Main{lang_cfg['ext']}",
                "/work", str(cfg.time_limit_sec),
                str(cfg.memory_limit_mb * 1024),
            ]

            logger.debug(f"Docker cmd: {' '.join(cmd[:8])}...")

            process = await _run_async(cmd)
            stdout = process.stdout or ""

            return self._parse_judge_output(stdout, len(test_cases))

        except Exception as exc:
            logger.exception(f"Docker 判题异常: {exc}")
            return JudgeResult(
                status=STATUS_RE,
                passed=0, total=len(test_cases),
            )
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    # ── Subprocess 降级 ─────────────────────────────────

    async def _run_subprocess(
        self, code: str, language: str, test_cases: list,
        cfg: JudgeConfig, lang_cfg: dict,
    ) -> JudgeResult:
        work_dir = Path(tempfile.mkdtemp(prefix="eduagent_judge_"))
        try:
            code_file = work_dir / f"Main{lang_cfg['ext']}"
            code_file.write_text(code, encoding="utf-8")

            results: List[TestCaseResult] = []

            # ── 编译 ──
            compile_ok, compile_err = self._local_compile(language, code_file, work_dir)
            if not compile_ok:
                return JudgeResult(
                    status=STATUS_CE,
                    passed=0, total=len(test_cases),
                    compile_error=compile_err[:2000],
                )

            # ── 执行各测试用例 ──
            for i, tc in enumerate(test_cases):
                tc_input = tc.get("input", "")
                tc_expected = str(tc.get("expected_output", tc.get("output", "")))

                try:
                    exec_result = self._local_run(
                        language, work_dir, tc_input, cfg.time_limit_sec
                    )
                except subprocess.TimeoutExpired:
                    results.append(TestCaseResult(
                        case_id=i, status=STATUS_TLE,
                        time_ms=cfg.time_limit_sec * 1000, memory_kb=0,
                        expected=tc_expected, actual="",
                    ))
                    continue

                if exec_result["exit_code"] != 0:
                    results.append(TestCaseResult(
                        case_id=i, status=STATUS_RE,
                        time_ms=exec_result["time_ms"], memory_kb=0,
                        expected=tc_expected,
                        actual=exec_result.get("stderr", "")[:500],
                    ))
                    continue

                actual = exec_result["stdout"].strip()
                expected = tc_expected.strip()

                if actual == expected:
                    results.append(TestCaseResult(
                        case_id=i, status=STATUS_AC,
                        time_ms=exec_result["time_ms"], memory_kb=0,
                    ))
                else:
                    results.append(TestCaseResult(
                        case_id=i, status=STATUS_WA,
                        time_ms=exec_result["time_ms"], memory_kb=0,
                        expected=expected, actual=actual,
                    ))

            passed = sum(1 for r in results if r.status == STATUS_AC)
            total = len(test_cases)

            if total == 0:
                overall = STATUS_AC
            elif any(r.status == STATUS_RE for r in results):
                overall = STATUS_RE
            elif any(r.status == STATUS_TLE for r in results):
                overall = STATUS_TLE
            elif passed < total:
                overall = STATUS_WA
            else:
                overall = STATUS_AC

            return JudgeResult(
                status=overall, passed=passed, total=total,
                results=[{
                    "case_id": r.case_id, "status": r.status,
                    "time_ms": r.time_ms, "memory_kb": r.memory_kb,
                    "expected": r.expected, "actual": r.actual,
                } for r in results],
                total_time_ms=sum(r.time_ms for r in results),
            )

        except Exception as exc:
            logger.exception(f"Subprocess 判题异常: {exc}")
            return JudgeResult(status=STATUS_RE, passed=0, total=len(test_cases))
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    # ── 本地编译/执行辅助 ──────────────────────────────

    @staticmethod
    def _local_compile(language: str, code_file: Path, work_dir: Path) -> tuple:
        try:
            if language == "c":
                result = subprocess.run(
                    ["gcc", "-Wall", "-O2", str(code_file), "-o", str(work_dir / "prog")],
                    capture_output=True, text=True, timeout=30,
                )
            elif language == "cpp":
                result = subprocess.run(
                    ["g++", "-Wall", "-O2", "-std=c++17", str(code_file), "-o", str(work_dir / "prog")],
                    capture_output=True, text=True, timeout=30,
                )
            elif language == "java":
                result = subprocess.run(
                    ["javac", "-d", str(work_dir), str(code_file)],
                    capture_output=True, text=True, timeout=30,
                )
            else:  # python — 仅语法检查
                result = subprocess.run(
                    ["python3", "-c",
                     f"import py_compile; py_compile.compile('{code_file}', doraise=True)"],
                    capture_output=True, text=True, timeout=10,
                )

            if result.returncode != 0:
                return False, result.stderr or "编译失败"
            return True, None
        except FileNotFoundError:
            return False, f"编译器未安装: {language}"
        except subprocess.TimeoutExpired:
            return False, "编译超时"
        except Exception as exc:
            return False, f"编译异常: {exc}"

    @staticmethod
    def _local_run(language: str, work_dir: Path, stdin_text: str,
                   timeout_sec: int) -> dict:
        import time
        start = time.time()

        try:
            if language == "java":
                proc = subprocess.run(
                    ["java", "-cp", str(work_dir), "Main"],
                    input=stdin_text, capture_output=True, text=True,
                    timeout=timeout_sec + 1,
                )
            elif language == "python":
                proc = subprocess.run(
                    ["python3", str(work_dir / "Main.py")],
                    input=stdin_text, capture_output=True, text=True,
                    timeout=timeout_sec + 1,
                )
            else:
                proc = subprocess.run(
                    [str(work_dir / "prog")],
                    input=stdin_text, capture_output=True, text=True,
                    timeout=timeout_sec + 1,
                )
            elapsed = (time.time() - start) * 1000

            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout or "",
                "stderr": proc.stderr or "",
                "time_ms": round(elapsed, 1),
            }
        except subprocess.TimeoutExpired:
            elapsed = (time.time() - start) * 1000
            raise

    # ── 安全检查 ─────────────────────────────────────────

    def _check_safety(self, code: str, language: str, cfg: JudgeConfig) -> Optional[str]:
        if len(code.encode("utf-8")) > cfg.max_code_len:
            return f"代码超出最大长度限制 ({cfg.max_code_len} 字节)"

        patterns = FORBIDDEN_PATTERNS.get(language, [])
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return f"代码包含禁用模式: {pattern}"

        return None

    # ── 输出解析 ─────────────────────────────────────────

    @staticmethod
    def _parse_judge_output(stdout: str, total_cases: int) -> JudgeResult:
        """解析 Docker 容器输出的 JSON"""
        try:
            data = json.loads(stdout.strip())
            return JudgeResult(
                status=data.get("status", STATUS_WA),
                passed=data.get("passed", 0),
                total=data.get("total", total_cases),
                results=data.get("results", []),
                compile_error=data.get("compile_error"),
            )
        except json.JSONDecodeError:
            # 尝试从输出中提取 JSON（前面可能有日志）
            m = re.search(r'\{.*"status".*\}', stdout, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group())
                    return JudgeResult(
                        status=data.get("status", STATUS_WA),
                        passed=data.get("passed", 0),
                        total=data.get("total", total_cases),
                        results=data.get("results", []),
                        compile_error=data.get("compile_error"),
                    )
                except json.JSONDecodeError:
                    pass
            return JudgeResult(
                status=STATUS_RE,
                passed=0, total=total_cases,
            )


# ── 异步 subprocess ────────────────────────────────────

async def _run_async(cmd: List[str]) -> subprocess.CompletedProcess:
    """Async wrapper for subprocess"""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


# 模块单例
default_sandbox = SandboxService()
