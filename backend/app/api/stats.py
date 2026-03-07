"""
数据统计API
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from app.models.database import SessionLocal, Record, CorosData
from sqlalchemy import func

router = APIRouter()

@router.get("/overview")
async def get_stats_overview(
    days: int = Query(30, ge=1, le=365)
):
    """
    获取统计数据概览
    """
    try:
        db = SessionLocal()
        
        # 时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取所有记录
        records = db.query(Record).filter(
            Record.created_at >= start_date,
            Record.created_at <= end_date
        ).all()
        
        # 获取高驰数据
        coros_records = db.query(CorosData).join(Record).filter(
            Record.created_at >= start_date,
            Record.created_at <= end_date
        ).all()
        
        # 计算统计数据
        total_count = len(records)
        total_distance = sum(r.distance for r in coros_records if r.distance) or 0
        avg_pace_list = [r.avg_pace for r in coros_records if r.avg_pace]
        avg_heart_rate_list = [r.avg_heart_rate for r in coros_records if r.avg_heart_rate]
        avg_cadence_list = [r.avg_cadence for r in coros_records if r.avg_cadence]
        
        avg_pace = None
        if avg_pace_list:
            # 简单计算平均配速（这里简化处理）
            avg_pace = avg_pace_list[0]  # 实际应该解析配速字符串并计算
        
        avg_heart_rate = sum(avg_heart_rate_list) / len(avg_heart_rate_list) if avg_heart_rate_list else 0
        avg_cadence = sum(avg_cadence_list) / len(avg_cadence_list) if avg_cadence_list else 0
        
        db.close()
        
        return {
            "total_count": total_count,
            "total_distance": round(total_distance, 1),
            "avg_pace": avg_pace,
            "avg_heart_rate": round(avg_heart_rate),
            "avg_cadence": round(avg_cadence),
            "period_days": days
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
async def get_trends(
    metric: str = Query("pace", regex="^(pace|heart_rate|distance|cadence)$"),
    days: int = Query(90, ge=7, le=365)
):
    """
    获取趋势数据
    """
    try:
        db = SessionLocal()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 按日期分组统计
        records = db.query(
            func.date(Record.created_at).label('date'),
            func.avg(CorosData.distance).label('avg_distance'),
            func.avg(CorosData.avg_heart_rate).label('avg_hr'),
            func.avg(CorosData.avg_cadence).label('avg_cadence')
        ).join(CorosData).filter(
            Record.created_at >= start_date,
            Record.created_at <= end_date
        ).group_by(func.date(Record.created_at)).all()
        
        trends = []
        for record in records:
            data_point = {
                "date": record.date.isoformat() if hasattr(record.date, 'isoformat') else str(record.date),
            }
            
            if metric == "pace":
                data_point["value"] = None  # 需要解析配速
            elif metric == "heart_rate":
                data_point["value"] = round(record.avg_hr) if record.avg_hr else None
            elif metric == "distance":
                data_point["value"] = round(record.avg_distance, 2) if record.avg_distance else None
            elif metric == "cadence":
                data_point["value"] = round(record.avg_cadence) if record.avg_cadence else None
            
            trends.append(data_point)
        
        db.close()
        
        return {
            "metric": metric,
            "trends": trends,
            "period_days": days
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
