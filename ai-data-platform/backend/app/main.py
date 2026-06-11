from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.services.mysql_service import mysql_service
from app.api import chat, query, schema

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("正在初始化数据库...")
    await init_db()

    logger.info("正在连接MySQL...")
    try:
        await mysql_service.connect()
    except Exception as e:
        logger.warning(f"MySQL连接失败（开发环境可忽略）: {e}")

    logger.info(f"{settings.APP_NAME} 启动成功!")
    yield

    # 关闭时
    logger.info("正在关闭MySQL连接...")
    await mysql_service.close()
    logger.info("应用已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI智能数据分析中台 - 你的智能数据助理",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(query.router)
app.include_router(schema.router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
