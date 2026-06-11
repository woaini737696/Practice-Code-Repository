from sqlalchemy import Column, Integer, JSON, DECIMAL, TIMESTAMP, func, ForeignKey
from app.database import Base


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("distilled_users.id"), nullable=False)
    conversation = Column(JSON, nullable=False, comment="完整对话记录")
    scores = Column(JSON, comment="各维度评分")
    total_score = Column(DECIMAL(5, 2), comment="总分")
    created_at = Column(TIMESTAMP, server_default=func.now())
