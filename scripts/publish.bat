@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   EduAgent 发布脚本 (Windows)
echo   中国软件杯 A3 - 基于大模型的个性化资源生成与学习多智能体系统
echo ============================================================
echo.

set "PROJECT_ROOT=%~dp0.."
set "OUTPUT_DIR=%PROJECT_ROOT%\release"
set "VERSION=%date:~0,4%%date:~5,2%%date:~8,2%"

:: 清理旧的发布目录
if exist "%OUTPUT_DIR%" (
    echo 清理旧发布目录...
    rmdir /s /q "%OUTPUT_DIR%"
)
mkdir "%OUTPUT_DIR%"

:: ============================================================
:: 1. 生成源码包
:: ============================================================
echo [1/2] 生成源码包...

set "SOURCE_DIR=%OUTPUT_DIR%\EduAgent_源码包"
mkdir "%SOURCE_DIR%"

:: 使用 robocopy 复制源码（排除敏感文件和临时文件）
robocopy "%PROJECT_ROOT%" "%SOURCE_DIR%" /e /xd ^
    .git .idea .vscode .pytest_cache __pycache__ node_modules dist .vite ^
    stickynotes .agents .claude release screenshots logs ^
    /xf ^
    .env *.db *.pyc *.log *.tar *.tar.gz *.zip ^
    /njh /njs /ndl /nc /ns

:: 删除不应存在的文件
del /f /q "%SOURCE_DIR%\.env" 2>nul
del /f /q "%SOURCE_DIR%\backend\.env" 2>nul
del /f /q "%SOURCE_DIR%\frontend\.env" 2>nul
del /f /q "%SOURCE_DIR%\frontend\src\eduagent.db" 2>nul

echo [OK] 源码包已生成

:: ============================================================
:: 2. 生成安装运行包
:: ============================================================
echo.
echo [2/2] 生成安装运行包...

set "INSTALL_DIR=%OUTPUT_DIR%\EduAgent_安装运行包"
mkdir "%INSTALL_DIR%"

:: 复制部署目录
xcopy "%PROJECT_ROOT%\deploy\*" "%INSTALL_DIR%\" /e /i /y /q

:: 复制数据目录
mkdir "%INSTALL_DIR%\data"
xcopy "%PROJECT_ROOT%\data\knowledge\*" "%INSTALL_DIR%\data\knowledge\" /e /i /y /q
xcopy "%PROJECT_ROOT%\data\sql\*" "%INSTALL_DIR%\data\sql\" /e /i /y /q
if exist "%PROJECT_ROOT%\data\chroma_db" (
    xcopy "%PROJECT_ROOT%\data\chroma_db\*" "%INSTALL_DIR%\data\chroma_db\" /e /i /y /q
)

:: 复制后端代码
mkdir "%INSTALL_DIR%\backend"
xcopy "%PROJECT_ROOT%\backend\*" "%INSTALL_DIR%\backend\" /e /i /y /q /xd __pycache__ logs
del /f /q "%INSTALL_DIR%\backend\.env" 2>nul
del /f /q "%INSTALL_DIR%\backend\eduagent.db" 2>nul

:: 复制前端代码
mkdir "%INSTALL_DIR%\frontend"
xcopy "%PROJECT_ROOT%\frontend\*" "%INSTALL_DIR%\frontend\" /e /i /y /q /xd node_modules dist
del /f /q "%INSTALL_DIR%\frontend\src\eduagent.db" 2>nul

:: 复制根目录配置
copy "%PROJECT_ROOT%\.env.example" "%INSTALL_DIR%\.env.example" >nul 2>&1
copy "%PROJECT_ROOT%\.dockerignore" "%INSTALL_DIR%\.dockerignore" >nul 2>&1

:: 创建镜像导出目录
mkdir "%INSTALL_DIR%\images"

:: 检查是否有预构建镜像
docker image inspect eduagent-backend:latest >nul 2>&1
if not errorlevel 1 (
    echo   导出后端镜像...
    docker save eduagent-backend:latest -o "%INSTALL_DIR%\images\eduagent-backend.tar"
    echo   [OK] 后端镜像已导出
) else (
    echo   [提示] 未找到后端预构建镜像，安装时将自动构建
)

docker image inspect eduagent-frontend:latest >nul 2>&1
if not errorlevel 1 (
    echo   导出前端镜像...
    docker save eduagent-frontend:latest -o "%INSTALL_DIR%\images\eduagent-frontend.tar"
    echo   [OK] 前端镜像已导出
) else (
    echo   [提示] 未找到前端预构建镜像，安装时将自动构建
)

:: 创建顶层 README
(
echo ============================================================
echo EduAgent - 个性化学习多智能体系统
echo 中国软件杯 A3 - 基于大模型的个性化资源生成与学习多智能体系统
echo ============================================================
echo.
echo 快速开始：
echo.
echo 1. 安装 Docker Desktop
echo    下载地址: https://www.docker.com/products/docker-desktop/
echo.
echo 2. 双击运行 scripts\install.bat
echo.
echo 3. 编辑 .env 文件，填入 API Key
echo.
echo 4. 双击运行 scripts\start.bat
echo.
echo 5. 访问 http://localhost:3000
echo.
echo 演示账号: demo_student / demo123
echo.
echo 详细说明: deploy\README.md
echo 配置说明: deploy\config\CONFIGURATION.md
echo ============================================================
) > "%INSTALL_DIR%\README.txt"

echo [OK] 安装运行包已生成

:: ============================================================
:: 打包为压缩文件
:: ============================================================
echo.
echo 正在打包压缩文件...

cd /d "%OUTPUT_DIR%"

:: 尝试使用 PowerShell 压缩
powershell -Command "Compress-Archive -Path 'EduAgent_源码包' -DestinationPath 'EduAgent_源码包_%VERSION%.zip' -Force" 2>nul
if not errorlevel 1 (
    echo [OK] 源码包压缩完成
) else (
    echo [提示] 压缩失败，请手动压缩
)

powershell -Command "Compress-Archive -Path 'EduAgent_安装运行包' -DestinationPath 'EduAgent_安装运行包_%VERSION%.zip' -Force" 2>nul
if not errorlevel 1 (
    echo [OK] 安装运行包压缩完成
) else (
    echo [提示] 压缩失败，请手动压缩
)

echo.
echo ============================================================
echo   发布完成！
echo ============================================================
echo.
echo   源码包:     %OUTPUT_DIR%\EduAgent_源码包
echo   安装运行包: %OUTPUT_DIR%\EduAgent_安装运行包
echo.
echo   压缩文件:
dir /b "%OUTPUT_DIR%\*.zip" 2>nul
echo.
echo ============================================================
echo.
pause
