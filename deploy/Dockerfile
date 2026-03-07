# 跑步Agent 后端 - 云端部署
# 国内服务器使用 DaoCloud 镜像，避免 Docker Hub 拉取超时
FROM docker.m.daocloud.io/library/python:3.11-slim

WORKDIR /app

# 系统依赖（OpenCV、媒体处理等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（国内使用清华 PyPI 镜像加速）
COPY backend/requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt

# 云端额外依赖
RUN pip install --no-cache-dir \
    pymysql \
    cryptography \
    python-jose[cryptography] \
    passlib[bcrypt]

# 应用代码
COPY backend/ /app/

# 数据目录
RUN mkdir -p /app/uploads/images /app/uploads/videos /app/uploads/visualizations

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
