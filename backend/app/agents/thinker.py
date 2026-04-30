"""
Thinker - Enhanced Thinking Module

Responsible for LLM inference and output parsing.
Supports streaming and non-streaming paths with exponential backoff retry.
Uses the shared LLMClient to eliminate code duplication.
"""
import time
import logging
from typing import Dict, Any, Generator, Optional
from dataclasses import dataclass

from app.agents.llm_client import LLMClient, LLMConfig, create_llm_client
from app.agents.types import ParsedOutput
from app.agents.exceptions import ReActAgentError
from app.agents.error_handler import sanitize_error_message

logger = logging.getLogger(__name__)


@dataclass
class ThinkConfig:
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 4096
    enable_thinking: bool = False
    retry_count: int = 2
    retry_base_delay: float = 0.5
    retry_max_delay: float = 4.0


class Thinker:
    """Thinking engine with LLM inference and output parsing."""

    def __init__(self, provider: str = "openai", config: Optional[ThinkConfig] = None):
        self.provider = provider
        self.config = config or ThinkConfig()
        self.llm = create_llm_client(
            provider=provider,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_tokens=self.config.max_tokens,
            enable_thinking=self.config.enable_thinking,
        )

    def think(self, prompt: str) -> ParsedOutput:
        """
        Synchronous thinking — calls LLM and parses output.

        Returns ParsedOutput with thought, action, is_final_answer, final_answer.
        On all-retries-exhausted, returns a graceful degradation response.
        """
        from app.agents.output_parser import OutputParser
        parser = OutputParser(mode="json")
        last_error = None

        for attempt in range(self.config.retry_count + 1):
            try:
                llm_output = self.llm.complete(prompt)
                if not llm_output or len(llm_output.strip()) < 10:
                    raise ReActAgentError("LLM output too short or empty")
                parsed = parser.parse(llm_output)
                return ParsedOutput(
                    thought=parsed.get("thought", ""),
                    action=parsed.get("action"),
                    action_input=parsed.get("action_input"),
                    is_final_answer=parsed.get("is_final_answer", False),
                    final_answer=parsed.get("final_answer"),
                )
            except Exception as e:
                last_error = e
                if attempt < self.config.retry_count:
                    delay = min(
                        self.config.retry_base_delay * (2 ** attempt),
                        self.config.retry_max_delay,
                    )
                    logger.warning(
                        f"[Thinker] Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

        logger.error(f"[Thinker] All {self.config.retry_count + 1} attempts exhausted.")
        error_msg = sanitize_error_message(last_error) if last_error else "未知错误"
        return ParsedOutput(
            thought=f"LLM调用在{self.config.retry_count + 1}次重试后仍然失败。",
            action=None,
            action_input=None,
            is_final_answer=True,
            final_answer=f"抱歉，AI推理服务暂时不可用（已重试{self.config.retry_count + 1}次）。请稍后再试。错误: {error_msg}",
        )

    def think_stream(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        """
        Streaming thinking — yields chunks as they arrive, then a complete parsed result.

        Yields:
            {"type": "thought_chunk", "content": "..."}
            {"type": "thought_complete", "parsed": ParsedOutput}
            {"type": "thought_error", "message": str, "raw_output": str}
        """
        from app.agents.output_parser import OutputParser
        parser = OutputParser(mode="json")
        buffer = ""

        for chunk in self.llm.complete_stream(prompt):
            if isinstance(chunk, dict):
                if chunk.get("type") == "reasoning_chunk":
                    yield {"type": "reasoning_chunk", "content": chunk["content"]}
                elif chunk.get("type") == "content":
                    buffer += chunk["content"]
                    yield {"type": "thought_chunk", "content": chunk["content"]}
            else:
                buffer += chunk
                yield {"type": "thought_chunk", "content": chunk}

        try:
            parsed = parser.parse(buffer)
            yield {
                "type": "thought_complete",
                "parsed": ParsedOutput(
                    thought=parsed.get("thought", ""),
                    action=parsed.get("action"),
                    action_input=parsed.get("action_input"),
                    is_final_answer=parsed.get("is_final_answer", False),
                    final_answer=parsed.get("final_answer"),
                ),
            }
        except Exception as e:
            logger.error(f"[Thinker] Stream parse failed: {e}")
            yield {
                "type": "thought_error",
                "message": str(e),
                "raw_output": buffer[:500],
            }
