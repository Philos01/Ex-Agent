"""
Permission database model
"""
from sqlalchemy import Column, Integer, String, Text
from app.models.base import BaseModel


class Permission(BaseModel):
    """
    Permission model for role-based access control
    """
    __tablename__ = "permissions"
    
    name = Column(String(50), unique=True, nullable=False, comment="权限名称")
    description = Column(Text, nullable=True, comment="权限描述")
