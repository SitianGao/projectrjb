#!/bin/bash
# =============================================================
# EduAgent 发布脚本
# 生成两个规范交付目录：
#   1. EduAgent_源码包
#   2. EduAgent_安装运行包
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/release"
VERSION=$(date +%Y%m%d)

echo ""
echo "============================================================"
echo "  EduAgent 发布脚本"
echo "  中国软件杯 A3 - 基于大模型的个性化资源生成与学习多智能体系统"
echo "============================================================"
echo ""

# 清理旧的发布目录
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# ============================================================
# 1. 生成源码包
# ============================================================
echo "[1/2] 生成源码包..."

SOURCE_DIR="$OUTPUT_DIR/EduAgent_源码包"
mkdir -p "$SOURCE_DIR"

# 复制源码（排除敏感文件和临时文件）
rsync -a \
    --exclude='.git' \
    --exclude='.idea' \
    --exclude='.vscode' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='*.db' \
    --exclude='logs/' \
    --exclude='node_modules/' \
    --exclude='dist/' \
    --exclude='.vite/' \
    --exclude='stickynotes/' \
    --exclude='.agents/' \
    --exclude='.claude/' \
    --exclude='release/' \
    --exclude='screenshots/' \
    --exclude='*.tar' \
    --exclude='*.log' \
    "$PROJECT_ROOT/" "$SOURCE_DIR/"

# 确保 .env.example 存在但 .env 不存在
rm -f "$SOURCE_DIR/.env" "$SOURCE_DIR/backend/.env" "$SOURCE_DIR/frontend/.env"
rm -f "$SOURCE_DIR/frontend/src/eduagent.db"

# 创建 .env 从模板
if [ -f "$PROJECT_ROOT/.env.example" ]; then
    cp "$PROJECT_ROOT/.env.example" "$SOURCE_DIR/.env.example"
fi

echo "[OK] 源码包已生成: $SOURCE_DIR"

# ============================================================
# 2. 生成安装运行包
# ============================================================
echo ""
echo "[2/2] 生成安装运行包..."

INSTALL_DIR="$OUTPUT_DIR/EduAgent_安装运行包"
mkdir -p "$INSTALL_DIR"

# 复制部署目录
cp -r "$PROJECT_ROOT/deploy/"* "$INSTALL_DIR/"

# 复制数据目录（知识库、SQL、向量库）
mkdir -p "$INSTALL_DIR/data"
cp -r "$PROJECT_ROOT/data/knowledge" "$INSTALL_DIR/data/"
cp -r "$PROJECT_ROOT/data/sql" "$INSTALL_DIR/data/"
if [ -d "$PROJECT_ROOT/data/chroma_db" ]; then
    cp -r "$PROJECT_ROOT/data/chroma_db" "$INSTALL_DIR/data/"
fi

# 复制后端代码（用于构建镜像）
mkdir -p "$INSTALL_DIR/backend"
cp -r "$PROJECT_ROOT/backend/"* "$INSTALL_DIR/backend/"
rm -f "$INSTALL_DIR/backend/.env"
rm -f "$INSTALL_DIR/backend/eduagent.db"
rm -rf "$INSTALL_DIR/backend/__pycache__"
rm -rf "$INSTALL_DIR/backend/logs"

# 复制前端代码（用于构建镜像）
mkdir -p "$INSTALL_DIR/frontend"
cp -r "$PROJECT_ROOT/frontend/"* "$INSTALL_DIR/frontend/"
rm -rf "$INSTALL_DIR/frontend/node_modules"
rm -rf "$INSTALL_DIR/frontend/dist"
rm -f "$INSTALL_DIR/frontend/src/eduagent.db"

# 复制根目录配置文件
cp "$PROJECT_ROOT/.env.example" "$INSTALL_DIR/.env.example" 2>/dev/null || true
cp "$PROJECT_ROOT/.dockerignore" "$INSTALL_DIR/" 2>/dev/null || true

# 创建镜像导出目录
mkdir -p "$INSTALL_DIR/images"

# 检查是否有预构建镜像
if docker image inspect eduagent-backend:latest >/dev/null 2>&1; then
    echo "  导出后端镜像..."
    docker save eduagent-backend:latest -o "$INSTALL_DIR/images/eduagent-backend.tar"
    echo "  [OK] 后端镜像已导出"
else
    echo "  [提示] 未找到后端预构建镜像，安装时将自动构建"
fi

if docker image inspect eduagent-frontend:latest >/dev/null 2>&1; then
    echo "  导出前端镜像..."
    docker save eduagent-frontend:latest -o "$INSTALL_DIR/images/eduagent-frontend.tar"
    echo "  [OK] 前端镜像已导出"
else
    echo "  [提示] 未找到前端预构建镜像，安装时将自动构建"
fi

# 创建顶层 README
cat > "$INSTALL_DIR/README.txt" << 'EOF'
============================================================
EduAgent - 个性化学习多智能体系统
中国软件杯 A3 - 基于大模型的个性化资源生成与学习多智能体系统
============================================================

快速开始：

1. 安装 Docker Desktop
   下载地址: https://www.docker.com/products/docker-desktop/

2. 双击运行 scripts\install.bat

3. 编辑 .env 文件，填入 API Key

4. 双击运行 scripts\start.bat

5. 访问 http://localhost:3000

演示账号: demo_student / demo123

详细说明: deploy\README.md
配置说明: deploy\config\CONFIGURATION.md
============================================================
EOF

echo "[OK] 安装运行包已生成: $INSTALL_DIR"

# ============================================================
# 打包为压缩文件
# ============================================================
echo ""
echo "正在打包压缩文件..."

cd "$OUTPUT_DIR"
if command -v zip >/dev/null 2>&1; then
    zip -r "EduAgent_源码包_${VERSION}.zip" "EduAgent_源码包/"
    zip -r "EduAgent_安装运行包_${VERSION}.zip" "EduAgent_安装运行包/"
    echo "[OK] 压缩包已生成"
elif command -v tar >/dev/null 2>&1; then
    tar -czf "EduAgent_源码包_${VERSION}.tar.gz" "EduAgent_源码包/"
    tar -czf "EduAgent_安装运行包_${VERSION}.tar.gz" "EduAgent_安装运行包/"
    echo "[OK] 压缩包已生成"
else
    echo "[提示] 未找到 zip/tar 命令，请手动压缩 release 目录"
fi

echo ""
echo "============================================================"
echo "  发布完成！"
echo "============================================================"
echo ""
echo "  源码包:     $OUTPUT_DIR/EduAgent_源码包"
echo "  安装运行包: $OUTPUT_DIR/EduAgent_安装运行包"
echo ""
echo "  压缩文件:"
ls -lh "$OUTPUT_DIR"/*.zip "$OUTPUT_DIR"/*.tar.gz 2>/dev/null || echo "  （请手动压缩）"
echo ""
echo "============================================================"
