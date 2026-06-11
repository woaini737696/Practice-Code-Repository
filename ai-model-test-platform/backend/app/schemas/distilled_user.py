from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatRecordItem(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class DistilledUserCreate(BaseModel):
    name: str
    chat_records: Optional[List[ChatRecordItem]] = []


class DistilledUserResponse(BaseModel):
    id: int
    name: str
    source_file: Optional[str]
    message_count: int
    status: int
    created_at: datetime

    class Config:
        from_attributes = True


class DistilledUserDetail(DistilledUserResponse):
    chat_records: List[ChatRecordItem] = []
