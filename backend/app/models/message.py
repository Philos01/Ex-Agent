"""
Message database model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Message(BaseModel):
    """
    Chat message model
    """
    __tablename__ = "messages"
    
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True, comment="会话ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    role = Column(String(20), nullable=False, index=True, comment="角色: user/assistant/system")
    content = Column(Text, nullable=False, comment="消息内容")
    sources = Column(JSON, nullable=True, comment="引用来源(JSON格式，支持列表或字典)")
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    user = relationship("User", back_populates="messages")
