from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, func
from app.database import Base


class ScoreDimension(Base):
    __tablename__ = "score_dimensions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="维度名称")
    weight = Column(DECIMAL(5, 2), nullable=False, default=1.00)
    description = Column(Text, comment="维度描述")
    scoring_criteria = Column(Text, comment="评分标准说明")
    sort_order = Column(Integer, default=0, comment="排序")
    is_enabled = Column(Integer, default=1, comment="状态: 1-启用, 0-禁用")
    created_at = Column(TIMESTAMP, server_default=func.now())
