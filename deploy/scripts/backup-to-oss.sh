#!/bin/bash
# 数据库备份到阿里云 OSS
# 用法: 在服务器上配置 crontab，例如每天凌晨 2 点: 0 2 * * * /opt/running-agent/deploy/scripts/backup-to-oss.sh

set -e
# 进入 deploy 目录（docker compose 需在此运行）
DEPLOY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DEPLOY_DIR"

# 从 .env 加载（需提前配置）
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# 必填：OSS 配置
OSS_BUCKET="${OSS_BUCKET:-}"
OSS_PREFIX="${OSS_PREFIX:-running-agent-backup}"
OSS_ENDPOINT="${OSS_ENDPOINT:-oss-cn-hangzhou.aliyuncs.com}"

if [ -z "$OSS_BUCKET" ]; then
  echo "请设置 OSS_BUCKET 环境变量"
  exit 1
fi

BACKUP_DIR="/tmp/running-agent-backup"
mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="$BACKUP_DIR/running_agent_$STAMP.sql.gz"

# 从 MySQL 容器导出
echo "导出数据库..."
docker compose exec -T mysql mysqldump -u running -p"$MYSQL_PASSWORD" running_agent | gzip > "$DUMP_FILE"

# 上传到 OSS（需安装 ossutil: https://help.aliyun.com/document_detail/120075.html）
if command -v ossutil &>/dev/null; then
  echo "上传到 OSS..."
  ossutil cp "$DUMP_FILE" "oss://$OSS_BUCKET/$OSS_PREFIX/$(basename $DUMP_FILE)"
  echo "备份完成: oss://$OSS_BUCKET/$OSS_PREFIX/$(basename $DUMP_FILE)"
else
  echo "未安装 ossutil，备份文件保存在: $DUMP_FILE"
  echo "安装: https://help.aliyun.com/document_detail/120075.html"
fi

# 清理本地临时文件（保留最近 3 天）
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +3 -delete
