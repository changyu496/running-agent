#!/bin/bash
# 步知 - 本地模式启动脚本（后端 + 前端 + Electron）
# 用法：./start-local.sh          # 正常启动
#       ./start-local.sh --restart  # 强制重启后端

set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

# 切换到本地配置（public 和 build 都要更新，Electron 有 build 时从 build 加载）
CONFIG_SRC="$ROOT/frontend/public/config.local.json"
CONFIG_DST="$ROOT/frontend/public/config.json"
BUILD_CONFIG="$ROOT/frontend/build/config.json"
if [ -f "$CONFIG_SRC" ]; then
  cp "$CONFIG_SRC" "$CONFIG_DST"
  [ -d "$ROOT/frontend/build" ] && cp "$CONFIG_SRC" "$BUILD_CONFIG" && echo "已切换为本地配置 (public + build)"
  [ ! -d "$ROOT/frontend/build" ] && echo "已切换为本地配置 (apiUrl: http://localhost:8000)"
else
  echo "警告: config.local.json 不存在，请确保 config.json 中 apiUrl 为 http://localhost:8000"
fi

# 强制重启
if [ "$1" = "--restart" ] || [ "$1" = "-r" ]; then
  echo "正在停止旧后端..."
  for pid in $(lsof -t -i :8000 2>/dev/null); do
    kill -9 "$pid" 2>/dev/null || true
  done
  pkill -9 -f "python.*main.py" 2>/dev/null || true
  pkill -9 -f "uvicorn.*main:app" 2>/dev/null || true
  sleep 2
  echo "已停止，继续启动..."
fi

CURL_OPTS="--connect-timeout 2 --max-time 5 -s"

echo "=========================================="
echo "  步知 · 本地模式启动"
echo "=========================================="
echo "  提示：Electron 将加载 localhost:3000（最新代码），进度条等新功能可见"
echo ""

# 1. 启动后端
if ! curl $CURL_OPTS -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null | grep -q 200; then
  echo "[1/3] 正在启动后端 (Python)..."
  cd "$ROOT/backend"
  if ! python3 -c "import passlib" 2>/dev/null; then
    echo "      安装认证依赖..."
    pip install -q passlib[bcrypt] python-jose[cryptography] 2>/dev/null || pip install passlib[bcrypt] python-jose[cryptography]
  fi
  python3 main.py &
  cd "$ROOT"
  echo "      等待后端就绪..."
  for i in {1..30}; do
    if curl $CURL_OPTS http://localhost:8000/api/health 2>/dev/null | grep -q healthy; then
      echo "      后端已就绪 ✓"
      break
    fi
    [ $((i % 5)) -eq 0 ] && echo "      已等待 ${i}s..."
    sleep 1
  done
  if ! curl $CURL_OPTS http://localhost:8000/api/health 2>/dev/null | grep -q healthy; then
    echo "      警告: 后端可能尚未就绪"
  fi
else
  echo "[1/3] 后端已在运行 ✓"
fi

# 2. 启动前端
FRONTEND_READY=0
if curl $CURL_OPTS -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q 200; then
  echo "[2/3] 前端已在运行 ✓"
  FRONTEND_READY=1
else
  echo "[2/3] 正在启动前端 (React)..."
  cd "$ROOT/frontend"
  [ ! -d "node_modules" ] && echo "      安装依赖..." && npm install
  BROWSER=none DISABLE_ESLINT_PLUGIN=true npx react-scripts start &
  cd "$ROOT"
  echo "      等待前端编译..."
  for i in {1..180}; do
    if curl $CURL_OPTS -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q 200; then
      echo "      前端已就绪 ✓"
      FRONTEND_READY=1
      break
    fi
    [ $((i % 15)) -eq 0 ] && echo "      已等待 ${i}s..."
    sleep 1
  done
  [ "$FRONTEND_READY" -eq 0 ] && echo "❌ 前端未能就绪" && exit 1
fi

# 3. 启动 Electron
echo "[3/3] 正在打开应用窗口..."
echo ""
echo "  侧边栏将显示「本地」标签，表示已连接本地后端"
echo "  关闭窗口后，后端与前端仍在运行"
echo ""
cd "$ROOT/frontend"
SKIP_BACKEND_START=1 exec npx electron .
