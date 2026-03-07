"""
视频分析API
"""
import json
import logging
import asyncio
import threading
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request

logger = logging.getLogger(__name__)

# 视频分析执行日志（供前端轮询，缓解等待焦虑）
VIDEO_LOGS = []
VIDEO_LOGS_LOCK = threading.Lock()
MAX_LOGS = 80
from typing import Optional
import os
import shutil
from datetime import datetime
from app.services.video_service import VideoAnalyzer
from app.services.qwen_service import analyze_video_pose
from app.models.database import SessionLocal, Record, VideoAnalysis, init_db

router = APIRouter()
# 不再在各 api 模块重复调用，由 main.py 统一初始化
# init_db()

from app.utils.paths import get_project_root
from app.utils.storage import is_oss, save_file, get_local_path, save_local_file, to_storage_key
import tempfile
import os as os_module

UPLOAD_DIR = os.path.join(get_project_root(), "uploads", "videos")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _append_log(msg: str):
    with VIDEO_LOGS_LOCK:
        VIDEO_LOGS.append(msg)
        if len(VIDEO_LOGS) > MAX_LOGS:
            VIDEO_LOGS.pop(0)


@router.get("/logs")
async def get_video_logs():
    """获取最近视频分析执行日志（供前端轮询）"""
    with VIDEO_LOGS_LOCK:
        return {"logs": list(VIDEO_LOGS)}


# 视频上传最大 2GB（Starlette 0.40+ 支持 max_part_size，旧版默认仅 1MB）
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024


async def _parse_form(request):
    """解析 form，若 Starlette 支持 max_part_size 则使用以支持大文件"""
    import inspect
    sig = inspect.signature(request.form)
    if "max_part_size" in sig.parameters:
        return await request.form(max_part_size=MAX_VIDEO_SIZE)
    return await request.form()


