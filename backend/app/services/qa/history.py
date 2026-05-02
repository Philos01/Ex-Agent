"""
Conversation history management — filtered retrieval and appending.
"""
import logging
from typing import List
from app.core.config import get_complete_config

logger = logging.getLogger(__name__)


def get_filtered_history(session_id: str = "default") -> List[dict]:
    cfg = get_complete_config()
    context_config = cfg.get("context_management", {})

    if not context_config.get("enabled", True):
        return []

    try:
        from app.services.context_manager import get_context_manager

        max_history = context_config.get("max_history_rounds", 5)
        exclude_errors = context_config.get("exclude_error_messages", True)
        exclude_questionable = context_config.get("exclude_questionable_messages", False)

        context_mgr = get_context_manager(session_id, max_history=max_history)
        filtered_history = context_mgr.get_filtered_history(
            exclude_errors=exclude_errors,
            exclude_questionable=exclude_questionable,
        )

        logger.debug("Fetched %d filtered history messages", len(filtered_history))
        return filtered_history

    except Exception as e:
        logger.error("Failed to get filtered history: %s", e, exc_info=True)
        return []


def add_to_history(role: str, content: str, session_id: str = "default"):
    cfg = get_complete_config()
    context_config = cfg.get("context_management", {})

    if not context_config.get("enabled", True):
        return

    try:
        from app.services.context_manager import get_context_manager

        max_history = context_config.get("max_history_rounds", 5)
        context_mgr = get_context_manager(session_id, max_history=max_history)
        context_mgr.add_message(role, content)

        logger.debug("Added %s message to history", role)
    except Exception as e:
        logger.error("Failed to add to history: %s", e, exc_info=True)
