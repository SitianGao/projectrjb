"""
pytest 共享 fixtures — 供 test/ 目录下所有测试使用

asyncio_mode = "auto" 已在 pyproject.toml 中配置；
若本地环境未安装 pytest-asyncio，则使用下面的轻量兼容钩子运行 async tests。
"""

from __future__ import annotations

import asyncio
import inspect


def pytest_pyfunc_call(pyfuncitem):
    """Run async tests when pytest-asyncio is unavailable in a local env."""
    if pyfuncitem.config.pluginmanager.hasplugin("asyncio"):
        return None

    test_fn = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_fn):
        return None

    fixture_names = pyfuncitem._fixtureinfo.argnames
    kwargs = {name: pyfuncitem.funcargs[name] for name in fixture_names}
    asyncio.run(test_fn(**kwargs))
    return True
