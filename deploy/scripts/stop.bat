@echo off
chcp 65001 >nul

echo.
echo ============================================================
echo   EduAgent 停止脚本
echo ============================================================
echo.

cd /d "%~dp0.."

docker compose -f docker-compose.prod.yml down

if errorlevel 1 (
    echo [错误] 停止失败！
    pause
    exit /b 1
)

echo.
echo [OK] EduAgent 已停止
echo.
pause
