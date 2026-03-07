"""
跑步Agent - 后端主程序
"""
import os
import sys

# 加载 .env（云端部署、本地开发）
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.expanduser("~"), ".matplotlib"))

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# CORS：从环境变量读取，默认允许本地开发
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,file://,null")
CORS_ORIGINS = [x.strip() for x in _cors_origins.split(",")] if _cors_origins != "*" else ["*"]

# 无需认证的路径
AUTH_SKIP_PATHS = {"/", "/api/health", "/api/auth/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    """API 认证：/api/* 除白名单外需 JWT。文件接口支持 query 传 token（img src 无法带 header）"""
    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if path in AUTH_SKIP_PATHS or not path.startswith("/api/"):
            return await call_next(request)
        token = None
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
        elif path.startswith("/api/files") and request.query_params.get("token"):
            token = request.query_params.get("token")
        if not token:
            return JSONResponse({"detail": "未提供认证信息"}, status_code=401)
        from app.utils.auth import decode_token
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            return JSONResponse({"detail": "认证无效或已过期"}, status_code=401)
        request.state.username = payload["sub"]
        return await call_next(request)


app = FastAPI(title="步知 API", version="1.0.0")
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "步知 API", "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

def _ph():
    r = APIRouter()
    r.router = r
    return r

def _ensure_upload_dirs():
    """确保上传目录存在（Docker 启动时）"""
    from app.utils.paths import get_project_root
    for d in ["uploads/videos", "uploads/images", "uploads/visualizations"]:
        p = os.path.join(get_project_root(), d)
        os.makedirs(p, exist_ok=True)

def _mount_routers():
    _ensure_upload_dirs()
    try:
        from app.models.database import init_db
        init_db()
    except Exception as e:
        logging.warning(f"init_db: {e}")

    # 认证（无依赖，最先挂载）
    try:
        from app.api import auth
        app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
    except Exception as e:
        logging.warning(f"加载 auth 失败: {e}")

    # 逐个加载，任一失败不影响其他
    mods = [
        ("files", "app.api.files", "/api/files", "文件服务"),
        ("records", "app.api.records", "/api/records", "历史记录"),
        ("stats", "app.api.stats", "/api/stats", "数据统计"),
        ("memo", "app.api.memo", "/api/memo", "备忘录分析"),
        ("guidance", "app.api.guidance", "/api/guidance", "智能指导"),
    ]
    for name, mod_path, prefix, tag in mods:
        try:
            mod = __import__(mod_path, fromlist=["router"])
            r = getattr(mod, "router", mod)
            app.include_router(r, prefix=prefix, tags=[tag])
        except Exception as e:
            logging.warning(f"加载 {name} 失败: {e}，使用占位")
            app.include_router(_ph(), prefix=prefix, tags=[tag])

    # video 含 mediapipe/matplotlib，可能较慢或失败
    try:
        from app.api import video
        app.include_router(getattr(video, "router", video), prefix="/api/video", tags=["视频分析"])
    except Exception as e:
        logging.warning(f"加载 video 失败: {e}，视频分析暂不可用")
        app.include_router(_ph(), prefix="/api/video", tags=["视频分析"])

try:
    _mount_routers()
except Exception as e:
    logging.warning(f"挂载路由失败: {e}，仅保留 /api/health")

if __name__ == "__main__":
    import uvicorn
    from app.utils.paths import get_project_root
    for d in ["uploads/videos", "uploads/images", "uploads/visualizations"]:
        p = os.path.join(get_project_root(), d)
        os.makedirs(p, exist_ok=True)
    # 打包后直接传 app 对象，避免 uvicorn 再次 import main 导致异常
    reload = not getattr(sys, "frozen", False)
    if getattr(sys, "frozen", False):
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload)
