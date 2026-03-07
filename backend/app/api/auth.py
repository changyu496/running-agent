"""
认证 API：登录
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.models.database import SessionLocal, User
from app.utils.auth import verify_password, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """登录，返回 JWT"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == req.username).first()
        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        token = create_access_token(req.username)
        return LoginResponse(access_token=token, username=req.username)
    finally:
        db.close()
