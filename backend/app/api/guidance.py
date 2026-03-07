"""
智能指导API
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from app.models.database import SessionLocal, Record, CorosData
from app.utils.config import get_user_info, get_training_goals, get_personal_bests
from app.services.qwen_service import analyze_coros_image
import json

router = APIRouter()

@router.get("/")
async def get_guidance():
    """
    获取智能指导
    """
    try:
        db = SessionLocal()
        
        # 获取用户信息
        user_info = get_user_info()
        training_goals = get_training_goals()
        personal_bests = get_personal_bests()
        
        # 获取最近一周的数据
        week_ago = datetime.now() - timedelta(days=7)
        week_records = db.query(Record).filter(
            Record.created_at >= week_ago
        ).all()
        
        # 获取最近一个月的数据
        month_ago = datetime.now() - timedelta(days=30)
        month_records = db.query(Record).filter(
            Record.created_at >= month_ago
        ).all()
        
        # 计算统计数据
        week_coros = db.query(CorosData).join(Record).filter(
            Record.created_at >= week_ago
        ).all()
        
        month_coros = db.query(CorosData).join(Record).filter(
            Record.created_at >= month_ago
        ).all()
        
        week_distance = sum(r.distance for r in week_coros if r.distance) or 0
        week_count = len(week_records)
        week_avg_hr = sum(r.avg_heart_rate for r in week_coros if r.avg_heart_rate) / len(week_coros) if week_coros else 0
        
        month_distance = sum(r.distance for r in month_coros if r.distance) or 0
        month_count = len(month_records)
        
        # 构建提示词给Qwen生成建议
        prompt = f"""基于以下跑步数据，生成个性化的训练指导建议：

用户信息：
- 年龄：{user_info.get('age')}岁
- 身高：{user_info.get('height')}cm
- 体重：{user_info.get('weight')}kg
- 最大心率：{user_info.get('max_heart_rate')}bpm
- 静息心率：{user_info.get('resting_heart_rate')}bpm

个人最佳成绩：
- 半马：{personal_bests.get('half_marathon', 'N/A')}
- 全马：{personal_bests.get('marathon', 'N/A')}
- 10公里：{personal_bests.get('10k', 'N/A')}

训练目标：
- 有氧配速：{training_goals.get('aerobic_pace', 'N/A')}
- 周跑量目标：{training_goals.get('weekly_distance_target', 'N/A')}km
- 周训练次数：{training_goals.get('weekly_sessions', 'N/A')}次

本周数据：
- 跑步次数：{week_count}次
- 总距离：{week_distance:.1f}km
- 平均心率：{week_avg_hr:.0f}bpm

最近一个月数据：
- 跑步次数：{month_count}次
- 总距离：{month_distance:.1f}km

请生成：
1. 本周训练总结
2. 趋势分析（进步/下降）
3. 下周训练建议（具体、可执行）
4. 注意事项和健康提醒

请以JSON格式返回，包含：week_summary, trend_analysis, next_week_suggestions, health_reminders
"""
        
        # 这里简化处理，直接生成文本建议
        # 实际应该调用Qwen API，但为了简化，先返回结构化数据
        
        week_summary = f"本周你完成了{week_count}次跑步，总距离{week_distance:.1f}km。"
        if week_count > 0:
            week_summary += f"平均心率{week_avg_hr:.0f}bpm，训练强度适中。"
        
        trend_analysis = []
        if month_count > week_count * 4:
            trend_analysis.append("训练频率保持稳定")
        if week_distance > training_goals.get('weekly_distance_target', 0) * 0.8:
            trend_analysis.append("周跑量接近目标")
        
        next_week_suggestions = [
            f"继续保持{training_goals.get('weekly_sessions', 4)}次训练频率",
            f"目标周跑量{training_goals.get('weekly_distance_target', 30)}km",
            "建议加入1-2次长距离慢跑",
            "保持有氧配速{training_goals.get('aerobic_pace', '4:50')}的训练"
        ]
        
        health_reminders = [
            "注意跑后拉伸，特别是膝关节和踝关节",
            "如果感觉疲劳，可以适当增加休息日",
            "保持充足睡眠和营养补充"
        ]
        
        db.close()
        
        return {
            "week_summary": week_summary,
            "trend_analysis": trend_analysis,
            "next_week_suggestions": next_week_suggestions,
            "health_reminders": health_reminders,
            "stats": {
                "week_count": week_count,
                "week_distance": round(week_distance, 1),
                "week_avg_hr": round(week_avg_hr),
                "month_count": month_count,
                "month_distance": round(month_distance, 1)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
