#!/bin/bash
# 仅打包前端：连接云端 API，不包含后端
# 用法: ./package-frontend-only.sh [API_URL]
# 示例: ./package-frontend-only.sh http://47.101.135.105:8000

set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

API_URL="${1:-http://47.101.135.105:8000}"

echo "=========================================="
echo "  步知 - 仅打包前端（云端模式）"
echo "=========================================="
echo ""
echo "API 地址: $API_URL"
echo ""

# 1. 更新 config.json
CONFIG="$ROOT/frontend/public/config.json"
echo "[1/3] 配置 API 地址..."
echo "{\"apiUrl\": \"$API_URL\"}" > "$CONFIG"
echo "      已写入 $CONFIG"

# 2. 构建前端
echo ""
echo "[2/3] 构建 React 前端..."
cd "$ROOT/frontend"
npm run build

# 3. 打包 Electron（不包含后端）
echo ""
echo "[3/3] 打包 Electron..."
npx electron-builder --mac --config electron-builder-cloud.json

echo ""
echo "=========================================="
echo "  ✅ 打包完成"
echo "=========================================="
echo ""
echo "输出位置: frontend/dist/"
echo "  - 步知.app"
echo "  - 步知-1.0.0.dmg"
echo ""
echo "双击运行后，将连接云端 API: $API_URL"
echo ""
echo "若 Electron 打包失败（如 node:url 报错），请升级 Node.js:"
echo "  brew install node  或  nvm install 18"
echo ""
