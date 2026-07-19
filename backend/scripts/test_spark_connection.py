"""
讯飞星火 Spark X2 连接测试脚本。

用法：
    cd backend
    python scripts/test_spark_connection.py

功能：
    1. 非流式调用验证基本连接
    2. 流式调用验证 SSE 解析
    3. 通过 LLMClient 验证 Agent 调用路径
    4. 脱敏输出，不打印完整密钥
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 确保 backend 目录在 Python path 中
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import config  # noqa: E402


def mask_secret(value: str, show: int = 4) -> str:
    """脱敏显示密钥，只保留前 show 个字符。"""
    if not value:
        return "<未配置>"
    if len(value) <= show:
        return "*" * len(value)
    return value[:show] + "*" * (len(value) - show)


def is_placeholder(value: str) -> bool:
    """检查值是否为占位符（包含非 ASCII 字符）。"""
    try:
        value.encode("ascii")
        return False
    except UnicodeEncodeError:
        return True


def check_api_key() -> bool:
    """检查 API 密钥是否有效。"""
    api_password = config.SPARK_API_PASSWORD
    if not api_password or is_placeholder(api_password):
        return False
    return True


async def test_non_stream() -> bool:
    """测试非流式调用。"""
    import httpx

    api_url = config.SPARK_API_URL
    api_password = config.SPARK_API_PASSWORD
    model = config.SPARK_MODEL

    print("=" * 60)
    print("[测试 1] 非流式调用")
    print(f"  URL:   {api_url}")
    print(f"  Model: {model}")
    print(f"  Key:   {mask_secret(api_password)}")
    print()

    if not check_api_key():
        print("  [SKIP] SPARK_API_PASSWORD 未配置或为占位符")
        return False

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "请只回复：Spark X2 连接成功"}],
        "stream": False,
    }

    try:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT) as client:
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_password}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            elapsed = int((time.monotonic() - start) * 1000)

            print(f"  HTTP 状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"  [FAIL] 请求失败: {response.text[:200]}")
                return False

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            print(f"  响应内容: {content.strip()}")
            print(f"  Token 用量: prompt={usage.get('prompt_tokens', '?')}, "
                  f"completion={usage.get('completion_tokens', '?')}, "
                  f"total={usage.get('total_tokens', '?')}")
            print(f"  耗时: {elapsed}ms")
            print("  [PASS] 非流式调用成功")
            return True

    except httpx.TimeoutException:
        print(f"  [FAIL] 超时 ({config.LLM_TIMEOUT}s)")
        return False
    except httpx.HTTPStatusError as e:
        print(f"  [FAIL] HTTP 错误: {e.response.status_code}")
        print(f"     {e.response.text[:200]}")
        return False
    except Exception as e:
        print(f"  [FAIL] 异常: {type(e).__name__}: {e}")
        return False


async def test_stream() -> bool:
    """测试流式调用。"""
    import httpx

    api_url = config.SPARK_API_URL
    api_password = config.SPARK_API_PASSWORD
    model = config.SPARK_MODEL

    print()
    print("=" * 60)
    print("[测试 2] 流式调用")
    print(f"  URL:   {api_url}")
    print(f"  Model: {model}")
    print()

    if not check_api_key():
        print("  [SKIP] SPARK_API_PASSWORD 未配置或为占位符")
        return False

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "请只回复：流式连接成功"}],
        "stream": True,
    }

    try:
        start = time.monotonic()
        chunks: list[str] = []
        chunk_count = 0

        async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT) as client:
            async with client.stream(
                "POST",
                api_url,
                headers={
                    "Authorization": f"Bearer {api_password}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as response:
                print(f"  HTTP 状态码: {response.status_code}")

                if response.status_code != 200:
                    body = await response.aread()
                    print(f"  [FAIL] 请求失败: {body.decode()[:200]}")
                    return False

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                chunks.append(content)
                                chunk_count += 1
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

        elapsed = int((time.monotonic() - start) * 1000)
        full_text = "".join(chunks)

        print(f"  收到 {chunk_count} 个 chunk")
        print(f"  响应内容: {full_text.strip()}")
        print(f"  耗时: {elapsed}ms")

        if chunk_count == 0:
            print("  [WARN] 未收到任何内容块")
            return False

        print("  [PASS] 流式调用成功")
        return True

    except httpx.TimeoutException:
        print(f"  [FAIL] 超时 ({config.LLM_TIMEOUT}s)")
        return False
    except httpx.HTTPStatusError as e:
        print(f"  [FAIL] HTTP 错误: {e.response.status_code}")
        return False
    except Exception as e:
        print(f"  [FAIL] 异常: {type(e).__name__}: {e}")
        return False


async def test_llm_client() -> bool:
    """测试通过 LLMClient 调用（Agent 调用路径）。"""
    print()
    print("=" * 60)
    print("[测试 3] LLMClient 调用 (Agent 路径)")
    print()

    if not check_api_key():
        print("  [SKIP] SPARK_API_PASSWORD 未配置或为占位符")
        return False

    try:
        from agents.llm_client import LLMClient

        client = LLMClient(primary="spark")

        start = time.monotonic()
        result = await client.chat(
            system="你是一个教育助手",
            user="请只回复：LLMClient 连接成功",
        )
        elapsed = int((time.monotonic() - start) * 1000)

        print(f"  响应内容: {result.strip()}")
        print(f"  耗时: {elapsed}ms")

        if client.last_usage:
            print(f"  Provider: {client.last_usage.provider}")
            print(f"  Model: {client.last_usage.model}")

        print("  [PASS] LLMClient 调用成功")
        return True

    except Exception as e:
        print(f"  [FAIL] 异常: {type(e).__name__}: {e}")
        return False


async def test_llm_client_json() -> bool:
    """测试 LLMClient JSON 调用（结构化输出）。"""
    print()
    print("=" * 60)
    print("[测试 4] LLMClient JSON 调用 (结构化输出)")
    print()

    if not check_api_key():
        print("  [SKIP] SPARK_API_PASSWORD 未配置或为占位符")
        return False

    try:
        from agents.llm_client import LLMClient

        client = LLMClient(primary="spark")

        start = time.monotonic()
        result = await client.chat_json(
            system="你是一个教育助手，请用JSON格式回答",
            user='请返回一个JSON对象，包含status字段，值为"success"',
        )
        elapsed = int((time.monotonic() - start) * 1000)

        print(f"  响应内容: {json.dumps(result, ensure_ascii=False)}")
        print(f"  耗时: {elapsed}ms")

        if client.last_usage:
            print(f"  Provider: {client.last_usage.provider}")
            print(f"  Model: {client.last_usage.model}")

        print("  [PASS] LLMClient JSON 调用成功")
        return True

    except Exception as e:
        print(f"  [FAIL] 异常: {type(e).__name__}: {e}")
        return False


async def main():
    print("+" + "-" * 58 + "+")
    print("|        讯飞星火 Spark X2 连接测试                       |")
    print("+" + "-" * 58 + "+")
    print()
    print("当前配置:")
    print(f"  LLM_PRIMARY:    {config.LLM_PRIMARY}")
    print(f"  SPARK_MODEL:    {config.SPARK_MODEL}")
    print(f"  SPARK_BASE_URL: {config.SPARK_BASE_URL}")
    print(f"  SPARK_API_URL:  {config.SPARK_API_URL}")
    print(f"  SPARK_ENABLED:  {config.SPARK_ENABLED}")
    print(f"  SPARK_PROTOCOL: {config.SPARK_PROTOCOL}")
    print(f"  SPARK_KEY:      {mask_secret(config.SPARK_API_PASSWORD)}")
    print(f"  LLM_TIMEOUT:    {config.LLM_TIMEOUT}s")
    print(f"  LLM_MAX_RETRIES:{config.LLM_MAX_RETRIES}")

    results = {}
    results["非流式"] = await test_non_stream()
    results["流式"] = await test_stream()
    results["LLMClient"] = await test_llm_client()
    results["LLMClient JSON"] = await test_llm_client_json()

    print()
    print("=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    all_pass = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {name:20s} {status}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("[OK] 全部测试通过! Spark X2 配置正确。")
    else:
        print("[WARN] 部分测试失败，请检查配置。")
        if not check_api_key():
            print("       提示: 请在 backend/.env 中填写真实的 SPARK_API_PASSWORD")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
