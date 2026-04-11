"""
Base model with common fields
"""
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.core.config import Base


class BaseModel(Base):
    """
    Base model with version ID and timestamps
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, default=0, nullable=False, comment="乐观锁版本号")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
