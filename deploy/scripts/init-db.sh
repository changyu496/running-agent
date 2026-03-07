#!/bin/bash
# 在 backend 容器内执行数据库初始化（创建表 + 默认用户 changyu496）
# 用法: ./init-db.sh  或  docker compose exec backend python -c "from app.models.database import init_db; init_db()"

set -e
cd "$(dirname "$0")/.."

echo "执行数据库初始化..."
docker compose exec backend python -c "
from app.models.database import init_db
init_db()
print('完成')
"
echo "默认用户: changyu496 / 31Eq845F"
