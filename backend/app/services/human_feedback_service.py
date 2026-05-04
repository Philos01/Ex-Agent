import json
import logging
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.core.config import get_complete_config

logger = logging.getLogger(__name__)

DB_FILENAME = "human_feedback.db"


class HumanFeedbackService:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            cfg = get_complete_config()
            data_dir = Path(cfg.get("data_dir", "data"))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / DB_FILENAME
        self._db_path = Path(db_path)
        self._lock = threading.RLock()
        self._queues: Dict[str, deque] = defaultdict(deque)
        self._conn = None
        self._init_db()

    def _get_conn(self):
        if self._conn is None:
            import sqlite3
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS human_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    iteration INTEGER DEFAULT 0,
                    feedback_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_name TEXT,
                    tool_parameters TEXT,
                    is_applied BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_feedback_session ON human_feedback(session_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_type ON human_feedback(feedback_type);
                CREATE INDEX IF NOT EXISTS idx_feedback_applied ON human_feedback(is_applied);
            """)
            conn.commit()

    def submit_feedback(
        self,
        session_id: str,
        feedback_type: str,
        content: str,
        tool_name: Optional[str] = None,
        tool_parameters: Optional[Dict[str, Any]] = None,
        iteration: int = 0,
    ) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            params_json = json.dumps(tool_parameters, ensure_ascii=False) if tool_parameters else None
            cursor = conn.execute(
                """INSERT INTO human_feedback (session_id, iteration, feedback_type, content, tool_name, tool_parameters)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, iteration, feedback_type, content, tool_name, params_json),
            )
            conn.commit()
            feedback_id = cursor.lastrowid
            feedback_record = {
                "id": feedback_id,
                "session_id": session_id,
                "iteration": iteration,
                "feedback_type": feedback_type,
                "content": content,
                "tool_name": tool_name,
                "tool_parameters": tool_parameters,
                "is_applied": False,
            }
            self._queues[session_id].append(feedback_record)
            logger.info("[HumanFeedbackService] Feedback %d submitted for session %s, type=%s", feedback_id, session_id, feedback_type)
            return feedback_record

    def get_pending_feedback(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            queue = self._queues.get(session_id)
            if queue:
                for i, fb in enumerate(queue):
                    if not fb.get("is_applied", False):
                        return fb
            return None

    def get_all_pending_feedback(self, session_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            queue = self._queues.get(session_id, deque())
            return [fb for fb in queue if not fb.get("is_applied", False)]

    def mark_feedback_applied(self, feedback_id: int, session_id: str):
        with self._lock:
            conn = self._get_conn()
            conn.execute("UPDATE human_feedback SET is_applied = TRUE WHERE id = ?", (feedback_id,))
            conn.commit()
            queue = self._queues.get(session_id, deque())
            for fb in queue:
                if fb.get("id") == feedback_id:
                    fb["is_applied"] = True
                    break
            logger.info("[HumanFeedbackService] Feedback %d marked as applied", feedback_id)

    def get_feedback_history(self, session_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT * FROM human_feedback WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
            results = []
            for row in rows:
                record = dict(row)
                if record.get("tool_parameters"):
                    try:
                        record["tool_parameters"] = json.loads(record["tool_parameters"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                results.append(record)
            return results

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            total = conn.execute("SELECT COUNT(*) as cnt FROM human_feedback").fetchone()["cnt"]
            applied = conn.execute("SELECT COUNT(*) as cnt FROM human_feedback WHERE is_applied = TRUE").fetchone()["cnt"]
            type_rows = conn.execute(
                "SELECT feedback_type, COUNT(*) as cnt FROM human_feedback GROUP BY feedback_type"
            ).fetchall()
            by_type = {row["feedback_type"]: row["cnt"] for row in type_rows}
            session_rows = conn.execute(
                "SELECT session_id, COUNT(*) as cnt FROM human_feedback GROUP BY session_id"
            ).fetchall()
            by_session = {row["session_id"]: row["cnt"] for row in session_rows}
            return {
                "total": total,
                "applied": applied,
                "application_rate": round(applied / total, 2) if total > 0 else 0.0,
                "by_type": by_type,
                "by_session": by_session,
            }

    def clear_session_queue(self, session_id: str):
        with self._lock:
            if session_id in self._queues:
                self._queues[session_id].clear()

    def close(self):
        with self._lock:
            if self._conn:
                self._conn.commit()
                self._conn.close()
                self._conn = None


_feedback_service: Optional[HumanFeedbackService] = None


def get_feedback_service() -> HumanFeedbackService:
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = HumanFeedbackService()
    return _feedback_service
