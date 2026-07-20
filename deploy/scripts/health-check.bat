@echo off
chcp 65001 >nul

echo.
echo ============================================================
echo   EduAgent 健康检查
echo ============================================================
echo.

cd /d "%~dp0.."

:: 检查容器状态
echo [容器状态]
docker compose -f docker-compose.prod.yml ps
echo.

:: 检查后端健康
echo [后端健康检查]
curl -s http://localhost:8000/api/health 2>nul
if errorlevel 1 (
    echo [警告] 后端未响应，请等待片刻后重试
) else (
    echo.
    echo [OK] 后端正常
)
echo.

:: 检查前端
echo [前端健康检查]
curl -s -o nul -w "HTTP %%{http_code}" http://localhost:3000/ 2>nul
if errorlevel 1 (
    echo [警告] 前端未响应
) else (
    echo.
    echo [OK] 前端正常
)
echo.

:: 显示资源使用
echo [资源使用]
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" eduagent-backend eduagent-frontend 2>nul
echo.

pause
