"""路径工具：开发环境、打包、云端部署均能正确解析"""
import os
import sys

def get_backend_root():
    """backend 根目录（数据库等，即包含 main.py 的目录）"""
    # 云端 Docker：数据库由 DATABASE_URL 指定，此路径仅用于 SQLite 本地开发
    if getattr(sys, "frozen", False):
        home = os.path.expanduser("~")
        return os.path.join(home, "Library", "Application Support", "步知")
    # app/utils/paths.py -> app/utils -> app -> backend
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_project_root():
    """项目根目录（uploads 等，即包含 uploads/ 的父目录）"""
    # 云端 Docker：UPLOAD_DIR 为 /app/uploads，则 project_root = /app
    upload_dir = os.environ.get("UPLOAD_DIR")
    if upload_dir:
        return os.path.dirname(upload_dir)  # /app/uploads -> /app
    return get_backend_root()
