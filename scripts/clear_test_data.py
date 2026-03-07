#!/usr/bin/env python3
"""
清理全部记录：删除所有跑步记录、高驰数据、视频分析
用法：cd backend && python ../scripts/clear_test_data.py
（需使用已安装项目依赖的 Python 环境）
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.models.database import SessionLocal, Record, CorosData, VideoAnalysis

def main():
    db = SessionLocal()
    try:
        n_coros = db.query(CorosData).delete()
        n_video = db.query(VideoAnalysis).delete()
        n_records = db.query(Record).delete()
        db.commit()
        print(f"已删除: {n_records} 条记录, {n_coros} 条高驰数据, {n_video} 条视频分析")
        print("全部记录已清理完成")
    except Exception as e:
        db.rollback()
        print(f"清理失败: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
