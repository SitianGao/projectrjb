@echo off
chcp 65001 >nul

echo.
echo ============================================================
echo   EduAgent 日志查看
echo ============================================================
echo.
echo 按 Ctrl+C 退出日志查看
echo.

cd /d "%~dp0.."

if "%1"=="" (
    docker compose -f docker-compose.prod.yml logs -f --tail=100
) else if "%1"=="backend" (
    docker compose -f docker-compose.prod.yml logs -f --tail=100 backend
) else if "%1"=="frontend" (
    docker compose -f docker-compose.prod.yml logs -f --tail=100 frontend
) else (
    echo 用法: view-logs.bat [backend^|frontend]
    echo   无参数 - 查看所有日志
    echo   backend - 只看后端日志
    echo   frontend - 只看前端日志
    pause
)
