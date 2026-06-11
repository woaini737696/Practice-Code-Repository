from sqlalchemy import Column, Integer, String, Text, DateTime, TIMESTAMP, func, ForeignKey
from app.database import Base


class ChatRecord(Base):
    __tablename__ = "chat_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("distilled_users.id"), nullable=False)
    role = Column(String(20), nullable=False, comment="角色: user/assistant")
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime)
    created_at = Column(TIMESTAMP, server_default=func.now())
