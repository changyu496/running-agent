#!/bin/bash
# 将 Python 后端打包为独立可执行文件，供另一台 Mac 直接使用（无需安装 Python）
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "  打包跑步Agent 后端..."
echo "=========================================="

# 确保 sqlalchemy 已安装（PyInstaller 需能 import 才能打包）
if ! python3 -c "import sqlalchemy" 2>/dev/null; then
  echo "正在安装 sqlalchemy..."
  pip3 install sqlalchemy || { echo "请先运行: pip3 install -r requirements.txt"; exit 1; }
fi

# 检查 PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
  echo "安装 PyInstaller..."
  pip3 install pyinstaller
fi

# 打包（--onedir 比 --onefile 更稳定，尤其对 mediapipe/opencv）
# 将 config.example.json 打入包内，首次运行可复制到 Application Support
python3 -m PyInstaller --clean --noconfirm \
  --name "running-agent-backend" \
  --onedir \
  --add-data "../config.example.json:." \
  --hidden-import "uvicorn.logging" \
  --hidden-import "uvicorn.loops" \
  --hidden-import "uvicorn.loops.auto" \
  --hidden-import "uvicorn.protocols" \
  --hidden-import "uvicorn.protocols.http" \
  --hidden-import "uvicorn.protocols.http.auto" \
  --hidden-import "uvicorn.protocols.websockets" \
  --hidden-import "uvicorn.protocols.websockets.auto" \
  --hidden-import "uvicorn.lifespan" \
  --hidden-import "uvicorn.lifespan.on" \
  --hidden-import "app.utils.paths" \
  --hidden-import "sqlalchemy" \
  --hidden-import "app.api.memo" \
  --hidden-import "app.api.video" \
  --hidden-import "app.api.records" \
  --hidden-import "app.api.stats" \
  --hidden-import "app.api.guidance" \
  --hidden-import "app.api.files" \
  --hidden-import "app.services.qwen_service" \
  --hidden-import "app.services.run_score" \
  --hidden-import "app.services.video_service" \
  --hidden-import "dashscope" \
  --collect-all "mediapipe" \
  --collect-all "cv2" \
  main.py

echo ""
echo "✅ 打包完成: dist/running-agent-backend/"
echo "   可执行文件: dist/running-agent-backend/running-agent-backend"