@router.post("/analyze")
async def analyze_video(request: Request):
    """
    分析跑步视频。Starlette 0.40+ 支持大文件(>1MB)，旧版仅支持 1MB 以内。
    升级: pip install 'starlette>=0.40.0'
    """
    try:
        form = await _parse_form(request)
        video = form.get("video")
        angle = form.get("angle", "side")
        force_flip_180 = form.get("force_flip_180", "false")
        if not video or not hasattr(video, "file"):
            raise HTTPException(status_code=400, detail="请上传视频文件")
        if angle not in ["side", "back"]:
            raise HTTPException(status_code=400, detail="角度必须是 'side' 或 'back'")

        force_flip = (force_flip_180 or "").lower() in ("true", "1", "yes")
        with VIDEO_LOGS_LOCK:
            VIDEO_LOGS.clear()
        _append_log("收到请求，开始处理...")
        logger.info("[视频分析] 收到请求，角度=%s，画面倒置=%s", angle, force_flip)
        # 保存上传的视频（本地或 OSS）
        fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{video.filename}"
        video_key = f"uploads/videos/{fname}"
        video.file.seek(0)
        save_file(video.file, video_key)
        _append_log("视频已保存")
        logger.info("[视频分析] 视频已保存: %s", video_key)

        # MediaPipe 需要本地路径，OSS 时下载到临时文件
        video_path = get_local_path(video_key)
        output_dir = None
        if is_oss():
            output_dir = os.path.join(tempfile.gettempdir(), "buzhi_vis")
            os.makedirs(output_dir, exist_ok=True)
        try:
            _append_log("开始 MediaPipe 姿态检测...")
            logger.info("[视频分析] 开始 MediaPipe 姿态检测...")
            analyzer = VideoAnalyzer()
            loop = asyncio.get_event_loop()
            analysis_data = await loop.run_in_executor(
                None,
                lambda: analyzer.analyze_video(video_path, angle, force_flip_180=force_flip, output_dir=output_dir, log_cb=_append_log)
            )
            _append_log(f"MediaPipe 完成，已提取 {analysis_data.get('frame_count', 0)} 帧数据")
            logger.info("[视频分析] MediaPipe 完成，已提取 %d 帧数据", analysis_data.get("frame_count", 0))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"视频分析失败: {str(e)}")
        
        # 调用Qwen分析（带错误处理）- Qwen 只接受图片，必须用 visualization_image_path
        qwen_result = {}
        vis_image = analysis_data.get("visualization_image_path")
        vis_image = vis_image if vis_image and not str(vis_image).lower().endswith(('.mp4', '.mov', '.webm')) else None
        try:
            if vis_image and os.path.exists(vis_image):
                _append_log("调用 Qwen AI 分析跑姿...")
                logger.info("[视频分析] 调用 Qwen AI 分析跑姿...")
                qwen_result = analyze_video_pose(
                    analysis_data["keypoints_data"],
                    analysis_data["angles_data"],
                    vis_image,
                    angle,
                    analysis_data.get("symmetry_data")
                )
            else:
                logger.warning("[视频分析] 无可视化图片，跳过 Qwen AI 分析")
                qwen_result = {"raw_text": "未生成可视化图片，仅提供基础姿态数据"}
        except Exception as e:
            logger.warning("[视频分析] Qwen 分析失败: %s", e)
            # Qwen分析失败不影响基本分析结果
            qwen_result = {
                "raw_text": f"AI分析失败: {str(e)}，但基本姿态数据已提取",
                "error": str(e)
            }
        
        # 计算整体评分（基于角度数据）
        overall_score = 85  # 默认分数
        if angle == "side":
            angles = eval(analysis_data["angles_data"]) if isinstance(analysis_data["angles_data"], str) else analysis_data["angles_data"]
            # 简单的评分逻辑
            if angles.get("knee_angle", 0) > 110:
                overall_score += 5
            if abs(angles.get("torso_lean", 0)) < 10:
                overall_score += 5
        else:
            symmetry = eval(analysis_data["symmetry_data"]) if isinstance(analysis_data["symmetry_data"], str) else analysis_data["symmetry_data"]
            if symmetry.get("shoulder_balance_angle", 0) < 5:
                overall_score += 5

        _append_log(f"分析完成，整体评分 {overall_score}")
        logger.info("[视频分析] 完成，整体评分=%d", overall_score)

        # OSS 时上传可视化文件
        vis_path = analysis_data["visualization_path"]
        vis_key = f"uploads/visualizations/{os.path.basename(vis_path)}"
        if is_oss():
            save_local_file(vis_path, vis_key)
            vis_img = analysis_data.get("visualization_image_path")
            if vis_img and os_module.path.exists(vis_img):
                vis_img_key = f"uploads/visualizations/{os.path.basename(vis_img)}"
                save_local_file(vis_img, vis_img_key)
        else:
            vis_key = vis_path

        # 格式化 AI 分析结果：优先用 raw_text，否则将 dict 转为 JSON 供前端解析展示
        if isinstance(qwen_result, dict) and "raw_text" in qwen_result:
            analysis_text_val = qwen_result["raw_text"]
        elif isinstance(qwen_result, dict):
            analysis_text_val = json.dumps(qwen_result, ensure_ascii=False)
        else:
            analysis_text_val = str(qwen_result)

        if is_oss() and video_path.startswith(tempfile.gettempdir()):
            try:
                os_module.unlink(video_path)
            except Exception:
                pass

        return {
            "success": True,
            "video_path": video_key,
            "video_angle": angle,
            "keypoints_data": analysis_data["keypoints_data"],
            "angles_data": analysis_data["angles_data"],
            "symmetry_data": analysis_data.get("symmetry_data"),
            "visualization_path": vis_key,
            "overall_score": overall_score,
            "analysis_text": analysis_text_val,
            "qwen_result": qwen_result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_video_record(
    record_id: int = Form(...),  # 必选：关联的跑步记录 ID
    video_path: str = Form(...),
    video_angle: str = Form(...),
    keypoints_data: str = Form(...),
    angles_data: str = Form(...),
    symmetry_data: Optional[str] = Form(None),
    visualization_path: str = Form(...),
    overall_score: int = Form(...),
    analysis_text: str = Form(...)
):
    """
    保存视频分析到指定跑步记录（必须关联）
    """
    try:
        db = SessionLocal()
        record = db.query(Record).filter(Record.id == record_id).first()
        if not record:
            db.close()
            raise HTTPException(status_code=404, detail="所选跑步记录不存在")
        if record.record_type not in ("memo", "both"):
            db.close()
            raise HTTPException(status_code=400, detail="只能关联备忘录分析类型的跑步记录")

        # 若该记录已有视频分析，先删除
        existing = db.query(VideoAnalysis).filter(VideoAnalysis.record_id == record_id).first()
        if existing:
            db.delete(existing)

        # 更新记录：添加视频路径，类型改为 both
        record.video_path = video_path
        record.video_angle = video_angle
        record.record_type = "both"
        record.analysis_result = record.analysis_result  # 保留原有备忘录分析

        # 创建视频分析数据
        video_analysis = VideoAnalysis(
            record_id=record_id,
            video_angle=video_angle,
            keypoints_data=keypoints_data,
            angles_data=angles_data,
            symmetry_data=symmetry_data,
            visualization_path=visualization_path,
            overall_score=overall_score,
            analysis_text=analysis_text
        )
        db.add(video_analysis)
        db.commit()
        db.close()

        return {"success": True, "record_id": record_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
