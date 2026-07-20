@echo off
chcp 65001 >nul

echo.
echo ============================================================
echo   EduAgent 重启脚本
echo ============================================================
echo.

cd /d "%~dp0.."

echo 正在停止...
docker compose -f docker-compose.prod.yml down

echo.
echo 正在启动...
docker compose -f docker-compose.prod.yml up -d

if errorlevel 1 (
    echo [错误] 重启失败！
    pause
    exit /b 1
)

echo.
echo [OK] EduAgent 已重启
echo.
echo   前端地址:  http://localhost:3000
echo   后端 API:  http://localhost:8000
echo.
pause
