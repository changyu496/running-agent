"""
跑步分数计算（参考 RQ Running Quotient / Jack Daniels VDOT）

RQ 即时跑力基于《丹尼爾博士跑步方程式》，由配速、心率、坡度与里程数分析得出。
核心采用 Daniels-Gilbert 公式计算 VDOT（伪最大摄氧量），再映射为 0-100 分数。

Daniels-Gilbert 公式：
VDOT = (−4.60 + 0.182258×V + 0.000104×V²) / (0.8 + 0.1894393×e^(-0.012778×T) + 0.2989558×e^(-0.1932605×T))
其中 V = 速度(m/min), T = 时间(min)
"""
import re
import math
from typing import Optional


def _parse_pace_to_sec_per_km(pace_str: str) -> Optional[float]:
    """解析配速为 秒/公里"""
    if not pace_str:
        return None
    s = str(pace_str).strip()
    m = re.match(r"(\d+)[\'′](\d+)[\"″]?", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.match(r"(\d+):(\d+)", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    try:
        return float(s) * 60
    except ValueError:
        return None


def _parse_duration_to_minutes(duration_str: str) -> Optional[float]:
    """解析时长为分钟，支持 1:07:13、67:13、67 等"""
    if not duration_str:
        return None
    s = str(duration_str).strip()
    parts = re.split(r"[:：]", s)
    if len(parts) == 3:  # H:MM:SS
        return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
    if len(parts) == 2:  # MM:SS
        return int(parts[0]) + int(parts[1]) / 60
    if len(parts) == 1:
        try:
            return float(parts[0])
        except ValueError:
            return None
    return None


def _daniels_gilbert_vdot(velocity_m_per_min: float, time_min: float) -> float:
    """
    Daniels-Gilbert 公式计算 VDOT
    V = 速度 m/min, T = 时间 min
    VDOT 典型范围 30-75
    """
    if velocity_m_per_min <= 0 or time_min <= 0:
        return 0
    V = velocity_m_per_min
    T = time_min
    num = -4.60 + 0.182258 * V + 0.000104 * (V ** 2)
    den = 0.8 + 0.1894393 * math.exp(-0.012778 * T) + 0.2989558 * math.exp(-0.1932605 * T)
    if den <= 0:
        return 0
    return num / den


def _vdot_to_score(vdot: float, avg_hr: Optional[int] = None, max_hr: Optional[int] = None) -> int:
    """
    将 VDOT 映射为 0-100 分数
    VDOT 30->约0, 50->约50, 65->约80, 75->约100
    可选：用心率效率微调（低心率+快配速=有氧能力强，略加分）
    """
    if vdot <= 0:
        return 0
    # 线性映射 VDOT 25-75 -> 0-100
    base = (vdot - 25) * (100 / 50)
    base = max(0, min(100, base))

    # 心率微调：需用户配置 max_hr，这里简化
    if avg_hr and max_hr and max_hr > 0:
        hr_pct = avg_hr / max_hr
        # 相同配速下心率越低，效率越好，略加分
        if hr_pct < 0.70 and vdot > 45:
            base = min(100, base + 3)
        elif hr_pct > 0.90:
            base = max(0, base - 3)

    return int(round(max(0, min(100, base))))


# AI 可能返回中文键名，建立映射
_CN_KEY_MAP = {
    "距离": "distance", "distance_km": "distance",
    "运动时间": "duration", "运动时长": "duration",
    "平均配速": "avg_pace", "最大配速": "avg_pace",
    "平均心率": "avg_heart_rate", "最大心率": "max_heart_rate",
    "平均步频": "avg_cadence", "最大步频": "avg_cadence",
}


def _extract_number(val) -> Optional[float]:
    """从 '14.00 km'、'124 bpm' 等字符串提取数字"""
    if val is None:
        return None
    s = str(val).strip()
    m = re.search(r"[\d.]+", s)
    if m:
        try:
            return float(m.group())
        except ValueError:
            return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _get_from_overview(d: dict, *key_groups) -> Optional[float]:
    """从 data_overview 取值，支持中英文键，支持带单位字符串"""
    for keys in key_groups:
        for k in keys:
            v = d.get(k)
            if v is not None and v != "":
                n = _extract_number(v)
                if n is not None:
                    return n
    return None


def _get_float(d: dict, *keys) -> Optional[float]:
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            n = _extract_number(v)
            if n is not None:
                return n
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
    return None


def _get_int(d: dict, *keys) -> Optional[int]:
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            n = _extract_number(v)
            if n is not None:
                return int(n)
            try:
                return int(float(v))
            except (ValueError, TypeError):
                pass
    return None


def _normalize_overview(d: dict) -> dict:
    """将 AI 返回的中文键名 data_overview 转为可解析格式"""
    if not d:
        return d
    out = dict(d)
    for cn, en in _CN_KEY_MAP.items():
        if cn in d and en not in out:
            out[en] = d[cn]
    return out


def _get_pace_str(d: dict) -> Optional[str]:
    """获取配速字符串，支持中英文键"""
    for k in ("avg_pace", "average_pace_min_per_km", "平均配速", "最大配速"):
        v = d.get(k)
        if v is not None and v != "":
            return str(v)
    return None


def _get_duration_str(d: dict) -> Optional[str]:
    """获取时长字符串"""
    for k in ("duration", "duration_hhmmss", "运动时间", "运动时长"):
        v = d.get(k)
        if v is not None and v != "":
            return str(v)
    return None


def _parse_duration_cn(s: str) -> Optional[float]:
    """解析中文时长如 1小时7分13秒"""
    if not s:
        return None
    s = str(s).strip()
    total = 0
    m = re.search(r"(\d+)\s*小时", s)
    if m:
        total += int(m.group(1)) * 60
    m = re.search(r"(\d+)\s*分", s)
    if m:
        total += int(m.group(1))
    m = re.search(r"(\d+)\s*秒", s)
    if m:
        total += int(m.group(1)) / 60
    if total > 0:
        return total
    return _parse_duration_to_minutes(s)


def compute_run_score(
    data_overview: dict,
    distance: Optional[float] = None,
    avg_pace: Optional[str] = None,
    avg_heart_rate: Optional[int] = None,
    max_heart_rate: Optional[int] = None,
) -> int:
    """
    计算跑步分数 0-100（参考 RQ 即时跑力 / Daniels VDOT）

    使用 Daniels-Gilbert 公式：根据配速、距离（推导时长）计算 VDOT，
    再映射为 0-100。若有心率可做微调。
    支持 AI 返回的中文键名（距离、平均配速、运动时间等）。
    """
    d = _normalize_overview(data_overview or {})
    dist = distance or _get_float(d, "distance", "distance_km", "距离")
    pace_str = avg_pace or _get_pace_str(d)
    duration_str = _get_duration_str(d)
    hr = avg_heart_rate or _get_int(d, "avg_heart_rate", "average_heart_rate_bpm", "平均心率")
    max_hr = max_heart_rate or _get_int(d, "max_heart_rate", "max_heart_rate_bpm", "最大心率")

    sec_per_km = _parse_pace_to_sec_per_km(str(pace_str)) if pace_str else None
    if not sec_per_km or sec_per_km <= 0:
        return 0

    # V = 速度 m/min = 1000m / (sec_per_km/60) min = 60000/sec_per_km
    velocity_m_per_min = 60000.0 / sec_per_km

    # T = 时间 min：优先用 duration，支持 1:07:13 或 1小时7分13秒
    time_min = None
    if duration_str:
        time_min = _parse_duration_cn(duration_str) or _parse_duration_to_minutes(duration_str)
    if time_min is None or time_min <= 0:
        if dist and dist > 0:
            pace_min_per_km = sec_per_km / 60
            time_min = dist * pace_min_per_km
        else:
            # 无距离时假设 5km 估算
            time_min = 5 * (sec_per_km / 60)

    # 限制 T 范围，公式在极短/极长时间可能不稳定
    time_min = max(2, min(180, time_min))

    vdot = _daniels_gilbert_vdot(velocity_m_per_min, time_min)
    return _vdot_to_score(vdot, hr, max_hr)


def compute_vdot_raw(
    data_overview: dict,
    distance: Optional[float] = None,
    avg_pace: Optional[str] = None,
) -> Optional[float]:
    """
    仅计算原始 VDOT 值（供调试或高级展示）
    """
    dist = distance or _get_float(data_overview, "distance", "distance_km")
    pace_str = avg_pace or data_overview.get("avg_pace") or data_overview.get("average_pace_min_per_km")
    duration_str = data_overview.get("duration") or data_overview.get("duration_hhmmss")

    sec = _parse_pace_to_sec_per_km(str(pace_str)) if pace_str else None
    if not sec or sec <= 0:
        return None
    V = 60000.0 / sec
    T = _parse_duration_to_minutes(duration_str) if duration_str else None
    if T is None and dist and dist > 0:
        T = dist * (sec / 60)
    if not T or T <= 0:
        T = 10  # 默认 10 分钟
    T = max(2, min(180, T))
    return round(_daniels_gilbert_vdot(V, T), 1)


def _infer_run_type(data_overview: dict, memo_text: str = "") -> str:
    """根据数据推断训练类型"""
    distance = _get_float(data_overview, "distance", "distance_km")
    pace_sec = None
    for key in ("avg_pace", "average_pace_min_per_km"):
        p = data_overview.get(key)
        if p:
            pace_sec = _parse_pace_to_sec_per_km(str(p))
            break
    avg_hr = _get_int(data_overview, "avg_heart_rate", "average_heart_rate_bpm")

    if not distance and not pace_sec:
        return "other"
    if distance and distance >= 20:
        return "long"
    if avg_hr and avg_hr < 125:
        return "recovery"
    if pace_sec and pace_sec > 360:
        return "recovery"
    if avg_hr and 150 <= avg_hr <= 165:
        return "pace"
    if distance and distance < 5 and avg_hr and avg_hr > 160:
        return "interval"
    return "aerobic"


def infer_run_type(data_overview: dict, memo_text: str = "") -> str:
    return _infer_run_type(data_overview, memo_text)


RUN_TYPE_LABELS = {
    "recovery": "恢复跑",
    "aerobic": "有氧跑",
    "long": "长距离",
    "pace": "节奏跑",
    "interval": "间歇跑",
    "other": "其他",
}
