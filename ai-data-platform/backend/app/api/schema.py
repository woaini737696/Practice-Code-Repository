from fastapi import APIRouter, HTTPException
from app.services.mysql_service import mysql_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/schema", tags=["数据目录"])


@router.get("")
async def get_schema():
    """
    获取数据库表结构
    """
    try:
        result = await mysql_service.get_schema()
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    except Exception as e:
        logger.error(f"获取表结构接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample/{table_name}")
async def get_sample_data(table_name: str, limit: int = 5):
    """
    获取表样本数据
    """
    try:
        result = await mysql_service.get_sample_data(table_name, limit)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    except Exception as e:
        logger.error(f"获取样本数据接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
