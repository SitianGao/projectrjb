@echo off
chcp 65001 >nul

echo.
echo ============================================================
echo   EduAgent 演示数据重置脚本
echo ============================================================
echo.
echo 此操作将：
echo   1. 删除后端运行时数据（数据库、向量库、生成资源）
echo   2. 重新启动后端服务（自动重新初始化演示数据）
echo.
echo [注意] 此操作不可逆！
echo.

set /p confirm="确认重置？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消。
    pause
    exit /b 0
)

cd /d "%~dp0.."

echo.
echo [1/3] 停止后端服务...
docker compose -f docker-compose.prod.yml stop backend

echo [2/3] 清除运行时数据...
docker volume rm eduagent-runtime >nul 2>&1
docker volume create eduagent-runtime >nul 2>&1
echo [OK] 运行时数据已清除

echo [3/3] 重新启动后端服务...
docker compose -f docker-compose.prod.yml up -d backend

echo.
echo [OK] 演示数据已重置
echo [提示] 后端正在重新初始化，约需 1-2 分钟...
echo.
pause
