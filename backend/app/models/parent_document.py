import json
from sqlalchemy import Column, String, Integer, Text
from app.core.config import Base


class ParentDocumentModel(Base):
    __tablename__ = "parent_documents"

    parent_id = Column(String(36), primary_key=True)
    filename = Column(String(512), nullable=False, index=True)
    title = Column(String(512), default='')
    title_hierarchy = Column(Text, default='[]')
    content = Column(Text, nullable=False)
    section_level = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    child_count = Column(Integer, default=0)
    created_at = Column(String(32))
    updated_at = Column(String(32))

    def get_hierarchy(self):
        try:
            return json.loads(self.title_hierarchy)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_hierarchy(self, hierarchy: list):
        self.title_hierarchy = json.dumps(hierarchy, ensure_ascii=False)
