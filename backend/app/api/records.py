"""
历史记录API
"""
from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.database import SessionLocal, Record, CorosData, VideoAnalysis
import json

router = APIRouter()

class RecordListItem(BaseModel):
    id: int
    created_at: str
    record_type: str
    run_date: Optional[str] = None
    run_type: Optional[str] = None
    run_score: Optional[int] = None
    distance: Optional[float] = None
    avg_pace: Optional[str] = None
    avg_heart_rate: Optional[int] = None
    avg_cadence: Optional[int] = None

class RecordDetail(BaseModel):
    id: int
    created_at: str
    record_type: str
    run_date: Optional[str] = None
    run_type: Optional[str] = None
    run_score: Optional[int] = None
    memo_text: Optional[str] = None
    coros_image_path: Optional[str] = None
    video_path: Optional[str] = None
    video_angle: Optional[str] = None
    analysis_result: Optional[dict] = None
    coros_data: Optional[dict] = None
    video_analysis: Optional[dict] = None
    linked_records: Optional[List[int]] = None

@router.get("/list", response_model=List[RecordListItem])
async def get_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    record_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    获取记录列表
    """
    try:
        db = SessionLocal()
        query = db.query(Record)
        
        # 筛选类型
        if record_type:
            query = query.filter(Record.record_type == record_type)
        
        # 搜索
        if search:
            query = query.filter(Record.memo_text.contains(search))
        
        # 排序和分页
        records = query.order_by(Record.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for record in records:
            # 获取高驰数据
            coros_data = db.query(CorosData).filter(CorosData.record_id == record.id).first()
            
            item = RecordListItem(
                id=record.id,
                created_at=record.created_at.isoformat(),
                record_type=record.record_type,
                run_date=record.run_date or (record.created_at.strftime("%Y-%m-%d") if record.created_at else None),
                run_type=record.run_type,
                run_score=record.run_score,
                distance=coros_data.distance if coros_data else None,
                avg_pace=coros_data.avg_pace if coros_data else None,
                avg_heart_rate=coros_data.avg_heart_rate if coros_data else None,
                avg_cadence=coros_data.avg_cadence if coros_data else None
            )
            result.append(item)
        
        db.close()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{record_id}", response_model=RecordDetail)
async def get_record_detail(record_id: int):
    """
    获取记录详情
    """
    try:
        db = SessionLocal()
        record = db.query(Record).filter(Record.id == record_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        # 获取高驰数据
        coros_data = db.query(CorosData).filter(CorosData.record_id == record.id).first()
        coros_dict = None
        if coros_data:
            coros_dict = {
                "distance": coros_data.distance,
                "duration": coros_data.duration,
                "avg_pace": coros_data.avg_pace,
                "avg_heart_rate": coros_data.avg_heart_rate,
                "max_heart_rate": coros_data.max_heart_rate,
                "avg_cadence": coros_data.avg_cadence,
                "avg_stride_length": coros_data.avg_stride_length,
                "avg_power": coros_data.avg_power,
                "max_power": getattr(coros_data, "max_power", None),
                "form_power": getattr(coros_data, "form_power", None),
                "form_power_ratio": getattr(coros_data, "form_power_ratio", None),
                "avg_gct": getattr(coros_data, "avg_gct", None),
                "vertical_oscillation": getattr(coros_data, "vertical_oscillation", None),
                "calories": coros_data.calories
            }
        
        # 获取视频分析数据
        video_analysis = db.query(VideoAnalysis).filter(VideoAnalysis.record_id == record.id).first()
        video_dict = None
        if video_analysis:
            video_dict = {
                "video_angle": video_analysis.video_angle,
                "keypoints_data": json.loads(video_analysis.keypoints_data) if video_analysis.keypoints_data else None,
                "angles_data": json.loads(video_analysis.angles_data) if video_analysis.angles_data else None,
                "symmetry_data": json.loads(video_analysis.symmetry_data) if video_analysis.symmetry_data else None,
                "visualization_path": video_analysis.visualization_path,
                "overall_score": video_analysis.overall_score,
                "analysis_text": video_analysis.analysis_text
            }
        
        # 解析分析结果
        analysis_result = None
        if record.analysis_result:
            try:
                analysis_result = json.loads(record.analysis_result)
            except:
                analysis_result = {"raw_text": record.analysis_result}

        # 若跑步分数为 0 但有 data_overview，尝试重新计算（兼容旧数据及中文键名）
        if (record.run_score is None or record.run_score == 0) and analysis_result:
            do = analysis_result.get("data_overview") or {}
            if do and isinstance(do, dict):
                try:
                    from app.services.run_score import compute_run_score
                    new_score = compute_run_score(do)
                    if new_score > 0:
                        record.run_score = new_score
                        db.commit()
                except Exception:
                    pass
        
        # 解析关联记录
        linked_records = None
        if record.linked_record_ids:
            try:
                linked_records = json.loads(record.linked_record_ids)
            except:
                linked_records = []
        
        db.close()
        
        return RecordDetail(
            id=record.id,
            created_at=record.created_at.isoformat(),
            record_type=record.record_type,
            run_date=record.run_date or (record.created_at.strftime("%Y-%m-%d") if record.created_at else None),
            run_type=record.run_type,
            run_score=record.run_score,
            memo_text=record.memo_text,
            coros_image_path=record.coros_image_path,
            video_path=record.video_path,
            video_angle=record.video_angle,
            analysis_result=analysis_result,
            coros_data=coros_dict,
            video_analysis=video_dict,
            linked_records=linked_records
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RecordUpdateBody(BaseModel):
    run_date: Optional[str] = None
    run_type: Optional[str] = None

@router.patch("/{record_id}")
async def update_record(record_id: int, body: RecordUpdateBody = Body(default=RecordUpdateBody())):
    """更新记录的跑步日期、训练类型"""
    try:
        db = SessionLocal()
        record = db.query(Record).filter(Record.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        if body.run_date is not None:
            record.run_date = body.run_date
        if body.run_type is not None:
            record.run_type = body.run_type
        db.commit()
        db.close()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{record_id}")
async def delete_record(record_id: int):
    """
    删除记录
    """
    try:
        db = SessionLocal()
        record = db.query(Record).filter(Record.id == record_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        db.delete(record)
        db.commit()
        db.close()
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/link")
async def link_records(record_ids: List[int] = Body(...)):
    """
    手动关联记录
    """
    try:
        db = SessionLocal()
        
        if len(record_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要2条记录才能关联")
        
        # 更新所有记录
        linked_ids_json = json.dumps(record_ids)
        for record_id in record_ids:
            record = db.query(Record).filter(Record.id == record_id).first()
            if record:
                record.is_linked = True
                record.linked_record_ids = linked_ids_json
        
        db.commit()
        db.close()
        
        return {"success": True, "linked_count": len(record_ids)}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unlink/{record_id}")
async def unlink_record(record_id: int):
    """
    解除记录关联
    """
    try:
        db = SessionLocal()
        record = db.query(Record).filter(Record.id == record_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        record.is_linked = False
        record.linked_record_ids = None
        
        db.commit()
        db.close()
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-link")
async def auto_link():
    """
    自动关联记录
    """
    try:
        from app.services.link_service import auto_link_records
        linked_groups = auto_link_records()
        return {"success": True, "linked_groups": linked_groups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
