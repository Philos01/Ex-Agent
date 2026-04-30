"""
ReAct Agent Module v3.0 — Multi-step Reasoning & Tool Invocation

Modular architecture:
- AgentLoop: Unified execution engine
- Thinker: LLM inference & output parsing
- Actor: Tool dispatch & execution
- Observer: Result processing & compression
- Reflector: State evaluation (keyword + LLM-based)
- LLMClient: Shared LLM client factory
- Types: Centralized type definitions

Supporting:
- MemoryScratchpad, PromptEngine, TokenBudgetManager
- OutputParser, ErrorHandler, Exceptions
"""

# ── New v3.0 API ──
from app.agents.agent_loop import AgentLoop
from app.agents.thinker import Thinker, ThinkConfig
from app.agents.actor import Actor
from app.agents.observer import Observer
from app.agents.reflector import Reflector
from app.agents.types import (
    AgentStep, AgentState, AgentEvent, EventType, StepType,
    ParsedOutput, ReflectionResult, ActionResult,
)
from app.agents.llm_client import LLMClient, LLMConfig, create_llm_client

# ── Support Modules ──
from app.agents.memory import MemoryScratchpad
from app.agents.output_parser import OutputParser
from app.agents.prompt_engine import PromptEngine
from app.agents.token_budget import TokenBudgetManager
from app.agents.error_handler import sanitize_error_message, classify_error

# ── Exceptions ──
from app.agents.exceptions import (
    ReActAgentError,
    OutputParseError,
    MaxIterationsReached,
    ToolNotFoundError,
    ToolExecutionError,
)

# ── Backward compatibility: v2.0 ReActAgent alias ──
ReActAgent = AgentLoop
ThinkEngine = Thinker
ActionEngine = Actor
ObservationCompressor = Observer

__all__ = [
    # v3.0
    "AgentLoop",
    "Thinker", "ThinkConfig",
    "Actor",
    "Observer",
    "Reflector",
    "LLMClient", "LLMConfig", "create_llm_client",
    "AgentStep", "AgentState", "AgentEvent", "EventType", "StepType",
    "ParsedOutput", "ReflectionResult", "ActionResult",
    # Support
    "MemoryScratchpad",
    "OutputParser",
    "PromptEngine",
    "TokenBudgetManager",
    "sanitize_error_message", "classify_error",
    # Exceptions
    "ReActAgentError", "OutputParseError", "MaxIterationsReached",
    "ToolNotFoundError", "ToolExecutionError",
    # Backward compatibility
    "ReActAgent", "ThinkEngine", "ActionEngine", "ObservationCompressor",
]
