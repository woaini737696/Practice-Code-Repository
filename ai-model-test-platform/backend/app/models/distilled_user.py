from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from app.database import Base


class DistilledUser(Base):
    __tablename__ = "distilled_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="用户名称")
    source_file = Column(String(255), comment="源文件名")
    chat_summary = Column(Text, comment="聊天摘要")
    message_count = Column(Integer, default=0, comment="消息数量")
    status = Column(Integer, default=1, comment="状态: 1-启用, 0-禁用")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
