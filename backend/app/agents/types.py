"""
ReAct Agent Type Definitions

Centralized type definitions for the ReAct Agent system.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class StepType(str, Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    FINAL_ANSWER = "final_answer"


class EventType(str, Enum):
    THINKING = "thinking"
    THOUGHT_CHUNK = "thought_chunk"
    THOUGHT = "thought"
    REASONING_CHUNK = "reasoning_chunk"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"
    TOKEN_USAGE = "token_usage"
    ERROR = "error"
    DONE = "done"


@dataclass
class AgentStep:
    """Single step in the ReAct loop."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    raw_observation: Optional[str] = None
    reflection: Optional[str] = None
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thought": self.thought,
            "action": self.action,
            "action_input": self.action_input,
            "observation": self.observation,
            "raw_observation": self.raw_observation,
            "reflection": self.reflection,
            "success": self.success,
        }


@dataclass
class ParsedOutput:
    """Parsed LLM output."""
    thought: str = ""
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    is_final_answer: bool = False
    final_answer: Optional[str] = None


@dataclass
class ReflectionResult:
    """Result of reflection evaluation."""
    should_stop: bool = False
    should_continue: bool = True
    confidence: float = 0.5
    reason: str = ""
    suggestion: Optional[str] = None


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool = False
    output: str = ""
    error: Optional[str] = None
    tool_name: str = ""
    params_used: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


@dataclass
class AgentState:
    """Immutable snapshot of agent state at a point in time."""
    iteration: int = 0
    max_iterations: int = 5
    steps: List[AgentStep] = field(default_factory=list)
    is_finished: bool = False
    final_answer: Optional[str] = None
    success: bool = False

    def add_step(self, step: AgentStep) -> "AgentState":
        return AgentState(
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            steps=self.steps + [step],
            is_finished=self.is_finished,
            final_answer=self.final_answer,
            success=self.success,
        )


@dataclass
class AgentEvent:
    """Event emitted during agent execution."""
    type: EventType
    iteration: int = 0
    total_iterations: int = 5
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type.value,
            "iteration": self.iteration,
            "total": self.total_iterations,
        }
        if self.content is not None:
            result["content"] = self.content
        result.update(self.metadata)
        return result
