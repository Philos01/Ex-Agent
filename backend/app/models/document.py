"""
Document database model
"""
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Document(BaseModel):
    """
    Uploaded document model
    """
    __tablename__ = "documents"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    filename = Column(String(255), nullable=False, index=True, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    file_type = Column(String(50), nullable=False, comment="文件类型")
    
    # Relationships
    user = relationship("User", back_populates="documents")
