"""
User database model
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    """
    User model for authentication and authorization
    """
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    password_hash = Column(String(128), nullable=False, comment="密码哈希值")
    role = Column(String(20), default="user", nullable=False, index=True, comment="用户角色: user/admin")
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="是否激活")
    
    # Relationships
    sessions = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    messages = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    documents = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
