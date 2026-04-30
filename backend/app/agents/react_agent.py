"""
ReAct Agent v2.0 - 核心执行引擎
统一循环引擎，消除 run()/stream_run() 代码重复
模块化组件: ThinkEngine, ActionEngine, ObservationCompressor, Reflector, TokenBudgetManager
"""
import logging
from typing import Dict, Any, Optional, List, Generator
from app.core.config import get_complete_config
from app.skills import get_skill_manager
from app.agents.memory import MemoryScratchpad
from app.agents.output_parser import OutputParser
from app.agents.prompt_engine import PromptEngine
from app.agents.think_engine import ThinkEngine, ThinkConfig
from app.agents.action_engine import ActionEngine
from app.agents.observation_compressor import ObservationCompressor
from app.agents.reflector import Reflector
from app.agents.token_budget import TokenBudgetManager
from app.agents.error_handler import sanitize_error_message, classify_error
from app.agents.exceptions import (
    ReActAgentError,
    OutputParseError,
    MaxIterationsReached,
    ToolNotFoundError,
    ToolExecutionError,
)

logger = logging.getLogger(__name__)


class ReActAgent:
    """
    ReAct Agent v2.0 — 统一循环引擎

    核心改进:
    1. 统一 execute() 方法替代 run()/stream_run()，消除 95% 代码重复
    2. 模块化组件: ThinkEngine, ActionEngine, ObservationCompressor, Reflector
    3. Token 预算感知，自动压缩历史 Observation
    4. 显式 Reflection 阶段
    5. 安全错误消息（不泄露敏感信息）
    6. Prompt 分层缓存
    """

    def __init__(
        self,
        max_iterations: int = 5,
        output_format: str = "json",
        use_few_shot: bool = True,
        provider: str = "openai",
        max_tokens: int = 4096,
    ):
        self.cfg = get_complete_config()
        self.max_iterations = max_iterations
        self.provider = provider

        think_config = ThinkConfig(max_tokens=max_tokens)
        self.think_engine = ThinkEngine(provider=provider, config=think_config)
        self.action_engine = ActionEngine()
        self.compressor = ObservationCompressor()
        self.reflector = Reflector()
        self.scratchpad = MemoryScratchpad()
        self.token_budget = TokenBudgetManager(
            max_tokens=self.cfg.get("react_token_budget", 6000)
        )

        self.tools = self._get_tools_list()
        self.prompt_engine = PromptEngine(tools=self.tools, use_few_shot=use_few_shot)
        self._current_retrieved_context = ""

        logger.info(f"[ReActAgent] Initialized with max_iterations={max_iterations}, provider={provider}")

    def _get_tools_list(self) -> List[Dict[str, Any]]:
        skill_manager = get_skill_manager()
        skills = skill_manager.list_skills()
        tools = []
        for skill in skills:
            tools.append({
                "name": skill["name"],
                "description": skill["description"]
            })
        logger.debug(f"[ReActAgent] Loaded {len(tools)} tools")
        return tools

    def execute(
        self,
        user_question: str,
        conversation_history: str = "",
        retrieved_context: str = "",
        stream: bool = False
    ) -> Generator[Dict[str, Any], None, None]:
        """
        统一执行入口 —— 消除 run()/stream_run() 重复

        Args:
            user_question: 用户问题
            conversation_history: 对话历史
            retrieved_context: 检索到的知识库上下文
            stream: 是否流式输出

        Yields:
            事件字典 (type 字段标识事件类型)
        """
        logger.info(f"[ReActAgent] Starting for: {user_question[:50]}...")
        self._current_retrieved_context = retrieved_context

        base_prompt_cache = {}

        try:
            for iteration in range(self.max_iterations):
                yield {
                    "type": "thinking",
                    "iteration": iteration + 1,
                    "total": self.max_iterations
                }

                prompt = self._build_iteration_prompt(
                    user_question=user_question,
                    conversation_history=conversation_history,
                    iteration=iteration,
                    cache=base_prompt_cache
                )

                prompt_tokens = self.token_budget.estimate_tokens(prompt)
                if prompt_tokens > self.token_budget.max_tokens * 0.9:
                    self.scratchpad.compress_history(self.compressor)
                    prompt = self._build_iteration_prompt(
                        user_question=user_question,
                        conversation_history=conversation_history,
                        iteration=iteration,
                        cache={}
                    )
                    logger.warning(
                        f"[ReActAgent] Prompt too long ({prompt_tokens} tokens), "
                        f"compressed scratchpad"
                    )

                yield {
                    "type": "token_usage",
                    "estimated_tokens": prompt_tokens,
                    "budget_remaining": self.token_budget.max_tokens - prompt_tokens
                }

                if stream:
                    parsed = None
                    for event in self.think_engine.think_stream(prompt):
                        if event["type"] == "thought_chunk":
                            yield {"type": "thought_chunk", "content": event["content"]}
                        elif event["type"] == "thought_complete":
                            parsed = event["parsed"]
                        elif event["type"] == "thought_error":
                            logger.warning(f"[ReActAgent] Stream parse error: {event['message']}")
                            parsed = self.think_engine.think(prompt, stream=False)
                            break

                    if parsed is None:
                        parsed = self.think_engine.think(prompt, stream=False)
                else:
                    parsed = self.think_engine.think(prompt, stream=False)

                # 验证解析结果，修复 null/None/空 final_answer
                parsed = self._validate_parsed_result(parsed)

                yield {"type": "thought", "content": parsed["thought"]}

                evaluation = self.reflector.evaluate(
                    user_question=user_question,
                    thought=parsed["thought"],
                    action=parsed.get("action"),
                    observation="",
                    iteration=iteration,
                    max_iterations=self.max_iterations,
                    scratchpad_steps=self.scratchpad.get_steps()
                )

                if parsed["is_final_answer"] or (
                    evaluation["should_stop"] and not parsed.get("action")
                ):
                    logger.info(
                        f"[ReActAgent] Final answer at iteration {iteration + 1}. "
                        f"Reason: {evaluation['reason']}"
                    )
                    self.scratchpad.add_step(thought=parsed["thought"])
                    yield {"type": "final_answer", "content": parsed["final_answer"]}
                    yield {
                        "type": "done",
                        "final_answer": parsed["final_answer"],
                        "steps": self.scratchpad.get_steps(),
                        "success": True,
                        "iterations_used": iteration + 1
                    }
                    return

                action = parsed.get("action")
                action_input = parsed.get("action_input") or {}

                if not action:
                    logger.warning("[ReActAgent] No action and no final answer, forcing")
                    fallback_answer = self._force_answer_from_thought(parsed["thought"], parsed)
                    self.scratchpad.add_step(thought=parsed["thought"])
                    yield {"type": "final_answer", "content": fallback_answer}
                    yield {
                        "type": "done",
                        "final_answer": fallback_answer,
                        "steps": self.scratchpad.get_steps(),
                        "success": True
                    }
                    return

                yield {"type": "action", "name": action, "input": action_input}

                try:
                    result = self.action_engine.execute(action, action_input)
                except ToolNotFoundError as e:
                    result = {
                        "success": False,
                        "output": f"工具未找到: {str(e)}",
                        "error": str(e),
                        "tool_name": action,
                        "params_used": action_input,
                        "execution_time_ms": 0
                    }
                except Exception as e:
                    error_class = classify_error(e)
                    result = {
                        "success": False,
                        "output": error_class["user_message"],
                        "error": str(e),
                        "tool_name": action,
                        "params_used": action_input,
                        "execution_time_ms": 0
                    }

                raw_output = result["output"]

                compressed_obs = self.compressor.compress(
                    raw_output,
                    action_name=action
                )

                yield {
                    "type": "observation",
                    "content": compressed_obs,
                    "raw_length": len(raw_output),
                    "compressed_length": len(compressed_obs),
                    "success": result["success"]
                }

                post_eval = self.reflector.evaluate(
                    user_question=user_question,
                    thought=parsed["thought"],
                    action=action,
                    observation=compressed_obs,
                    iteration=iteration,
                    max_iterations=self.max_iterations,
                    scratchpad_steps=self.scratchpad.get_steps()
                )

                self.scratchpad.add_step(
                    thought=parsed["thought"],
                    action=action,
                    action_input=action_input,
                    observation=compressed_obs,
                    raw_observation=raw_output
                )

                if post_eval["should_stop"] and not result["success"]:
                    logger.info(
                        f"[ReActAgent] Tool failed and reflector suggests stop: {post_eval['reason']}"
                    )

            yield {
                "type": "error",
                "message": f"达到最大迭代次数 ({self.max_iterations})"
            }
            yield {
                "type": "done",
                "final_answer": "抱歉，经过多步思考仍未能得出满意答案。请尝试简化问题或提供更多细节。",
                "steps": self.scratchpad.get_steps(),
                "success": False,
                "iterations_used": self.max_iterations
            }

        except Exception as e:
            logger.error(f"[ReActAgent] Unexpected error: {e}", exc_info=True)
            safe_msg = "执行过程中发生内部错误，请稍后重试。"
            yield {"type": "error", "message": safe_msg}
            yield {
                "type": "done",
                "final_answer": safe_msg,
                "steps": self.scratchpad.get_steps(),
                "success": False
            }

    def run(
        self,
        user_question: str,
        conversation_history: str = "",
        retrieved_context: str = ""
    ) -> Dict[str, Any]:
        """
        执行 ReAct 循环（非流式，兼容旧接口）

        Args:
            user_question: 用户问题
            conversation_history: 对话历史

        Returns:
            最终结果
        """
        final_answer = ""
        steps = []
        success = False

        for event in self.execute(
            user_question=user_question,
            conversation_history=conversation_history,
            retrieved_context=retrieved_context,
            stream=False
        ):
            if event.get("type") == "final_answer":
                final_answer = event.get("content", "")
            elif event.get("type") == "done":
                final_answer = event.get("final_answer", final_answer)
                steps = event.get("steps", steps)
                success = event.get("success", False)

        return {
            "final_answer": final_answer,
            "steps": steps,
            "success": success
        }

    def stream_run(
        self,
        user_question: str,
        conversation_history: str = "",
        retrieved_context: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """
        执行 ReAct 循环（流式，兼容旧接口）

        Args:
            user_question: 用户问题
            conversation_history: 对话历史

        Yields:
            事件字典
        """
        yield from self.execute(
            user_question=user_question,
            conversation_history=conversation_history,
            retrieved_context=retrieved_context,
            stream=True
        )

    def _build_iteration_prompt(
        self,
        user_question: str,
        conversation_history: str,
        iteration: int,
        cache: dict
    ) -> str:
        ctx = getattr(self, '_current_retrieved_context', '')
        if "system_part" not in cache:
            cache["system_part"] = self.prompt_engine.get_system_part()
            cache["tools_part"] = self.prompt_engine.get_tools_part()

        scratchpad_text = self.scratchpad.get_scratchpad_text()

        if cache.get("system_part") and cache.get("tools_part"):
            return self.prompt_engine.build_prompt_from_parts(
                system_part=cache["system_part"],
                tools_part=cache["tools_part"],
                user_question=user_question,
                scratchpad_text=scratchpad_text,
                conversation_history=conversation_history,
                retrieved_context=ctx,
                provider=self.provider
            )

        return self.prompt_engine.build_prompt(
            user_question=user_question,
            scratchpad_text=scratchpad_text,
            conversation_history=conversation_history,
            retrieved_context=ctx,
            provider=self.provider
        )

    def _validate_parsed_result(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并修复解析结果

        修复场景:
        1. is_final_answer=True 但 final_answer 为 null/None/空/"None"
        2. thought 为空但 is_final_answer=True
        3. final_answer 过短（<10 字符）且 thought 有内容 → 用 thought 补全
        """
        fa = parsed.get("final_answer")
        is_final = parsed.get("is_final_answer", False)
        thought = parsed.get("thought", "")

        # 场景 1: is_final_answer 但 final_answer 无效 → 强制降级
        if is_final:
            fa_str = str(fa).strip() if fa is not None else ""
            if fa is None or fa_str in ("", "None", "null", "none") or len(fa_str) < 5:
                logger.warning(
                    f"[ReActAgent] Invalid final_answer detected: "
                    f"is_final=True, fa='{fa_str}' (len={len(fa_str)}), "
                    f"forcing is_final_answer=False"
                )
                parsed["is_final_answer"] = False
                parsed["final_answer"] = None
                is_final = False

        # 场景 2: thought 为空 → 尝试从 final_answer 回填
        if (not thought or not str(thought).strip()) and fa:
            parsed["thought"] = str(fa)

        # 场景 3: is_final_answer 但 final_answer 过短 → 用 thought 作为答案
        if is_final and fa and len(str(fa).strip()) < 10 and thought and len(str(thought).strip()) > 20:
            logger.info("[ReActAgent] final_answer too short, using thought as answer")
            parsed["final_answer"] = str(thought).strip()

        return parsed

    def _force_answer_from_thought(self, thought: str, parsed: Dict[str, Any] = None) -> str:
        if parsed and parsed.get("final_answer"):
            final_answer = str(parsed.get("final_answer")).strip()
            if len(final_answer) > 10 and final_answer not in ("None", "null", "none"):
                return final_answer

        for marker in ["最终答案", "答案", "Final Answer"]:
            idx = thought.find(marker)
            if idx >= 0:
                extracted = thought[idx + len(marker):].strip("：:。. \n")
                if extracted and extracted not in ("None", "null", "none") and len(extracted) > 5:
                    return extracted

        # 兜底：返回 thought 本身（但如果 thought 也空/无效，给一个合理的降级消息）
        if thought and thought.strip() and thought.strip() not in ("None", "null", "none"):
            return thought.strip()

        return "抱歉，我暂时无法回答这个问题。请尝试提供更多信息，或换一种方式提问。"

    def reset(self) -> None:
        self.scratchpad.clear()
        self.prompt_engine.clear_request_cache()
        logger.debug("[ReActAgent] Reset")
