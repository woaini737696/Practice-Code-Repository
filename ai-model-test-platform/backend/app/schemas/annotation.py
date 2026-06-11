from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnnotationCreate(BaseModel):
    result_id: int
    dimension_id: int
    ai_score: Optional[float] = None
    human_score: Optional[float] = None
    comment: Optional[str] = None


class AnnotationResponse(BaseModel):
    id: int
    result_id: int
    dimension_id: int
    ai_score: Optional[float]
    human_score: Optional[float]
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
