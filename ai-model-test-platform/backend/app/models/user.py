from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
