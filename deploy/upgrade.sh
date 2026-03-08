#!/bin/bash
# 步知 - 服务器一键升级脚本
# 用法：在项目根目录执行 ./deploy/upgrade.sh
#       或在 deploy 目录执行 ./upgrade.sh
# 可选：./deploy/upgrade.sh --no-pull  跳过 git pull（代码已手动上传时使用）

set -e

# 定位项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$SCRIPT_DIR" == *"/deploy" ]]; then
  ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  ROOT="$(cd "$SCRIPT_DIR" && pwd)"
fi
DEPLOY_DIR="$ROOT/deploy"

cd "$ROOT"
echo "=========================================="
echo "  步知 - 服务器升级"
echo "  项目目录: $ROOT"
echo "=========================================="

# 1. 拉取最新代码（可跳过）
if [[ "$1" != "--no-pull" ]]; then
  echo "[1/4] 拉取最新代码..."
  if git rev-parse --git-dir > /dev/null 2>&1; then
    git pull || { echo "  ⚠ git pull 失败，继续使用当前代码构建"; }
  else
    echo "  非 git 仓库，跳过 pull"
  fi
else
  echo "[1/4] 跳过 git pull (--no-pull)"
fi

# 2. 检查 .env
echo "[2/4] 检查环境配置..."
if [ ! -f "$DEPLOY_DIR/.env" ]; then
  echo "  ❌ 未找到 deploy/.env，请先配置："
  echo "     cp deploy/.env.example deploy/.env"
  echo "     nano deploy/.env  # 填写 MYSQL_PASSWORD、SECRET_KEY 等"
  exit 1
fi
echo "  ✓ .env 已存在"

# 3. 构建并启动
echo "[3/4] 构建并重启服务..."
cd "$DEPLOY_DIR"
docker compose up -d --build
echo "  ✓ 容器已启动"

# 4. 健康检查
echo "[4/4] 健康检查..."
sleep 5
for i in {1..12}; do
  if curl -s --connect-timeout 2 --max-time 5 http://localhost:8000/api/health 2>/dev/null | grep -q healthy; then
    echo "  ✓ 后端已就绪"
    echo ""
    echo "=========================================="
    echo "  升级完成！"
    echo "  API: http://localhost:8000"
    echo "  健康检查: curl http://localhost:8000/api/health"
    echo "=========================================="
    exit 0
  fi
  [ $i -lt 12 ] && echo "  等待后端启动... (${i}/12)" && sleep 5
done

echo "  ⚠ 健康检查超时，请查看日志: docker compose -f $DEPLOY_DIR/docker-compose.yml logs backend"
exit 1
