"""
pytest 共享 fixtures — 供 test/ 目录下所有测试使用

asyncio_mode = "auto" 已在 pyproject.toml 中配置，
pytest-asyncio 1.4+ 自动管理事件循环，无需手动定义 event_loop fixture。
"""
