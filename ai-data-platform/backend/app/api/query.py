from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.mysql_service import mysql_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["查询"])


class QueryRequest(BaseModel):
    sql: str
    params: Optional[tuple] = None


class QueryResponse(BaseModel):
    success: bool
    data: Optional[list] = None
    columns: Optional[list] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None
    sql: Optional[str] = None
    error: Optional[str] = None


@router.post("", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    直接执行SQL查询（SQL实验室用）
    """
    try:
        result = await mysql_service.execute_query(
            sql=request.sql,
            params=request.params
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"查询接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
