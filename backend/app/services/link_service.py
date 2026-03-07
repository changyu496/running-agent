"""
记录关联服务
"""
from datetime import datetime, timedelta
from app.models.database import SessionLocal, Record, CorosData
import json

def should_link_records(record1, record2, threshold_minutes=30):
    """
    判断两条记录是否应该关联（同一次跑步）
    
    Args:
        record1: 记录1
        record2: 记录2
        threshold_minutes: 时间间隔阈值（分钟）
    
    Returns:
        bool: 是否应该关联
    """
    # 时间间隔检查
    time_diff = abs((record1.created_at - record2.created_at).total_seconds() / 60)
    if time_diff > threshold_minutes:
        return False
    
    # 获取高驰数据
    db = SessionLocal()
    coros1 = db.query(CorosData).filter(CorosData.record_id == record1.id).first()
    coros2 = db.query(CorosData).filter(CorosData.record_id == record2.id).first()
    
    if not coros1 or not coros2:
        db.close()
        return False
    
    # 距离相似度检查（允许10%误差）
    if coros1.distance and coros2.distance:
        distance_diff = abs(coros1.distance - coros2.distance) / max(coros1.distance, coros2.distance)
        if distance_diff > 0.1:
            db.close()
            return False
    
    # 配速相似度检查（简化处理）
    # 实际应该解析配速字符串并比较
    
    db.close()
    return True

def auto_link_records():
    """
    自动关联记录
    """
    db = SessionLocal()
    
    # 获取所有未关联的记录
    unlinked_records = db.query(Record).filter(
        Record.is_linked == False
    ).order_by(Record.created_at.desc()).all()
    
    linked_groups = []
    
    for record in unlinked_records:
        # 检查是否已经属于某个组
        already_linked = False
        for group in linked_groups:
            if record.id in group:
                already_linked = True
                break
        
        if already_linked:
            continue
        
        # 创建新组
        current_group = [record.id]
        
        # 查找应该关联的其他记录
        for other_record in unlinked_records:
            if other_record.id == record.id:
                continue
            
            if should_link_records(record, other_record):
                current_group.append(other_record.id)
        
        if len(current_group) > 1:
            linked_groups.append(current_group)
    
    # 更新数据库
    for group in linked_groups:
        for record_id in group:
            record = db.query(Record).filter(Record.id == record_id).first()
            if record:
                record.is_linked = True
                record.linked_record_ids = json.dumps(group)
    
    db.commit()
    db.close()
    
    return linked_groups
