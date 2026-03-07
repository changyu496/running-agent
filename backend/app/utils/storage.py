"""
存储抽象：本地目录 / OSS
- 本地：STORAGE_TYPE=local 或不设置
- 生产：STORAGE_TYPE=oss，需配置 OSS_* 环境变量
"""
import os
import tempfile
import shutil
from pathlib import Path
from typing import BinaryIO, Optional

STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "local").lower()
OSS_BUCKET = os.environ.get("OSS_BUCKET", "")
OSS_ENDPOINT = os.environ.get("OSS_ENDPOINT", "oss-cn-shanghai.aliyuncs.com")
OSS_ACCESS_KEY_ID = os.environ.get("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET = os.environ.get("OSS_ACCESS_KEY_SECRET", "")


def is_oss() -> bool:
    """是否使用 OSS"""
    return STORAGE_TYPE == "oss" and OSS_BUCKET and OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET


def _get_project_root():
    from app.utils.paths import get_project_root
    return get_project_root()


def save_file(content: BinaryIO, key: str) -> str:
    """
    保存文件，返回存储 key（用于存入 DB）
    key 格式: uploads/images/xxx.jpg, uploads/videos/xxx.mp4, uploads/visualizations/xxx.jpg
    """
    if is_oss():
        import oss2
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        endpoint = f"https://{OSS_ENDPOINT}" if not OSS_ENDPOINT.startswith("http") else OSS_ENDPOINT
        bucket = oss2.Bucket(auth, endpoint, OSS_BUCKET)
        content.seek(0)
        bucket.put_object(key, content.read())
        return key
    else:
        root = _get_project_root()
        full_path = os.path.join(root, key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            content.seek(0)
            shutil.copyfileobj(content, f)
        return key


def save_local_file(local_path: str, key: str) -> str:
    """
    将本地文件上传到存储（用于视频分析生成的 visualization）
    """
    if is_oss():
        import oss2
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        endpoint = f"https://{OSS_ENDPOINT}" if not OSS_ENDPOINT.startswith("http") else OSS_ENDPOINT
        bucket = oss2.Bucket(auth, endpoint, OSS_BUCKET)
        with open(local_path, "rb") as f:
            bucket.put_object(key, f.read())
        return key
    else:
        root = _get_project_root()
        dest = os.path.join(root, key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(local_path, dest)
        return key


def get_local_path(key: str) -> str:
    """
    获取可读的本地路径。OSS 时下载到临时文件并返回临时路径。
    调用方负责处理完后删除临时文件（或使用 with 上下文）。
    """
    if is_oss():
        import oss2
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        endpoint = f"https://{OSS_ENDPOINT}" if not OSS_ENDPOINT.startswith("http") else OSS_ENDPOINT
        bucket = oss2.Bucket(auth, endpoint, OSS_BUCKET)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(key).suffix)
        tmp.close()
        bucket.get_object_to_file(key, tmp.name)
        return tmp.name
    else:
        root = _get_project_root()
        return os.path.join(root, key)


def get_url(key: str, base_url: Optional[str] = None) -> str:
    """
    获取文件访问 URL。
    - OSS: 返回 OSS 公网 URL（需 bucket 为公共读，或使用签名 URL）
    - 本地: 返回 /api/files/{key}，需配合 base_url
    """
    if is_oss():
        # 公共读 bucket: https://bucket.region.aliyuncs.com/key
        return f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{key}"
    else:
        # 本地走 /api/files，key 可能为 uploads/xxx 或仅 filename
        filename = key.split("/")[-1] if "/" in key else key
        if base_url:
            return f"{base_url.rstrip('/')}/api/files/{filename}"
        return f"/api/files/{filename}"


def to_storage_key(path_or_key: str, subdir: str) -> str:
    """
    将路径或 key 转为统一存储 key。
    - 已有 uploads/ 前缀: 直接返回
    - 绝对路径: 提取 uploads/xxx 部分
    - 仅文件名: 返回 uploads/{subdir}/filename
    """
    s = path_or_key.replace("\\", "/")
    if "uploads/" in s:
        idx = s.find("uploads/")
        return s[idx:]
    if s.startswith("/") or (len(s) > 1 and s[1] == ":"):
        # 绝对路径，取最后两级如 images/xxx 或 videos/xxx
        parts = [p for p in s.split("/") if p]
        if len(parts) >= 2:
            return f"uploads/{parts[-2]}/{parts[-1]}"
        return f"uploads/{subdir}/{parts[-1]}" if parts else ""
    return f"uploads/{subdir}/{s}"
