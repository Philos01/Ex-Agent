"""
AgentLoop - Unified ReAct Agent Execution Engine

Single unified loop that replaces the dual run()/stream_run() pattern.
Delegates to modular components: Thinker, Actor, Observer, Reflector.
"""
import logging
from typing import Dict, Any, List, Generator, Optional

from app.core.config import get_complete_config
from app.agents.types import (
    AgentStep, AgentState, AgentEvent, EventType,
    ParsedOutput, ReflectionResult,
)
from app.agents.thinker import Thinker, ThinkConfig
from app.agents.actor import Actor
from app.agents.observer import Observer
from app.agents.reflector import Reflector
from app.agents.memory import MemoryScratchpad
from app.agents.prompt_engine import PromptEngine
from app.agents.token_budget import TokenBudgetManager
from app.agents.error_handler import classify_error
from app.agents.exceptions import ToolNotFoundError

logger = logging.getLogger(__name__)


class AgentLoop:
    """
    ReAct Agent v3.0 — Unified Execution Engine

    Core cycle: Think → Act → Observe → Reflect → (repeat or finish)

    Key improvements over v2:
    1. Single execute() method — no run()/stream_run() duplication
    2. Standardized event types via AgentEvent
    3. Immutable AgentState tracking
    4. LLM-based reflection option
    5. Shared LLMClient eliminates code duplication
    """

    def __init__(
        self,
        max_iterations: int = 5,
        provider: str = "openai",
        use_few_shot: bool = True,
        use_llm_reflection: bool = False,
        max_tokens: int = 4096,
        enable_thinking: bool = False,
    ):
        self.cfg = get_complete_config()
        self.max_iterations = max_iterations
        self.provider = provider

        # Core modules
        think_config = ThinkConfig(max_tokens=max_tokens, enable_thinking=enable_thinking)
        self.thinker = Thinker(provider=provider, config=think_config)
        self.actor = Actor()
        self.observer = Observer()
        self.reflector = Reflector(use_llm=use_llm_reflection, provider=provider)

        # Support modules
        self.scratchpad = MemoryScratchpad()
        self.token_budget = TokenBudgetManager(
            max_tokens=self.cfg.get("react_token_budget", 6000)
        )
        self._current_retrieved_context = ""

        # Tools & prompts
        self.tools = self._load_tools()
        self.prompt_engine = PromptEngine(tools=self.tools, use_few_shot=use_few_shot)

        logger.info(
            f"[AgentLoop] Initialized: max_iter={max_iterations}, "
            f"provider={provider}, tools={len(self.tools)}"
        )

    def _load_tools(self) -> List[Dict[str, Any]]:
        from app.skills import get_skill_manager
        skill_manager = get_skill_manager()
        skills = skill_manager.list_skills()
        return [{"name": s["name"], "description": s["description"]} for s in skills]

    # ── Public API ──────────────────────────────────────

    def run(
        self,
        user_question: str,
        conversation_history: str = "",
        retrieved_context: str = "",
    ) -> Dict[str, Any]:
        """Non-streaming execution. Returns final result dict."""
        final_answer = ""
        steps = []
        success = False

        for event in self.execute(user_question, conversation_history, retrieved_context=retrieved_context, stream=False):
            if event.type == EventType.FINAL_ANSWER:
                final_answer = event.content or ""
            elif event.type == EventType.DONE:
                final_answer = event.content or final_answer
                steps = event.metadata.get("steps", steps)
                success = event.metadata.get("success", False)

        return {"final_answer": final_answer, "steps": steps, "success": success}

    def stream_run(
        self,
        user_question: str,
        conversation_history: str = "",
        retrieved_context: str = "",
    ) -> Generator[Dict[str, Any], None, None]:
        """Streaming execution. Yields event dicts."""
        for event in self.execute(user_question, conversation_history, retrieved_context=retrieved_context, stream=True):
            yield event.to_dict()

    def execute(
        self,
        user_question: str,
        conversation_history: str = "",
        retrieved_context: str = "",
        stream: bool = False,
    ) -> Generator[AgentEvent, None, None]:
        """
        Unified execution entry point.

        Yields AgentEvent objects with standardized types.
        """
        logger.info(f"[AgentLoop] Starting: {user_question[:50]}...")

        base_prompt_cache: Dict[str, str] = {}
        self._current_retrieved_context = retrieved_context
        state = AgentState(max_iterations=self.max_iterations)

        try:
            for iteration in range(self.max_iterations):
                yield AgentEvent(
                    type=EventType.THINKING,
                    iteration=iteration + 1,
                    total_iterations=self.max_iterations,
                )

                # ── Build prompt with caching ──
                prompt = self._build_prompt(
                    user_question, conversation_history, iteration,
                    cache=base_prompt_cache,
                )

                prompt_tokens = self.token_budget.estimate_tokens(prompt)
                if prompt_tokens > self.token_budget.max_tokens * 0.9:
                    self.scratchpad.compress_history(self.observer.compress)
                    prompt = self._build_prompt(
                        user_question, conversation_history, iteration, cache={},
                    )

                yield AgentEvent(
                    type=EventType.TOKEN_USAGE,
                    iteration=iteration + 1,
                    total_iterations=self.max_iterations,
                    metadata={
                        "estimated_tokens": prompt_tokens,
                        "budget_remaining": self.token_budget.max_tokens - prompt_tokens,
                    },
                )

                # ── THINK ──
                parsed = self._do_think(prompt, stream)
                if stream:
                    # In stream mode, _do_think yields intermediate events;
                    # the last yield is the parsed result with type="thought_complete"
                    for chunk_event in parsed:
                        if chunk_event.get("type") == "thought_chunk":
                            yield AgentEvent(
                                type=EventType.THOUGHT_CHUNK,
                                content=chunk_event.get("content"),
                                iteration=iteration + 1,
                                total_iterations=self.max_iterations,
                            )
                        elif chunk_event.get("type") == "reasoning_chunk":
                            yield AgentEvent(
                                type=EventType.REASONING_CHUNK,
                                content=chunk_event.get("content"),
                                iteration=iteration + 1,
                                total_iterations=self.max_iterations,
                            )
                        elif chunk_event.get("type") == "thought_complete":
                            parsed = chunk_event["parsed"]
                        elif chunk_event.get("type") == "thought_error":
                            logger.warning(f"[AgentLoop] Stream parse error: {chunk_event['message']}")
                            parsed = self.thinker.think(prompt)

                parsed = self._validate_parsed(parsed)

                yield AgentEvent(
                    type=EventType.THOUGHT,
                    content=parsed.thought,
                    iteration=iteration + 1,
                    total_iterations=self.max_iterations,
                )

                # ── REFLECT (pre-action) ──
                evaluation = self.reflector.evaluate(
                    user_question=user_question,
                    thought=parsed.thought,
                    action=parsed.action,
                    observation="",
                    iteration=iteration,
                    max_iterations=self.max_iterations,
                    steps=state.steps,
                )

                # ── Check for final answer ──
                if parsed.is_final_answer or (evaluation.should_stop and not parsed.action):
                    logger.info(
                        f"[AgentLoop] Final answer at iteration {iteration + 1}. "
                        f"Reason: {evaluation.reason}"
                    )
                    self.scratchpad.add_step(thought=parsed.thought)
                    yield AgentEvent(
                        type=EventType.FINAL_ANSWER,
                        content=parsed.final_answer,
                        iteration=iteration + 1,
                        total_iterations=self.max_iterations,
                    )
                    yield AgentEvent(
                        type=EventType.DONE,
                        content=parsed.final_answer,
                        metadata={
                            "steps": self.scratchpad.get_steps(),
                            "success": True,
                            "iterations_used": iteration + 1,
                        },
                    )
                    return

                action = parsed.action
                action_input = parsed.action_input or {}

                if not action:
                    logger.warning("[AgentLoop] No action and no final answer, forcing answer")
                    fallback = self._force_answer(parsed.thought, parsed)
                    self.scratchpad.add_step(thought=parsed.thought)
                    yield AgentEvent(
                        type=EventType.FINAL_ANSWER,
                        content=fallback,
                        iteration=iteration + 1,
                        total_iterations=self.max_iterations,
                    )
                    yield AgentEvent(
                        type=EventType.DONE,
                        content=fallback,
                        metadata={
                            "steps": self.scratchpad.get_steps(),
                            "success": True,
                        },
                    )
                    return

                # ── ACT ──
                yield AgentEvent(
                    type=EventType.ACTION,
                    content={"name": action, "input": action_input},
                    iteration=iteration + 1,
                    total_iterations=self.max_iterations,
                )

                try:
                    result = self.actor.execute(action, action_input)
                except ToolNotFoundError as e:
                    result = type("R", (), {})()
                    result.success = False
                    result.output = f"工具未找到: {str(e)}"
                    result.error = str(e)
                    result.tool_name = action
                    result.params_used = action_input
                    result.execution_time_ms = 0
                except Exception as e:
                    error_class = classify_error(e)
                    result = type("R", (), {})()
                    result.success = False
                    result.output = error_class["user_message"]
                    result.error = str(e)
                    result.tool_name = action
                    result.params_used = action_input
                    result.execution_time_ms = 0

                # ── OBSERVE ──
                obs = self.observer.process(result)

                yield AgentEvent(
                    type=EventType.OBSERVATION,
                    content=obs["compressed"],
                    iteration=iteration + 1,
                    total_iterations=self.max_iterations,
                    metadata={
                        "raw_length": obs["raw_length"],
                        "compressed_length": obs["compressed_length"],
                        "success": obs["success"],
                    },
                )

                # ── REFLECT (post-action) ──
                post_eval = self.reflector.evaluate(
                    user_question=user_question,
                    thought=parsed.thought,
                    action=action,
                    observation=obs["compressed"],
                    iteration=iteration,
                    max_iterations=self.max_iterations,
                    steps=state.steps,
                    action_success=obs["success"],
                )

                # ── Update scratchpad & state ──
                step = AgentStep(
                    thought=parsed.thought,
                    action=action,
                    action_input=action_input,
                    observation=obs["compressed"],
                    raw_observation=obs["raw"],
                    success=obs["success"],
                )
                self.scratchpad.add_step(
                    thought=step.thought,
                    action=step.action,
                    action_input=step.action_input,
                    observation=step.observation,
                    raw_observation=step.raw_observation,
                )
                state = state.add_step(step)

                # ── Stop on persistent failure ──
                if post_eval.should_stop and not obs["success"]:
                    logger.info(f"[AgentLoop] Action failed and reflector suggests stop: {post_eval.reason}")

            # Max iterations reached
            yield AgentEvent(
                type=EventType.ERROR,
                content=f"达到最大迭代次数 ({self.max_iterations})",
            )
            yield AgentEvent(
                type=EventType.DONE,
                content="抱歉，经过多步思考仍未能得出满意答案。请尝试简化问题或提供更多细节。",
                metadata={
                    "steps": self.scratchpad.get_steps(),
                    "success": False,
                    "iterations_used": self.max_iterations,
                },
            )

        except Exception as e:
            logger.error(f"[AgentLoop] Unexpected error: {e}", exc_info=True)
            safe_msg = "执行过程中发生内部错误，请稍后重试。"
            yield AgentEvent(type=EventType.ERROR, content=safe_msg)
            yield AgentEvent(
                type=EventType.DONE,
                content=safe_msg,
                metadata={"steps": self.scratchpad.get_steps(), "success": False},
            )

    # ── Internal Helpers ────────────────────────────────

    def _do_think(self, prompt: str, stream: bool):
        """Execute thinking phase. Returns ParsedOutput (sync) or generator (stream)."""
        if stream:
            return self.thinker.think_stream(prompt)
        return self.thinker.think(prompt)

    def _build_prompt(
        self,
        user_question: str,
        conversation_history: str,
        iteration: int,
        cache: dict,
    ) -> str:
        if "system_part" not in cache:
            cache["system_part"] = self.prompt_engine.get_system_part()
            cache["tools_part"] = self.prompt_engine.get_tools_part()

        if cache.get("system_part") and cache.get("tools_part"):
            return self.prompt_engine.build_prompt_from_parts(
                system_part=cache["system_part"],
                tools_part=cache["tools_part"],
                user_question=user_question,
                scratchpad_text=self.scratchpad.get_scratchpad_text(),
                conversation_history=conversation_history,
                retrieved_context=self._current_retrieved_context,
                provider=self.provider,
            )
        return self.prompt_engine.build_prompt(
            user_question=user_question,
            scratchpad_text=self.scratchpad.get_scratchpad_text(),
            conversation_history=conversation_history,
            retrieved_context=self._current_retrieved_context,
            provider=self.provider,
        )

    def _validate_parsed(self, parsed: ParsedOutput) -> ParsedOutput:
        """Validate and repair parsed output."""
        fa = parsed.final_answer
        is_final = parsed.is_final_answer
        thought = parsed.thought
        fa_str = str(fa).strip() if fa is not None else ""

        if is_final:
            if fa is None or fa_str in ("", "None", "null", "none"):
                logger.warning(
                    f"[AgentLoop] Invalid final_answer: is_final=True, "
                    f"fa='{fa_str}', forcing is_final_answer=False"
                )
                parsed.is_final_answer = False
                parsed.final_answer = None
                is_final = False

        if (not thought or not str(thought).strip()) and fa:
            parsed.thought = str(fa)

        if is_final and fa and len(fa_str) < 10 and thought and len(str(thought).strip()) > 20:
            logger.info("[AgentLoop] final_answer too short, using thought as answer")
            parsed.final_answer = str(thought).strip()

        return parsed

    def _force_answer(self, thought: str, parsed: ParsedOutput) -> str:
        """Extract a best-effort answer from thought text."""
        fa = parsed.final_answer
        if fa:
            fa_str = str(fa).strip()
            if len(fa_str) > 10 and fa_str not in ("None", "null", "none"):
                return fa_str

        for marker in ["最终答案", "答案", "Final Answer"]:
            idx = thought.find(marker)
            if idx >= 0:
                extracted = thought[idx + len(marker):].strip("：:。. \n")
                if extracted and extracted not in ("None", "null", "none") and len(extracted) > 5:
                    return extracted

        if thought and thought.strip() and thought.strip() not in ("None", "null", "none"):
            return thought.strip()
        return "抱歉，我暂时无法回答这个问题。请尝试提供更多信息，或换一种方式提问。"

    def reset(self) -> None:
        """Reset agent state for a new task."""
        self.scratchpad.clear()
        self.prompt_engine.clear_request_cache()
        logger.debug("[AgentLoop] Reset")
