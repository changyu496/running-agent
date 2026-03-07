"""
文件服务API - 用于提供上传的文件访问
本地：从磁盘读取；OSS：重定向到 OSS URL
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import os

router = APIRouter()


@router.get("/{file_path:path}")
async def get_file(file_path: str):
    """
    获取上传的文件。file_path 可为 uploads/images/xxx.jpg 或仅 xxx.jpg
    """
    from app.utils.storage import is_oss, get_url
    from app.utils.paths import get_project_root

    # 标准化路径
    file_path = file_path.replace("\\", "/").lstrip("/")

    if is_oss():
        # OSS：file_path 可为 key 或 filename，重定向到 OSS URL
        import oss2
        from app.utils.storage import OSS_BUCKET, OSS_ENDPOINT, OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, f"https://{OSS_ENDPOINT}", OSS_BUCKET)
        candidates = [file_path] if file_path.startswith("uploads/") else [
            f"uploads/images/{file_path}",
            f"uploads/videos/{file_path}",
            f"uploads/visualizations/{file_path}",
        ]
        for key in candidates:
            try:
                if bucket.object_exists(key):
                    url = get_url(key)
                    return RedirectResponse(url=url, status_code=302)
            except Exception:
                pass
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

    # 本地存储
    base_dir = get_project_root()
    possible_paths = []
    if file_path.startswith("uploads/"):
        possible_paths.append(os.path.join(base_dir, file_path))
    possible_paths.extend([
        os.path.join(base_dir, "uploads", "images", os.path.basename(file_path)),
        os.path.join(base_dir, "uploads", "videos", os.path.basename(file_path)),
        os.path.join(base_dir, "uploads", "visualizations", os.path.basename(file_path)),
    ])
    if os.path.sep in file_path and not file_path.startswith("uploads/"):
        possible_paths.insert(0, file_path)
        possible_paths.insert(1, os.path.join(base_dir, file_path))

    for path in possible_paths:
        if os.path.exists(path):
            media_type = None
            headers = {}
            fn = path.lower()
            if fn.endswith('.mp4') or fn.endswith('.mov'):
                media_type = 'video/mp4'
                headers['Accept-Ranges'] = 'bytes'
            elif fn.endswith('.webm'):
                media_type = 'video/webm'
                headers['Accept-Ranges'] = 'bytes'
            return FileResponse(path, media_type=media_type, headers=headers)

    raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
