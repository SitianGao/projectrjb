@echo off
chcp 65001 >nul
setlocal

echo.
echo ============================================================
echo   EduAgent 启动脚本
echo ============================================================
echo.

cd /d "%~dp0.."

:: 检查 Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Desktop 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

:: 检查镜像是否存在，决定是否需要构建
docker image inspect eduagent-backend:latest >nul 2>&1
if errorlevel 1 (
    echo [提示] 未找到预构建镜像，将从源码构建（首次可能需要 5-10 分钟）...
    echo.
    docker compose -f docker-compose.prod.yml build
    if errorlevel 1 (
        echo [错误] 镜像构建失败！
        pause
        exit /b 1
    )
)

echo 正在启动 EduAgent...
echo.

docker compose -f docker-compose.prod.yml up -d

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！请检查日志: scripts\view-logs.bat
    pause
    exit /b 1
)

echo.
echo [OK] EduAgent 已启动
echo.
echo   前端地址:  http://localhost:3000
echo   后端 API:  http://localhost:8000
echo   API 文档:  http://localhost:8000/docs
echo   健康检查:  http://localhost:8000/api/health
echo.
echo   演示账号:  demo_student / demo123
echo.
echo [提示] 后端首次启动需要初始化数据库和 RAG，约需 1-2 分钟。
echo        请等待片刻后刷新页面。
echo.
pause
