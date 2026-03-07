#!/bin/bash
# 跑步Agent 一键启动脚本（Mac）
# 用法：./start.sh          # 正常启动
#       ./start.sh --restart  # 强制重启后端（更新代码后使用）

set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

# 强制重启：先杀掉占用 8000 端口的进程
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

# curl 统一加超时，避免卡住
CURL_OPTS="--connect-timeout 2 --max-time 5 -s"

echo "=========================================="
echo "  跑步Agent 启动中..."
echo "=========================================="

# 1. 启动后端（若未在运行）
if ! curl $CURL_OPTS -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null | grep -q 200; then
  echo "[1/3] 正在启动后端 (Python)..."
  cd "$ROOT/backend"
  # 确保认证依赖已安装（passlib、python-jose）
  if ! python3 -c "import passlib" 2>/dev/null; then
    echo "      安装认证依赖 (passlib, python-jose)..."
    pip install -q passlib[bcrypt] python-jose[cryptography] 2>/dev/null || pip install passlib[bcrypt] python-jose[cryptography]
  fi
  python3 main.py &
  BACKEND_PID=$!
  cd "$ROOT"
  echo "      等待后端就绪..."
  for i in {1..30}; do
    if curl $CURL_OPTS http://localhost:8000/api/health 2>/dev/null | grep -q healthy; then
      echo "      后端已就绪 (PID: $BACKEND_PID)"
      break
    fi
    [ $((i % 5)) -eq 0 ] && echo "      已等待 ${i}s..."
    sleep 1
  done
  if ! curl $CURL_OPTS http://localhost:8000/api/health 2>/dev/null | grep -q healthy; then
    echo "      警告: 后端可能尚未就绪，请查看上方是否有 Python 报错"
  fi
else
  echo "[1/3] 后端已在运行，跳过"
fi

# 2. 启动前端开发服务器（若未在运行）
FRONTEND_READY=0
if curl $CURL_OPTS -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q 200; then
  echo "[2/3] 前端已在运行，跳过"
  FRONTEND_READY=1
else
  echo "[2/3] 正在启动前端 (React)，首次编译约需 2-3 分钟..."
  cd "$ROOT/frontend"
  # 确保依赖已安装
  if [ ! -d "node_modules" ]; then
    echo "      首次运行，正在安装依赖 (npm install)..."
    npm install
  fi
  BROWSER=none DISABLE_ESLINT_PLUGIN=true npx react-scripts start &
  FRONTEND_PID=$!
  cd "$ROOT"
  echo "      等待前端编译完成..."
  for i in {1..180}; do
    if curl $CURL_OPTS -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q 200; then
      echo "      前端已就绪 (PID: $FRONTEND_PID)"
      FRONTEND_READY=1
      break
    fi
    [ $((i % 15)) -eq 0 ] && echo "      已等待 ${i}s，首次编译较慢请耐心等待..."
    sleep 1
  done
  if [ "$FRONTEND_READY" -eq 0 ]; then
    echo ""
    echo "  ❌ 前端未能就绪。请检查上方是否有报错。"
    echo "  手动启动前端: cd frontend && npm run dev:react"
    echo "  等待出现 'Compiled successfully!' 后，再执行 ./start.sh"
    echo ""
    exit 1
  fi
fi

# 3. 启动 Electron（Mac 应用窗口）
echo "[3/3] 正在打开 跑步Agent 应用窗口..."
echo ""
echo "  请使用弹出的「跑步Agent」窗口，不要用浏览器打开 localhost。"
echo "  关闭窗口后，后端与前端仍在运行；再次执行 ./start.sh 可重新打开应用。"
echo ""
cd "$ROOT/frontend"
SKIP_BACKEND_START=1 exec npx electron .
