from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.database import get_db
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 密码加密
import hashlib

def get_password_hash(password: str) -> str:
    # SHA256哈希后转hex，固定64字符，避免bcrypt 72字节限制
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT配置
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1天





def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username, User.is_active == 1).first()
    if user is None:
        raise credentials_exception
    return user


from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建新用户
    hashed_password = get_password_hash(data.password)
    db_user = User(username=data.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "注册成功", "user_id": db_user.id}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
    }


@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "created_at": current_user.created_at,
    }
