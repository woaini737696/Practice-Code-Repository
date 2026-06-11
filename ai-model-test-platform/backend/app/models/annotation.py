from sqlalchemy import Column, Integer, Text, DECIMAL, TIMESTAMP, func, ForeignKey
from app.database import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)
    dimension_id = Column(Integer, ForeignKey("score_dimensions.id"), nullable=False)
    ai_score = Column(DECIMAL(5, 2), comment="AI评分")
    human_score = Column(DECIMAL(5, 2), comment="人工修正评分")
    comment = Column(Text, comment="标注意见")
    annotated_by = Column(Integer, comment="标注人")
    created_at = Column(TIMESTAMP, server_default=func.now())
