from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.agents.data_analyst import agent
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["对话"])


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    type: str  # "data" | "text"
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None
    analysis: str
    suggestions: Optional[List[str]] = []
    error: Optional[str] = None


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    AI对话分析接口
    """
    try:
        # 转换历史记录格式
        history = None
        if request.history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ]

        # 调用Agent
        result = await agent.chat(
            message=request.message,
            history=history
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"对话接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
