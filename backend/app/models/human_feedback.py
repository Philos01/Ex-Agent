from sqlalchemy import Column, Integer, String, Boolean, Text
from app.models.base import BaseModel


class HumanFeedback(BaseModel):
    __tablename__ = "human_feedbacks"

    session_id = Column(String, nullable=False, index=True)
    iteration = Column(Integer, default=0)
    feedback_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tool_name = Column(String, nullable=True)
    tool_parameters = Column(Text, nullable=True)
    is_applied = Column(Boolean, default=False)
