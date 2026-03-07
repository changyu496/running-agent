"""
文件服务API - 用于提供上传的文件访问
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/{filename}")
async def get_file(filename: str):
    """
    获取上传的文件
    """
    from app.utils.paths import get_project_root
    base_dir = get_project_root()
    
    # 尝试多个可能的路径
    possible_paths = [
        os.path.join(base_dir, "uploads", "images", filename),
        os.path.join(base_dir, "uploads", "videos", filename),
        os.path.join(base_dir, "uploads", "visualizations", filename),
    ]
    
    # 也尝试完整路径（如果filename包含路径信息）
    if os.path.sep in filename:
        possible_paths.insert(0, filename)
        # 也尝试相对路径
        possible_paths.insert(1, os.path.join(base_dir, filename))
    
    for path in possible_paths:
        if os.path.exists(path):
            media_type = None
            headers = {}
            if filename.lower().endswith('.mp4') or filename.lower().endswith('.mov'):
                media_type = 'video/mp4'
                headers['Accept-Ranges'] = 'bytes'  # 支持视频拖动
            elif filename.lower().endswith('.webm'):
                media_type = 'video/webm'
                headers['Accept-Ranges'] = 'bytes'
            return FileResponse(path, media_type=media_type, headers=headers)
    
    raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
