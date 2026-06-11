from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, func
from app.database import Base


class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模型名称")
    base_url = Column(String(255), nullable=False)
    api_key = Column(String(255), nullable=False)
    model_name = Column(String(100), nullable=False)
    temperature = Column(DECIMAL(3, 2), default=0.70)
    max_tokens = Column(Integer, default=2048)
    system_prompt = Column(Text)
    timeout = Column(Integer, default=30)
    is_enabled = Column(Integer, default=1, comment="状态: 1-启用, 0-禁用")
    created_at = Column(TIMESTAMP, server_default=func.now())
