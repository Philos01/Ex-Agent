"""
Reflector - Enhanced Reflection Module

Evaluates agent state after each observation to decide whether to continue or stop.
Supports both fast keyword-based evaluation and LLM-based deep evaluation.
"""
import logging
from typing import Dict, Any, List, Optional, Union

from app.agents.types import ReflectionResult, AgentStep

logger = logging.getLogger(__name__)


class Reflector:
    """Evaluates agent state to guide the ReAct loop."""

    STRONG_END_SIGNALS = [
        "搜索完成", "Search Results", "查询成功", "天气信息", "Skill execution",
    ]
    WEAK_CONTINUE_SIGNALS = [
        "未找到", "没有结果", "0 papers", "执行失败", "搜索失败",
        "failed", "no results",
    ]

    def __init__(self, use_llm: bool = False, provider: str = "openai"):
        self.use_llm = use_llm
        self.provider = provider

    def evaluate(
        self,
        user_question: str,
        thought: str,
        action: Optional[str],
        observation: str,
        iteration: int,
        max_iterations: int,
        steps: Union[List[AgentStep], List[Dict[str, Any]]],
        action_success: bool = True,
    ) -> ReflectionResult:
        """
        Evaluate current state and decide next action.

        Returns ReflectionResult with should_stop, should_continue, confidence, reason, suggestion.
        """
        # Hard stop at max iterations
        if iteration >= max_iterations - 1:
            return ReflectionResult(
                should_stop=True,
                should_continue=False,
                confidence=0.5,
                reason="达到最大迭代次数",
            )

        # No action means the model chose to answer directly
        if not action:
            return ReflectionResult(
                should_stop=True,
                should_continue=False,
                confidence=0.9,
                reason="模型判断无需调用工具",
            )

        # LLM-based evaluation
        if self.use_llm:
            return self._llm_evaluate(
                user_question, thought, action, observation,
                iteration, max_iterations, steps, action_success,
            )

        # Fast keyword-based evaluation
        return self._keyword_evaluate(
            observation, action, iteration, max_iterations, steps, action_success,
        )

    def _keyword_evaluate(
        self,
        observation: str,
        action: str,
        iteration: int,
        max_iterations: int,
        steps: Union[List[AgentStep], List[Dict[str, Any]]],
        action_success: bool,
    ) -> ReflectionResult:
        """Fast keyword-based evaluation."""
        # Strong success signals → stop
        for signal in self.STRONG_END_SIGNALS:
            if signal in observation and action_success:
                return ReflectionResult(
                    should_stop=True,
                    should_continue=False,
                    confidence=0.85,
                    reason=f"观察结果包含成功信号: {signal}",
                )

        # Weak failure signals → retry if iterations remain
        for signal in self.WEAK_CONTINUE_SIGNALS:
            if signal in observation:
                if iteration < max_iterations - 2:
                    return ReflectionResult(
                        should_stop=False,
                        should_continue=True,
                        confidence=0.2,
                        reason=f"观察结果表明需要重试: {signal}",
                        suggestion=self._suggest_retry(action, observation),
                    )

        # Detect repetitive action loops
        if len(steps) >= 2:
            last_actions = [
                s.action if hasattr(s, "action") else s.get("action")
                for s in steps[-2:]
            ]
            if len(last_actions) >= 2 and last_actions[-1] == last_actions[-2] == action:
                return ReflectionResult(
                    should_stop=True,
                    should_continue=False,
                    confidence=0.6,
                    reason="连续调用同一工具，可能陷入循环",
                    suggestion="基于已有结果给出最佳回答",
                )

        # Default: observation looks fine, suggest stopping
        return ReflectionResult(
            should_stop=True,
            should_continue=False,
            confidence=0.7,
            reason="观察结果正常，信息充足",
        )

    def _llm_evaluate(
        self,
        user_question: str,
        thought: str,
        action: str,
        observation: str,
        iteration: int,
        max_iterations: int,
        steps: List[AgentStep],
        action_success: bool,
    ) -> ReflectionResult:
        """LLM-based deep evaluation for complex decisions."""
        try:
            from app.agents.llm_client import create_llm_client
            llm = create_llm_client(provider=self.provider, max_tokens=256, temperature=0.0)
            prompt = self._build_reflection_prompt(
                user_question, thought, action, observation,
                iteration, max_iterations, steps, action_success,
            )
            response = llm.complete(prompt)
            return self._parse_reflection_response(response, action, observation)
        except Exception as e:
            logger.warning(f"[Reflector] LLM evaluation failed, falling back to keyword: {e}")
            return self._keyword_evaluate(
                observation, action, iteration, max_iterations, steps, action_success,
            )

    def _build_reflection_prompt(
        self,
        user_question: str,
        thought: str,
        action: str,
        observation: str,
        iteration: int,
        max_iterations: int,
        steps: List[AgentStep],
        action_success: bool,
    ) -> str:
        steps_text = "\n".join(
            f"Step {i}: action={s.action}, success={s.success}"
            for i, s in enumerate(steps, 1)
        ) if steps else "无"
        return f"""评估当前 ReAct Agent 状态，决定是否应继续迭代。

用户问题: {user_question}
当前思考: {thought[:200]}
执行动作: {action}
动作成功: {action_success}
观察结果: {observation[:300]}
当前迭代: {iteration + 1}/{max_iterations}
历史步骤: {steps_text}

请回答（仅 JSON）:
{{"should_stop": true/false, "reason": "简短理由", "suggestion": "建议或null"}}"""

    def _parse_reflection_response(
        self, response: str, action: str, observation: str
    ) -> ReflectionResult:
        import json
        try:
            match = __import__("re").search(r"\{[\s\S]*\}", response)
            data = json.loads(match.group(0)) if match else {}
            return ReflectionResult(
                should_stop=data.get("should_stop", True),
                should_continue=not data.get("should_stop", True),
                confidence=0.8,
                reason=data.get("reason", "LLM评估"),
                suggestion=data.get("suggestion"),
            )
        except Exception:
            return ReflectionResult(
                should_stop=True,
                should_continue=False,
                confidence=0.7,
                reason="观察结果正常",
            )

    def _suggest_retry(self, action: str, observation: str) -> Optional[str]:
        """Suggest a retry strategy based on the failed action."""
        if action == "arxiv-watcher":
            if "0 papers" in observation or "未找到" in observation:
                return "尝试使用更广泛/不同的关键词重新搜索"
            if "执行失败" in observation or "failed" in observation.lower():
                return "ArXiv API 可能暂时不可用，稍后重试或使用本地知识库"
        return "尝试调整参数后重新调用"
