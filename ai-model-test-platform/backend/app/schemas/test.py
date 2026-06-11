from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class TestCreate(BaseModel):
    name: str
    user_ids: List[int]
    model_ids: List[int]
    config: Optional[Dict[str, Any]] = None


class TestResponse(BaseModel):
    id: int
    name: str
    status: str
    progress: int
    user_ids: List[int]
    model_ids: List[int]
    config: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TestDetail(TestResponse):
    results: List[Dict[str, Any]] = []
