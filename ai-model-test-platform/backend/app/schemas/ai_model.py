from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AIModelCreate(BaseModel):
    name: str
    base_url: str
    api_key: str
    model_name: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    system_prompt: Optional[str] = None
    timeout: Optional[int] = 30


class AIModelResponse(BaseModel):
    id: int
    name: str
    base_url: str
    model_name: str
    temperature: float
    max_tokens: int
    system_prompt: Optional[str]
    timeout: int
    is_enabled: int
    created_at: datetime

    class Config:
        from_attributes = True
