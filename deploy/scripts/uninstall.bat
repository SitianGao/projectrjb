@echo off
chcp 65001 >nul

echo.
echo ============================================================
echo   EduAgent 卸载脚本
echo ============================================================
echo.
echo 此操作将：
echo   1. 停止所有容器
echo   2. 删除所有容器和网络
echo   3. 删除数据卷（运行时数据）
echo   4. 删除 Docker 镜像
echo.
echo [注意] 此操作不可逆！所有运行时数据将被删除！
echo.

set /p confirm="确认卸载？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消。
    pause
    exit /b 0
)

cd /d "%~dp0.."

echo.
echo [1/4] 停止并删除容器...
docker compose -f docker-compose.prod.yml down -v

echo [2/4] 删除数据卷...
docker volume rm eduagent-runtime >nul 2>&1

echo [3/4] 删除镜像...
docker rmi eduagent-backend:latest >nul 2>&1
docker rmi eduagent-frontend:latest >nul 2>&1

echo [4/4] 清理配置...
if exist ".env" (
    set /p delenv="是否删除 .env 配置文件？(Y/N): "
    if /i "!delenv!"=="Y" (
        del ".env"
        echo [OK] .env 已删除
    ) else (
        echo [跳过] 保留 .env
    )
)

echo.
echo [OK] EduAgent 已卸载
echo.
pause
