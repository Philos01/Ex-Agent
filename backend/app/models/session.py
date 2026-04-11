"""
Session database model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Session(BaseModel):
    """
    Chat session model
    """
    __tablename__ = "sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    session_name = Column(String(100), nullable=False, comment="会话名称")
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="是否活跃")
    last_message_preview = Column(Text, nullable=True, comment="最后一条消息预览")
    message_count = Column(Integer, default=0, nullable=False, comment="消息总数")
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Message.created_at.asc()"
    )
