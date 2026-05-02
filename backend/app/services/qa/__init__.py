"""
QA service package — question-answering with RAG, skill execution, and ReAct modes.

Public API (backward-compatible with the old qa.py module):
- answer_question      — synchronous non-streaming QA
- stream_answer        — main streaming QA entry point
- _retrieve_documents  — document retrieval (used by routes.py)
- _format_conversation_history — conversation formatting (used by routes.py)
- _get_openai_client   — legacy LLM client factory (used by tests)
- regularize_output    — output post-processing
- _build_knowledge_base_overview — KB metadata overview
"""

from app.services.qa.utils import (
    format_conversation_history as _format_conversation_history,
    regularize_output,
    get_client_for_provider as _get_client_for_provider,
    get_openai_client as _get_openai_client,
)
from app.services.qa.kb_overview import (
    build_knowledge_base_overview as _build_knowledge_base_overview,
)
from app.services.qa.retrieval import (
    retrieve_documents as _retrieve_documents,
)
from app.services.qa.history import (
    get_filtered_history as _get_filtered_history,
    add_to_history as _add_to_history,
)
from app.services.qa.sync_answer import answer_question
from app.services.qa.stream_answer import stream_answer
from app.services.qa.react_stream import stream_answer_react as _stream_answer_react

__all__ = [
    "answer_question",
    "stream_answer",
    "_stream_answer_react",
    "_retrieve_documents",
    "_format_conversation_history",
    "_get_openai_client",
    "_get_client_for_provider",
    "regularize_output",
    "_build_knowledge_base_overview",
    "_get_filtered_history",
    "_add_to_history",
]
