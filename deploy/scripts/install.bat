@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   EduAgent 安装脚本
echo   中国软件杯 A3 - 基于大模型的个性化资源生成与学习多智能体系统
echo ============================================================
echo.

:: 检查 Docker Desktop
echo [1/4] 检查 Docker Desktop...
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Desktop 未运行！
    echo 请先安装并启动 Docker Desktop：
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)
echo [OK] Docker Desktop 已运行

:: 检查 Docker Compose
echo [2/4] 检查 Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Compose 不可用！
    echo 请更新 Docker Desktop 到最新版本。
    echo.
    pause
    exit /b 1
)
echo [OK] Docker Compose 可用

:: 创建 .env 配置文件
echo [3/4] 准备配置文件...
cd /d "%~dp0.."
if not exist ".env" (
    if exist "config\.env.example" (
        copy "config\.env.example" ".env" >nul
        echo [OK] 已创建 .env 配置文件（从模板复制）
        echo.
        echo [提示] 请编辑 .env 文件填入你的 API Key：
        echo   路径: %cd%\.env
        echo.
    ) else (
        echo [警告] 未找到配置模板，将使用默认配置
    )
) else (
    echo [OK] .env 配置文件已存在
)

:: 加载 Docker 镜像
echo [4/4] 加载 Docker 镜像...
set "IMAGES_DIR=%~dp0..\images"
set "LOADED=0"

if exist "%IMAGES_DIR%\eduagent-backend.tar" (
    echo   正在加载后端镜像...
    docker load -i "%IMAGES_DIR%\eduagent-backend.tar"
    if errorlevel 1 (
        echo [错误] 后端镜像加载失败！
        pause
        exit /b 1
    )
    set /a LOADED+=1
) else (
    echo [警告] 未找到后端镜像文件: %IMAGES_DIR%\eduagent-backend.tar
    echo   将尝试从本地构建...
)

if exist "%IMAGES_DIR%\eduagent-frontend.tar" (
    echo   正在加载前端镜像...
    docker load -i "%IMAGES_DIR%\eduagent-frontend.tar"
    if errorlevel 1 (
        echo [错误] 前端镜像加载失败！
        pause
        exit /b 1
    )
    set /a LOADED+=1
) else (
    echo [警告] 未找到前端镜像文件: %IMAGES_DIR%\eduagent-frontend.tar
    echo   将尝试从本地构建...
)

if !LOADED! gtr 0 (
    echo [OK] 已加载 !LOADED! 个 Docker 镜像
) else (
    echo [提示] 未找到预构建镜像，首次启动时将自动构建
)

:: 创建数据卷
echo.
echo 创建持久化数据卷...
docker volume create eduagent-runtime >nul 2>&1
echo [OK] 数据卷已创建

echo.
echo ============================================================
echo   安装完成！
echo ============================================================
echo.
echo   启动系统: scripts\start.bat
echo   访问地址: http://localhost:3000
echo   API 文档: http://localhost:8000/docs
echo.
echo   演示账号: demo_student / demo123
echo.
echo ============================================================
echo.
pause
