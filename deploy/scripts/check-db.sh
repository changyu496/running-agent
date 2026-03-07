#!/bin/bash
# 检查 MySQL 中是否有 users 表和默认用户
# 用法: ./check-db.sh（需在 deploy/ 目录下执行，或 cd deploy && ./scripts/check-db.sh）

set -e
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && source .env && set +a

echo "检查 MySQL 数据库..."
docker compose exec mysql mysql -urunning -p"${MYSQL_PASSWORD}" running_agent -e "
SHOW TABLES;
SELECT '--- users 表 ---' as '';
SELECT id, username, created_at FROM users;
" 2>/dev/null || {
  echo "提示: 需在 deploy 目录执行，且 .env 已配置 MYSQL_PASSWORD"
  echo "或手动执行: docker compose exec mysql mysql -urunning -p你的密码 running_agent -e 'SELECT * FROM users;'"
  exit 1
}
