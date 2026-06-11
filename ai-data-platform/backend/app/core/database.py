from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from app.core.config import settings
import os

# SQLite 异步引擎 (存储平台数据: 对话、配置、监控规则等)
os.makedirs(os.path.dirname(settings.SQLITE_PATH), exist_ok=True)
sqlite_async_url = f"sqlite+aiosqlite:///{settings.SQLITE_PATH}"

sqlite_engine = create_async_engine(
    sqlite_async_url,
    echo=settings.DEBUG,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    sqlite_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
