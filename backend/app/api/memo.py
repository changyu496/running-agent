"""
备忘录分析API
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import shutil
from datetime import datetime
from app.services.qwen_service import analyze_coros_image
from app.services.run_score import compute_run_score, infer_run_type, RUN_TYPE_LABELS
from app.models.database import SessionLocal, Record, CorosData, init_db
import json

router = APIRouter()

# 不再在各 api 模块重复调用，由 main.py 统一初始化
# init_db()

from app.utils.paths import get_project_root
from app.utils.storage import is_oss, save_file, get_local_path, to_storage_key
import tempfile

UPLOAD_DIR = os.path.join(get_project_root(), "uploads", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class MemoAnalysisRequest(BaseModel):
    memo_text: Optional[str] = ""
    image_path: str

class MemoAnalysisResponse(BaseModel):
    success: bool
    data_overview: dict
    performance_evaluation: dict
    improvement_suggestions: list
    record_id: Optional[int] = None
    image_path: Optional[str] = None
    run_score: Optional[int] = None  # 预览分数，由 data_overview 计算

@router.post("/analyze", response_model=MemoAnalysisResponse)
async def analyze_memo(
    memo_text: str = Form(""),
    image: UploadFile = File(...)
):
    """
    分析备忘录和高驰截图
    """
    try:
        # 保存上传的图片（本地或 OSS）
        fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.filename}"
        key = f"uploads/images/{fname}"
        image.file.seek(0)
        save_file(image.file, key)
        
        # Qwen 需要本地路径，OSS 时下载到临时文件
        img_path = get_local_path(key)
        try:
            max_retries = 2
            analysis_result = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    analysis_result = analyze_coros_image(img_path, memo_text)
                    break
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise HTTPException(
                            status_code=500, 
                            detail=f"分析失败（已重试{max_retries}次）: {str(last_error)}"
                        )
        finally:
            if is_oss() and img_path.startswith(tempfile.gettempdir()):
                try:
                    os.unlink(img_path)
                except Exception:
                    pass
        
        # 提取数据概览（处理不同格式的响应）
        data_overview = analysis_result.get("data_overview", {})
        if not data_overview and "raw_text" in analysis_result:
            # 如果没有结构化数据，尝试从原始文本中提取
            data_overview = {}
        
        performance_evaluation = analysis_result.get("performance_evaluation", {})
        if isinstance(performance_evaluation, str):
            performance_evaluation = {"text": performance_evaluation}
        
        improvement_suggestions = analysis_result.get("improvement_suggestions", [])
        if isinstance(improvement_suggestions, str):
            improvement_suggestions = [improvement_suggestions]
        
        run_score_preview = compute_run_score(data_overview) if data_overview else None
        
        return MemoAnalysisResponse(
            success=True,
            data_overview=data_overview,
            performance_evaluation=performance_evaluation,
            improvement_suggestions=improvement_suggestions,
            record_id=None,
            image_path=key,
            run_score=run_score_preview,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()  # 在终端输出完整堆栈，便于排查
        err_msg = str(e)
        if "API Key" in err_msg or "未配置" in err_msg:
            err_msg = "Qwen API Key 未配置或无效，请在 config.json 中设置 api_config.qwen_api_key"
        elif "InvalidApiKey" in err_msg or "401" in err_msg:
            err_msg = "Qwen API Key 无效或已过期，请检查 config.json"
        elif "RateLimit" in err_msg or "429" in err_msg:
            err_msg = "Qwen API 调用频率超限，请稍后再试"
        raise HTTPException(status_code=500, detail=err_msg)

@router.post("/save")
async def save_memo_record(
    memo_text: str = Form(""),
    image_path: str = Form(...),
    analysis_result: str = Form(...),  # JSON字符串
    run_date: Optional[str] = Form(None),  # YYYY-MM-DD
    run_type: Optional[str] = Form(None),  # recovery/aerobic/long/pace/interval/other
):
    """
    保存备忘录分析记录
    """
    try:
        db = SessionLocal()
        
        # 解析分析结果
        if isinstance(analysis_result, str):
            try:
                analysis = json.loads(analysis_result)
            except:
                analysis = {"raw_text": analysis_result}
        else:
            analysis = analysis_result
        
        data_overview = analysis.get("data_overview", {})
        now = datetime.now()
        run_date_val = run_date or now.strftime("%Y-%m-%d")
        run_type_val = run_type or infer_run_type(data_overview, memo_text)
        run_score_val = compute_run_score(data_overview)

        # 创建记录（保存解析后的 analysis 为 JSON，确保结构完整）
        record = Record(
            created_at=now,
            run_date=run_date_val,
            run_type=run_type_val,
            run_score=run_score_val,
            record_type="memo",
            memo_text=memo_text,
            coros_image_path=image_path,
            analysis_result=json.dumps(analysis, ensure_ascii=False)
        )
        db.add(record)
        db.flush()  # 分配 id，避免 commit 后 expire 导致 refresh 失败
        record_id = record.id

        # 创建高驰数据
        if data_overview and isinstance(data_overview, dict):
            def safe_float(value):
                try:
                    return float(value) if value else None
                except:
                    return None
            def safe_int(value):
                try:
                    return int(value) if value else None
                except:
                    return None
            def get_first(*keys, default=None):
                for k in keys:
                    v = data_overview.get(k)
                    if v is not None and v != "":
                        return v
                return default
            def to_num(val):
                if val is None: return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    import re
                    m = re.search(r"[\d.]+", str(val))
                    return float(m.group()) if m else None
            def to_int(val):
                n = to_num(val)
                return int(n) if n is not None else None
            dist = to_num(get_first("distance", "distance_km", "距离"))
            pace = str(get_first("avg_pace", "average_pace_min_per_km", "平均配速") or "")
            coros_data = CorosData(
                record_id=record_id,
                distance=dist,
                duration=str(get_first("duration", "duration_hhmmss", "运动时间", "运动时长") or ""),
                avg_pace=pace or None,
                avg_heart_rate=to_int(get_first("avg_heart_rate", "average_heart_rate_bpm", "平均心率")),
                max_heart_rate=to_int(get_first("max_heart_rate", "max_heart_rate_bpm", "最大心率")),
                avg_cadence=to_int(get_first("avg_cadence", "average_step_frequency_spd", "平均步频")),
                avg_stride_length=to_num(get_first("avg_stride_length", "average_stride_length_cm", "平均步幅")),
                avg_power=to_int(get_first("avg_power", "average_power_w", "平均功率")),
                max_power=to_int(get_first("max_power", "max_power_w", "最高功率", "最大功率")),
                form_power=to_int(get_first("form_power", "form_power_w", "姿势功率")),
                form_power_ratio=to_int(get_first("form_power_ratio", "姿势功率比")),
                avg_gct=to_int(get_first("avg_gct", "gct", "触地时间")),
                vertical_oscillation=to_num(get_first("vertical_oscillation_cm", "vertical_oscillation", "垂直振幅")),
                calories=to_int(get_first("calories"))
            )
            db.add(coros_data)

        db.commit()
        db.close()

        return {"success": True, "record_id": record_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
