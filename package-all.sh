#!/bin/bash
# 一键打包：后端 PyInstaller + 前端 React + Electron，生成可直接在另一台 Mac 使用的 .app
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "=========================================="
echo "  跑步Agent 完整打包"
echo "=========================================="

# 1. 打包后端
echo ""
echo "[1/3] 打包 Python 后端..."
cd "$ROOT/backend"
chmod +x build_standalone.sh
./build_standalone.sh
if [ ! -f "dist/running-agent-backend/running-agent-backend" ]; then
  echo "❌ 后端打包失败"
  exit 1
fi

# 2. 打包前端 + Electron
echo ""
echo "[2/3] 打包前端与 Electron..."
cd "$ROOT/frontend"
if ! node -e "require('node:url')" 2>/dev/null; then
  echo "⚠️  需要 Node.js 18+，当前: $(node -v)"
  echo "   请升级: brew install node 或 nvm install 18"
  exit 1
fi
npm run dist

# 3. 输出说明
echo ""
echo "=========================================="
echo "  ✅ 打包完成"
echo "=========================================="
echo ""
echo "输出位置: frontend/dist/"
echo "  - 跑步Agent.app  可双击运行"
echo "  - 跑步Agent-1.0.0.dmg  安装镜像"
echo ""
echo "在另一台 Mac 上："
echo "  1. 复制 跑步Agent.app 到目标 Mac"
echo "  2. 双击即可运行（无需安装 Python）"
echo "  3. 视频分析需目标 Mac 已安装 ffmpeg: brew install ffmpeg"
echo ""
