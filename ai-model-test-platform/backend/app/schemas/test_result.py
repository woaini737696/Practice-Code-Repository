from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class TestResultResponse(BaseModel):
    id: int
    test_id: int
    model_id: int
    user_id: int
    conversation: List[Dict[str, Any]]
    scores: Optional[Dict[str, Any]]
    total_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
