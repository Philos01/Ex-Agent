"""
Role-Permission association model
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import BaseModel


class RolePermission(BaseModel):
    """
    Association model for role-permission mapping
    """
    __tablename__ = "role_permissions"
    
    role = Column(String(20), nullable=False, index=True, comment="角色名称")
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False, index=True, comment="权限ID")
