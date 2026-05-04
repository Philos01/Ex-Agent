"""
ReAct-mode streaming QA — delegates to the ReAct agent loop.
"""
import logging
from typing import List

from app.services.qa.utils import format_conversation_history
from app.services.qa.retrieval import retrieve_documents

logger = logging.getLogger(__name__)


def stream_answer_react(
    question: str,
    provider: str = "openai",
    messages: List[dict] = None,
    max_tokens: int = None,
    enable_thinking: bool = False,
):
    """
    ReAct-mode streaming answer generator.

    Yields:
        ReAct event dicts with types: react_thought, react_thought_chunk,
        react_reasoning_chunk, react_action, react_observation,
        react_final_answer, react_steps, react_error, state
    """
    from app.agents import AgentLoop

    logger.debug(
        "[react_stream] Starting: question=%s, provider=%s, thinking=%s",
        question[:50], provider, enable_thinking,
    )

    conversation_history = format_conversation_history(messages)

    docs = retrieve_documents(question, provider, top_k=5)
    retrieved_context = "\n\n".join([d.get("text", "") for d in docs])
    logger.debug("[react_stream] Retrieved context length: %s", len(retrieved_context))

    agent = AgentLoop(
        provider=provider,
        max_tokens=max_tokens or 4096,
        enable_thinking=enable_thinking,
    )

    event_count = 0
    for event_dict in agent.stream_run(
        question,
        conversation_history=conversation_history,
        retrieved_context=retrieved_context,
    ):
        event_count += 1
        event_type = event_dict.get("type")

        if event_type == "thought":
            yield {"type": "react_thought", "content": event_dict.get("content")}
        elif event_type == "thought_chunk":
            yield {"type": "react_thought_chunk", "content": event_dict.get("content")}
        elif event_type == "reasoning_chunk":
            yield {"type": "react_reasoning_chunk", "content": event_dict.get("content")}
        elif event_type == "action":
            action_data = event_dict.get("content", {})
            action_name = action_data.get("name") if isinstance(action_data, dict) else event_dict.get("name")
            action_input = action_data.get("input") if isinstance(action_data, dict) else event_dict.get("input")
            logger.debug("[react_stream] Action: %s, input: %s", action_name, action_input)
            yield {"type": "react_action", "name": action_name, "input": action_input}
        elif event_type == "observation":
            yield {"type": "react_observation", "content": event_dict.get("content")}
        elif event_type == "final_answer":
            logger.debug("[react_stream] Final answer length: %s", len(str(event_dict.get("content"))))
            yield {"type": "react_final_answer", "content": event_dict.get("content")}
        elif event_type == "done":
            steps = event_dict.get("metadata", {}).get("steps", event_dict.get("steps", []))
            yield {"type": "react_steps", "steps": steps}
            yield {"type": "state", "phase": "done", "message": "生成完毕", "progress": 100}
        elif event_type == "error":
            error_msg = event_dict.get("content") or event_dict.get("message")
            yield {"type": "react_error", "message": error_msg}
        elif event_type == "thinking":
            iteration = event_dict.get("iteration", 1)
            total = event_dict.get("total", -1)
            progress_msg = f"思考中 (第{iteration}步)" if total == -1 else f"思考中 (第{iteration}/{total}步)"
            progress = min(int(iteration / max(total, 1) * 75), 90) if total > 0 else min(iteration * 10, 90)
            yield {
                "type": "state", "phase": "generating",
                "message": progress_msg,
                "progress": progress,
            }
        elif event_type == "token_usage":
            pass

    logger.debug("[react_stream] Done, %d events processed", event_count)
