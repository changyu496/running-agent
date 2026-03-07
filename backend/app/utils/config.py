"""
配置文件读取工具
"""
import json
import os
import sys
from pathlib import Path

def _get_config_path():
    """打包后使用 Application Support，开发时使用项目根目录"""
    if getattr(sys, "frozen", False):
        from app.utils.paths import get_backend_root
        return Path(get_backend_root()) / "config.json"
    return Path(__file__).parent.parent.parent.parent / "config.json"

CONFIG_PATH = _get_config_path()

def _ensure_config_exists():
    """打包后首次运行：若 config 不存在，从示例或默认创建"""
    if CONFIG_PATH.exists():
        return
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 尝试从打包目录或项目根目录的 config.example.json 复制
    candidates = [
        CONFIG_PATH.parent / "config.example.json",
        Path(__file__).parent.parent.parent.parent / "config.example.json",
    ]
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        candidates.extend([
            exe_dir / "config.example.json",
            exe_dir / "_internal" / "config.example.json",
        ])
    for candidate in candidates:
        if candidate.exists():
            import shutil
            shutil.copy(candidate, CONFIG_PATH)
            return
    # 否则创建默认配置
    default = {
        "user_info": {"name": "", "gender": "male", "age": 30, "height": 175, "weight": 70,
                      "max_heart_rate": None, "resting_heart_rate": 60},
        "training_goals": {"aerobic_pace": "4'30\"", "weekly_distance_target": 30, "weekly_sessions": 4},
        "personal_bests": {"half_marathon": None, "marathon": None, "10k": None},
        "api_config": {"qwen_api_key": "", "qwen_api_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation", "backup_model": None},
        "app_settings": {"theme": "light", "auto_link_threshold": 30},
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(default, f, ensure_ascii=False, indent=2)

def load_config():
    """加载配置文件"""
    _ensure_config_exists()
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_user_info():
    """获取用户信息"""
    config = load_config()
    return config.get("user_info", {})

def get_api_config():
    """获取API配置（环境变量 QWEN_API_KEY 优先于 config.json）"""
    config = load_config()
    api_config = dict(config.get("api_config", {}))
    # 云端部署：环境变量优先
    env_key = os.environ.get("QWEN_API_KEY")
    if env_key:
        api_config["qwen_api_key"] = env_key
    return api_config

def get_training_goals():
    """获取训练目标"""
    config = load_config()
    return config.get("training_goals", {})

def get_personal_bests():
    """获取个人最佳成绩"""
    config = load_config()
    return config.get("personal_bests", {})
