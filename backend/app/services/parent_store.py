import json
import logging
from datetime import datetime
from typing import List, Optional
from app.core.config import SessionLocal
from app.models.parent_document import ParentDocumentModel
from .parent_document import ParentDocument

logger = logging.getLogger(__name__)


class ParentDocumentStore:

    def __init__(self):
        self._ensure_table()

    def _ensure_table(self):
        from app.core.config import engine, Base
        Base.metadata.create_all(bind=engine)

    def save_parents(self, parents: List[ParentDocument]) -> int:
        if not parents:
            return 0

        db = SessionLocal()
        try:
            filenames = list(set(p.filename for p in parents))
            for fname in filenames:
                db.query(ParentDocumentModel).filter(
                    ParentDocumentModel.filename == fname
                ).delete()

            now = datetime.utcnow().isoformat()
            count = 0
            for p in parents:
                model = ParentDocumentModel(
                    parent_id=p.parent_id,
                    filename=p.filename,
                    title=p.title,
                    title_hierarchy=json.dumps(p.title_hierarchy, ensure_ascii=False),
                    content=p.content,
                    section_level=p.section_level,
                    char_count=p.char_count,
                    child_count=len(p.child_chunk_ids),
                    created_at=now,
                    updated_at=now
                )
                db.add(model)
                count += 1

            db.commit()
            logger.info(f"父文档存储完成: {count} 条记录")
            return count

        except Exception as e:
            db.rollback()
            logger.error(f"父文档存储失败: {e}")
            raise
        finally:
            db.close()

    def get_parents_by_ids(self, parent_ids: List[str]) -> List[dict]:
        if not parent_ids:
            return []

        db = SessionLocal()
        try:
            results = db.query(ParentDocumentModel).filter(
                ParentDocumentModel.parent_id.in_(parent_ids)
            ).all()

            return [
                {
                    "parent_id": r.parent_id,
                    "filename": r.filename,
                    "title": r.title,
                    "title_hierarchy": r.get_hierarchy(),
                    "content": r.content,
                    "section_level": r.section_level,
                    "char_count": r.char_count
                }
                for r in results
            ]
        finally:
            db.close()

    def get_parents_by_filename(self, filename: str) -> List[dict]:
        db = SessionLocal()
        try:
            results = db.query(ParentDocumentModel).filter(
                ParentDocumentModel.filename == filename
            ).order_by(ParentDocumentModel.section_level).all()

            return [
                {
                    "parent_id": r.parent_id,
                    "title": r.title,
                    "content": r.content,
                    "char_count": r.char_count
                }
                for r in results
            ]
        finally:
            db.close()

    def delete_by_filename(self, filename: str) -> int:
        db = SessionLocal()
        try:
            count = db.query(ParentDocumentModel).filter(
                ParentDocumentModel.filename == filename
            ).delete()
            db.commit()
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"删除父文档失败: {e}")
            raise
        finally:
            db.close()

    def get_stats(self) -> dict:
        db = SessionLocal()
        try:
            total = db.query(ParentDocumentModel).count()
            total_chars = db.query(ParentDocumentModel.char_count).all()
            total_chars_sum = sum(c[0] for c in total_chars if c[0]) if total_chars else 0
            return {
                "total_parents": total,
                "total_chars": total_chars_sum,
                "approx_tokens": total_chars_sum // 2
            }
        finally:
            db.close()
