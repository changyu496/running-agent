"""
数据库模型定义
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from app.utils.paths import get_backend_root

# 数据库：云端用 DATABASE_URL（MySQL），本地用 SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    DB_PATH = None
else:
    DB_PATH = os.path.join(get_backend_root(), "database", "running_agent.db")
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Record(Base):
    """主记录表"""
    __tablename__ = "records"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    run_date = Column(String(10), nullable=True)  # YYYY-MM-DD 跑步日期，一天可多次
    run_type = Column(String(20), nullable=True)  # recovery/aerobic/long/pace/interval/other 恢复跑/有氧跑/长距离/节奏跑/间歇跑/其他
    run_score = Column(Integer, nullable=True)  # 0-100 跑步分数，参考 RQ
    record_type = Column(String(20), nullable=False)  # memo/video/both
    memo_text = Column(Text, nullable=True)
    coros_image_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    video_angle = Column(String(10), nullable=True)  # side/back
    analysis_result = Column(Text, nullable=True)  # JSON
    is_linked = Column(Boolean, default=False)
    linked_record_ids = Column(Text, nullable=True)  # JSON array
    
    # 关联关系
    coros_data = relationship("CorosData", back_populates="record", uselist=False)
    video_analysis = relationship("VideoAnalysis", back_populates="record", uselist=False)

class CorosData(Base):
    """高驰数据表（含 Stryd 功率计数据）"""
    __tablename__ = "coros_data"
    
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("records.id"), nullable=False)
    distance = Column(Float, nullable=True)  # km
    duration = Column(String(20), nullable=True)  # HH:MM:SS
    avg_pace = Column(String(20), nullable=True)  # MM'SS"
    avg_heart_rate = Column(Integer, nullable=True)  # bpm
    max_heart_rate = Column(Integer, nullable=True)
    avg_cadence = Column(Integer, nullable=True)  # spm
    avg_stride_length = Column(Float, nullable=True)  # cm
    avg_power = Column(Integer, nullable=True)  # W
    max_power = Column(Integer, nullable=True)  # W Stryd 最高功率
    form_power = Column(Integer, nullable=True)  # W Stryd 姿势功率
    form_power_ratio = Column(Integer, nullable=True)  # % Stryd 姿势功率比，理想 20-30
    avg_gct = Column(Integer, nullable=True)  # ms Stryd 触地时间
    vertical_oscillation = Column(Float, nullable=True)  # cm Stryd 垂直振幅
    calories = Column(Integer, nullable=True)
    elevation_gain = Column(Integer, nullable=True)  # m
    elevation_loss = Column(Integer, nullable=True)  # m
    
    record = relationship("Record", back_populates="coros_data")

class VideoAnalysis(Base):
    """视频分析数据表"""
    __tablename__ = "video_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("records.id"), nullable=False)
    video_angle = Column(String(10), nullable=False)  # side/back
    keypoints_data = Column(Text, nullable=True)  # JSON
    angles_data = Column(Text, nullable=True)  # JSON
    symmetry_data = Column(Text, nullable=True)  # JSON (仅背面)
    visualization_path = Column(String(500), nullable=True)
    overall_score = Column(Integer, nullable=True)  # 0-100
    analysis_text = Column(Text, nullable=True)
    
    record = relationship("Record", back_populates="video_analysis")

_db_inited = False

def _migrate_add_columns():
    """迁移：添加 run_date, run_type, run_score 列"""
    from sqlalchemy import text
    for col, col_type in [("run_date", "VARCHAR(10)"), ("run_type", "VARCHAR(20)"), ("run_score", "INTEGER")]:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE records ADD COLUMN {col} {col_type}"))
                conn.commit()
        except Exception:
            pass  # 列已存在则忽略


def _migrate_coros_stryd_columns():
    """迁移：添加 Stryd 相关列到 coros_data"""
    from sqlalchemy import text
    stryd_cols = [
        ("max_power", "INTEGER"),
        ("form_power", "INTEGER"),
        ("form_power_ratio", "INTEGER"),
        ("avg_gct", "INTEGER"),
        ("vertical_oscillation", "REAL"),
    ]
    for col, col_type in stryd_cols:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE coros_data ADD COLUMN {col} {col_type}"))
                conn.commit()
        except Exception:
            pass

def init_db():
    """初始化数据库"""
    global _db_inited
    if _db_inited:
        return
    _db_inited = True
    if DB_PATH:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _migrate_add_columns()
    _migrate_coros_stryd_columns()
    db_info = DATABASE_URL.split("@")[-1] if DATABASE_URL else DB_PATH
    print(f"数据库初始化完成: {db_info}")

if __name__ == "__main__":
    init_db()
