from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP, func
from app.database import Base


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="测试名称")
    status = Column(String(20), default="pending", comment="状态: pending/running/scoring/completed/failed/cancelled")
    progress = Column(Integer, default=0, comment="进度百分比")
    user_ids = Column(JSON, nullable=False, comment="参与测试的用户ID列表")
    model_ids = Column(JSON, nullable=False, comment="参与测试的模型ID列表")
    config = Column(JSON, comment="测试配置")
    created_by = Column(Integer, comment="创建人")
    created_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)
