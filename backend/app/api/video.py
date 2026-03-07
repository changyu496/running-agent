"""
视频分析API
"""
import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

logger = logging.getLogger(__name__)
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
UPLOAD_DIR = os.path.join(get_project_root(), "uploads", "videos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    angle: str = Form(...),  # "side" or "back"
    force_flip_180: str = Form("false")  # 画面倒置时传 "true"
):
    """
    分析跑步视频
    """
    if angle not in ["side", "back"]:
        raise HTTPException(status_code=400, detail="角度必须是 'side' 或 'back'")
    
    try:
        force_flip = (force_flip_180 or "").lower() in ("true", "1", "yes")
        logger.info("[视频分析] 收到请求，角度=%s，画面倒置=%s", angle, force_flip)
        # 保存上传的视频
        file_path = os.path.join(UPLOAD_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{video.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        logger.info("[视频分析] 视频已保存: %s", file_path)

        # 使用MediaPipe分析视频
        try:
            logger.info("[视频分析] 开始 MediaPipe 姿态检测...")
            analyzer = VideoAnalyzer()
            analysis_data = analyzer.analyze_video(file_path, angle, force_flip_180=force_flip)
            logger.info("[视频分析] MediaPipe 完成，已提取 %d 帧数据", analysis_data.get("frame_count", 0))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"视频分析失败: {str(e)}")
        
        # 调用Qwen分析（带错误处理）- Qwen 只接受图片，必须用 visualization_image_path
        qwen_result = {}
        vis_image = analysis_data.get("visualization_image_path")
        vis_image = vis_image if vis_image and not str(vis_image).lower().endswith(('.mp4', '.mov', '.webm')) else None
        try:
            if vis_image and os.path.exists(vis_image):
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

        logger.info("[视频分析] 完成，整体评分=%d", overall_score)
        # 格式化 AI 分析结果：优先用 raw_text，否则将 dict 转为 JSON 供前端解析展示
        if isinstance(qwen_result, dict) and "raw_text" in qwen_result:
            analysis_text_val = qwen_result["raw_text"]
        elif isinstance(qwen_result, dict):
            analysis_text_val = json.dumps(qwen_result, ensure_ascii=False)
        else:
            analysis_text_val = str(qwen_result)

        return {
            "success": True,
            "video_path": file_path,
            "video_angle": angle,
            "keypoints_data": analysis_data["keypoints_data"],
            "angles_data": analysis_data["angles_data"],
            "symmetry_data": analysis_data.get("symmetry_data"),
            "visualization_path": analysis_data["visualization_path"],
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
