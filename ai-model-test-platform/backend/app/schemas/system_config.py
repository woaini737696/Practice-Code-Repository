from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemConfigCreate(BaseModel):
    config_key: str
    config_value: Optional[str] = None
    description: Optional[str] = None


class SystemConfigResponse(BaseModel):
    id: int
    config_key: str
    config_value: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
