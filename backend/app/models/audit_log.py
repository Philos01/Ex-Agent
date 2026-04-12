"""
Audit log database model for tracking configuration changes
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AuditLog(BaseModel):
    """
    Audit log model for tracking system changes
    """
    __tablename__ = "audit_logs"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="操作用户ID")
    action = Column(String(100), nullable=False, index=True, comment="操作类型")
    resource_type = Column(String(50), nullable=True, comment="资源类型")
    resource_id = Column(String(100), nullable=True, comment="资源ID")
    old_value = Column(Text, nullable=True, comment="变更前值")
    new_value = Column(Text, nullable=True, comment="变更后值")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(255), nullable=True, comment="User Agent")
    
    # Relationships
    user = relationship("User")
