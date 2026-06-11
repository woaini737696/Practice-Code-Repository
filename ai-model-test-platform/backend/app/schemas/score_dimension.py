from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScoreDimensionCreate(BaseModel):
    name: str
    weight: float
    description: Optional[str] = None
    scoring_criteria: Optional[str] = None
    sort_order: Optional[int] = 0


class ScoreDimensionResponse(BaseModel):
    id: int
    name: str
    weight: float
    description: Optional[str]
    scoring_criteria: Optional[str]
    sort_order: int
    is_enabled: int
    created_at: datetime

    class Config:
        from_attributes = True
