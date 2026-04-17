"""
ReAct Agent - 核心执行引擎
"""
import logging
import json
import re
from typing import Dict, Any, Optional, List, Generator
from app.core.config import load_config
from app.skills import get_skill_manager
from app.agents.memory import MemoryScratchpad
from app.agents.output_parser import OutputParser
from app.agents.prompt_engine import PromptEngine
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
    ReAct (Reasoning and Acting) Agent 核心执行引擎
    
    核心循环:
    1. 构建 Prompt
    2. 调用 LLM
    3. 解析输出
    4. 如果是 Final Answer → 返回结果
    5. 否则 → 执行工具，获取 Observation
    6. 更新暂存器，继续循环
    """
    
    def __init__(
        self,
        max_iterations: int = 5,
        output_format: str = "json",
        use_few_shot: bool = True,
        provider: str = "openai"
    ):
        """
        初始化 ReAct Agent
        
        Args:
            max_iterations: 最大迭代次数
            output_format: 输出格式，"json" 或 "text"
            use_few_shot: 是否使用 Few-Shot 示例
            provider: LLM 提供商
        """
        self.cfg = load_config()
        self.max_iterations = max_iterations
        self.provider = provider
        
        # 初始化组件
        self.skill_manager = get_skill_manager()
        self.scratchpad = MemoryScratchpad()
        self.output_parser = OutputParser(mode=output_format)
        
        # 获取工具列表
        self.tools = self._get_tools_list()
        
        # 初始化 PromptEngine
        self.prompt_engine = PromptEngine(
            tools=self.tools,
            use_few_shot=use_few_shot
        )
        
        logger.info(f"[ReActAgent] Initialized with max_iterations={max_iterations}, provider={provider}")
    
    def _get_tools_list(self) -> List[Dict[str, Any]]:
        """从 SkillManager 获取工具列表"""
        skills = self.skill_manager.list_skills()
        tools = []
        for skill in skills:
            tools.append({
                "name": skill["name"],
                "description": skill["description"]
            })
        logger.debug(f"[ReActAgent] Loaded {len(tools)} tools")
        return tools
    
    def _is_output_complete(self, llm_output: str) -> bool:
        """
        检查模型输出是否完整
        
        Args:
            llm_output: 模型输出
            
        Returns:
            是否完整
        """
        if not llm_output or len(llm_output.strip()) < 5:
            logger.warning("[ReActAgent] Output too short, considered incomplete")
            return False
        
        # 检查是否有合理的结束标记
        final_answer_patterns = [
            r'Final Answer\s*:',
            r'final_answer\s*":',
            r'"is_final_answer"\s*:\s*true',
        ]
        
        for pattern in final_answer_patterns:
            if re.search(pattern, llm_output, re.IGNORECASE):
                return True
        
        # 如果不是最终答案，检查是否有有效的思考和行动
        thought_patterns = [
            r'Thought\s*:',
            r'"thought"\s*":',
        ]
        
        has_thought = any(re.search(pattern, llm_output, re.IGNORECASE) for pattern in thought_patterns)
        
        if has_thought:
            return True
        
        # 至少要有一定的长度才认为有效
        return len(llm_output) > 50
    
    def _should_force_final_answer(self, parsed: Dict[str, Any]) -> bool:
        """
        判断是否应该强制给出最终答案（解决思考滞留问题）
        
        Args:
            parsed: 解析后的输出
            
        Returns:
            是否应该强制最终答案
        """
        # 如果已经有最终答案标志，不需要强制
        if parsed.get("is_final_answer"):
            return False
        
        # 如果有 final_answer 内容，即使没有标志，也认为是最终答案
        if parsed.get("final_answer") and len(str(parsed.get("final_answer")).strip()) > 10:
            logger.info("[ReActAgent] Found final_answer content, forcing final answer")
            return True
        
        # 检查 thought 中是否有表明应该结束的关键词
        thought = parsed.get("thought", "").lower()
        end_keywords = [
            "我现在知道最终答案了",
            "我可以给出答案了",
            "我不需要调用工具",
            "直接回答",
            "我已经有足够的信息",
            "基于现有结果",
            "我应该基于现有",
            "我将基于现有",
            "enough information",
            "no tool needed",
            "can answer directly",
            "final answer",
            "最终答案"
        ]
        
        for keyword in end_keywords:
            if keyword in thought:
                logger.info(f"[ReActAgent] Detected end keyword: '{keyword}', forcing final answer")
                return True
        
        # 如果没有 action，而且 thought 比较长，可能是在思考最终答案
        if not parsed.get("action") and len(thought) > 50:
            # 检查是否有提到"回答"、"给出"等词汇
            answer_hints = ["回答", "给出", "根据", "以下", "总结"]
            if any(hint in thought for hint in answer_hints):
                logger.info("[ReActAgent] Detected answer hint without action, forcing final answer")
                return True
        
        return False
    
    def _extract_final_answer_from_thought(self, thought: str, parsed: Dict[str, Any] = None) -> str:
        """
        从 Thought 中提取可能的最终答案
        
        Args:
            thought: 思考内容
            parsed: 解析后的完整输出
            
        Returns:
            提取的答案
        """
        # 优先使用 parsed 中的 final_answer
        if parsed and parsed.get("final_answer"):
            final_answer = str(parsed.get("final_answer")).strip()
            if len(final_answer) > 10:
                logger.info("[ReActAgent] Using final_answer from parsed output")
                return final_answer
        
        # 尝试找到"我现在知道最终答案了"之后的内容
        final_answer_markers = [
            r"我现在知道最终答案了[。，:：]?\s*(.*?)(?:$)",
            r"我应该基于现有[。，:：]?\s*(.*?)(?:$)",
            r"我将基于现有[。，:：]?\s*(.*?)(?:$)",
            r"基于现有结果[。，:：]?\s*(.*?)(?:$)",
            r"final answer[。，:：]?\s*(.*?)(?:$)",
            r"最终答案[。，:：]?\s*(.*?)(?:$)",
        ]
        
        for pattern in final_answer_markers:
            match = re.search(pattern, thought, re.DOTALL | re.IGNORECASE)
            if match and match.group(1).strip():
                extracted = match.group(1).strip()
                logger.info(f"[ReActAgent] Extracted final answer from thought (pattern: {pattern[:30]}...)")
                return extracted
        
        # 如果没有找到明确的标记，就用整个 thought
        logger.warning("[ReActAgent] No final answer marker found, using full thought")
        return thought
    
    def _get_skill_metadata(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        获取技能元数据，用于动态参数选择
        
        Args:
            skill_name: 技能名称
            
        Returns:
            技能元数据
        """
        try:
            skills = self.skill_manager.list_skills()
            for skill in skills:
                if skill["name"] == skill_name:
                    return skill
            return None
        except Exception as e:
            logger.warning(f"[ReActAgent] Failed to get skill metadata: {e}")
            return None
    
    def _validate_and_complete_params(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并补全技能参数（开放参数，允许模型自由填充）
        
        Args:
            action: 技能名称
            params: 当前参数（模型传递的所有参数）
            
        Returns:
            验证和补全后的参数（保留模型传递的所有参数）
        """
        if not action:
            return {}
        
        # 确保 params 是字典类型
        if not params:
            validated_params = {}
        elif isinstance(params, str):
            # 如果是字符串，尝试解析为字典，或者创建默认字典
            validated_params = {}
            logger.warning(f"[ReActAgent] Params was string, converting to dict: {params}")
        else:
            validated_params = params.copy()
        
        # 处理特定技能的参数名映射和默认值（仅在完全缺失时添加）
        if action == "arxiv-watcher":
            # 参数名映射：支持模型传递的各种参数名
            # search_query -> query
            if "search_query" in validated_params and "query" not in validated_params:
                validated_params["query"] = validated_params["search_query"]
            
            # max_results -> count
            if "max_results" in validated_params and "count" not in validated_params:
                try:
                    validated_params["count"] = int(validated_params["max_results"])
                except (ValueError, TypeError):
                    pass
            
            # 仅在完全缺失时添加默认值
            if "query" not in validated_params:
                validated_params["query"] = ""
            if "count" not in validated_params:
                validated_params["count"] = 5
            elif not isinstance(validated_params["count"], int):
                try:
                    validated_params["count"] = int(validated_params["count"])
                except (ValueError, TypeError):
                    validated_params["count"] = 5
        
        elif action == "amap-weather":
            if "city" not in validated_params:
                validated_params["city"] = "宁波"
        
        logger.debug(f"[ReActAgent] Validated params for {action}: {validated_params}")
        logger.debug(f"[ReActAgent] Original model params: {params}")
        return validated_params
    
    def run(
        self,
        user_question: str,
        conversation_history: str = ""
    ) -> Dict[str, Any]:
        """
        执行 ReAct 循环（非流式）
        
        Args:
            user_question: 用户问题
            conversation_history: 对话历史
            
        Returns:
            最终结果，包含:
            - final_answer: 最终答案
            - steps: 执行步骤
            - success: 是否成功
        """
        logger.info(f"[ReActAgent] Running for question: {user_question[:50]}...")
        
        try:
            for iteration in range(self.max_iterations):
                logger.debug(f"[ReActAgent] Iteration {iteration + 1}/{self.max_iterations}")
                
                # 1. 构建 Prompt
                prompt = self.prompt_engine.build_prompt(
                    user_question=user_question,
                    scratchpad_text=self.scratchpad.get_scratchpad_text(),
                    conversation_history=conversation_history,
                    provider=self.provider
                )
                
                # 2. 调用 LLM（带重试机制）
                max_llm_retries = 2
                llm_output = ""
                parsed = None
                
                for retry in range(max_llm_retries + 1):
                    try:
                        llm_output = self._call_llm(prompt)
                        
                        # 检查输出完整性
                        if not self._is_output_complete(llm_output) and retry < max_llm_retries:
                            logger.warning(f"[ReActAgent] Output incomplete, retrying ({retry + 1}/{max_llm_retries})")
                            continue
                        
                        # 3. 解析输出
                        parsed = self.output_parser.parse(llm_output)
                        break
                    except Exception as e:
                        if retry < max_llm_retries:
                            logger.warning(f"[ReActAgent] LLM call or parse failed, retrying: {e}")
                        else:
                            logger.error(f"[ReActAgent] Max retries exceeded: {e}")
                            raise
                
                if not parsed:
                    raise ReActAgentError("Failed to get valid response from LLM")
                
                # 4. 检查是否是最终答案
                if parsed["is_final_answer"]:
                    logger.info("[ReActAgent] Got final answer")
                    self.scratchpad.add_step(thought=parsed["thought"])
                    return {
                        "final_answer": parsed["final_answer"],
                        "steps": self.scratchpad.get_steps(),
                        "success": True
                    }
                
                # 4.5 检查是否应该强制给出最终答案（解决思考滞留问题）
                if self._should_force_final_answer(parsed):
                    logger.info("[ReActAgent] Forcing final answer due to thought stall")
                    final_answer = self._extract_final_answer_from_thought(parsed["thought"], parsed)
                    self.scratchpad.add_step(thought=parsed["thought"])
                    return {
                        "final_answer": final_answer,
                        "steps": self.scratchpad.get_steps(),
                        "success": True
                    }
                
                # 5. 验证并补全技能参数（动态参数选择）
                action = parsed["action"]
                action_input = parsed["action_input"] or {}
                
                if action:
                    # 验证和补全参数
                    validated_input = self._validate_and_complete_params(action, action_input)
                    
                    try:
                        observation = self._execute_tool(action, validated_input)
                    except Exception as e:
                        observation = f"工具执行失败: {str(e)}"
                else:
                    observation = "未指定工具"
                
                # 6. 更新暂存器
                self.scratchpad.add_step(
                    thought=parsed["thought"],
                    action=action,
                    action_input=action_input,
                    observation=observation
                )
            
            # 达到最大迭代次数
            raise MaxIterationsReached(self.max_iterations)
            
        except MaxIterationsReached:
            return {
                "final_answer": "抱歉，由于思考步骤过多，我未能得出最终答案。",
                "steps": self.scratchpad.get_steps(),
                "success": False
            }
        except Exception as e:
            logger.error(f"[ReActAgent] Error: {e}", exc_info=True)
            return {
                "final_answer": f"执行过程中发生错误: {str(e)}",
                "steps": self.scratchpad.get_steps(),
                "success": False
            }
    
    def stream_run(
        self,
        user_question: str,
        conversation_history: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """
        执行 ReAct 循环（流式）
        
        Args:
            user_question: 用户问题
            conversation_history: 对话历史
            
        Yields:
            事件字典
        """
        logger.info(f"[ReActAgent] Stream running for question: {user_question[:50]}...")
        
        try:
            for iteration in range(self.max_iterations):
                yield {"type": "thinking", "iteration": iteration + 1, "total": self.max_iterations}
                
                # 1. 构建 Prompt
                prompt = self.prompt_engine.build_prompt(
                    user_question=user_question,
                    scratchpad_text=self.scratchpad.get_scratchpad_text(),
                    conversation_history=conversation_history,
                    provider=self.provider
                )
                
                # 2. 调用 LLM（带重试机制）
                max_llm_retries = 2
                llm_output = ""
                parsed = None
                
                for retry in range(max_llm_retries + 1):
                    try:
                        llm_output = self._call_llm(prompt)
                        
                        # 检查输出完整性
                        if not self._is_output_complete(llm_output) and retry < max_llm_retries:
                            logger.warning(f"[ReActAgent] Output incomplete, retrying ({retry + 1}/{max_llm_retries})")
                            continue
                        
                        # 3. 解析输出
                        parsed = self.output_parser.parse(llm_output)
                        break
                    except Exception as e:
                        if retry < max_llm_retries:
                            logger.warning(f"[ReActAgent] LLM call or parse failed, retrying: {e}")
                        else:
                            logger.error(f"[ReActAgent] Max retries exceeded: {e}")
                            raise
                
                if not parsed:
                    raise ReActAgentError("Failed to get valid response from LLM")
                
                yield {"type": "thought", "content": parsed["thought"]}
                
                # 4. 检查是否是最终答案
                if parsed["is_final_answer"]:
                    logger.info("[ReActAgent] Got final answer")
                    self.scratchpad.add_step(thought=parsed["thought"])
                    yield {"type": "final_answer", "content": parsed["final_answer"]}
                    yield {
                        "type": "done",
                        "final_answer": parsed["final_answer"],
                        "steps": self.scratchpad.get_steps(),
                        "success": True
                    }
                    return
                
                # 4.5 检查是否应该强制给出最终答案（解决思考滞留问题）
                if self._should_force_final_answer(parsed):
                    logger.info("[ReActAgent] Forcing final answer due to thought stall")
                    final_answer = self._extract_final_answer_from_thought(parsed["thought"], parsed)
                    self.scratchpad.add_step(thought=parsed["thought"])
                    yield {"type": "final_answer", "content": final_answer}
                    yield {
                        "type": "done",
                        "final_answer": final_answer,
                        "steps": self.scratchpad.get_steps(),
                        "success": True
                    }
                    return
                
                # 5. 验证并补全技能参数（动态参数选择）
                action = parsed["action"]
                action_input = parsed["action_input"] or {}
                
                if action:
                    # 验证和补全参数
                    validated_input = self._validate_and_complete_params(action, action_input)
                    
                    yield {"type": "action", "name": action, "input": validated_input}
                    
                    try:
                        observation = self._execute_tool(action, validated_input)
                    except Exception as e:
                        observation = f"工具执行失败: {str(e)}"
                else:
                    observation = "未指定工具"
                
                yield {"type": "observation", "content": observation}
                
                # 6. 更新暂存器
                self.scratchpad.add_step(
                    thought=parsed["thought"],
                    action=action,
                    action_input=action_input,
                    observation=observation
                )
            
            # 达到最大迭代次数
            raise MaxIterationsReached(self.max_iterations)
            
        except MaxIterationsReached:
            yield {
                "type": "error",
                "message": "达到最大迭代次数"
            }
            yield {
                "type": "done",
                "final_answer": "抱歉，由于思考步骤过多，我未能得出最终答案。",
                "steps": self.scratchpad.get_steps(),
                "success": False
            }
        except Exception as e:
            logger.error(f"[ReActAgent] Error: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": str(e)
            }
            yield {
                "type": "done",
                "final_answer": f"执行过程中发生错误: {str(e)}",
                "steps": self.scratchpad.get_steps(),
                "success": False
            }
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM（非流式）
        
        Args:
            prompt: 提示词
            
        Returns:
            LLM 输出
        """
        import requests
        from openai import OpenAI
        
        try:
            from ollama import chat
            OLLAMA_SDK_AVAILABLE = True
        except ImportError:
            OLLAMA_SDK_AVAILABLE = False
        
        logger.debug(f"[ReActAgent] Calling LLM with prompt length: {len(prompt)}")
        
        temp = 0.1
        tp = 0.9
        mt = 1024
        
        if self.provider == "ollama":
            try:
                if OLLAMA_SDK_AVAILABLE:
                    logger.debug(f"[ReActAgent] Using Ollama SDK with model: {self.cfg.get('ollama_model')}")
                    response = chat(
                        model=self.cfg.get('ollama_model'),
                        messages=[{'role': 'user', 'content': prompt}],
                        options={
                            "temperature": temp,
                            "top_p": tp,
                            "top_k": self.cfg.get("top_k", 5),
                            "num_predict": mt
                        },
                        stream=False
                    )
                    return response.message.content.strip()
                else:
                    logger.debug(f"[ReActAgent] Ollama SDK not available, falling back to HTTP request")
                    endpoint = self.cfg.get("ollama_url").rstrip("/") + "/api/generate"
                    r = requests.post(
                        endpoint,
                        json={
                            "model": self.cfg.get("ollama_model"),
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": temp,
                                "top_p": tp,
                                "top_k": self.cfg.get("top_k", 5),
                                "num_predict": mt
                            }
                        },
                        timeout=60
                    )
                    r.raise_for_status()
                    return r.json().get("response", "")
            except Exception as e:
                logger.error(f"[ReActAgent] Ollama call failed: {e}", exc_info=True)
                raise ReActAgentError(f"Ollama call failed: {e}")
        else:
            try:
                key = self.cfg.get("openai_api_key")
                base_url = self.cfg.get("openai_base_url")
                client_kwargs = {}
                if key:
                    client_kwargs["api_key"] = key
                if base_url:
                    client_kwargs["base_url"] = base_url
                
                client = OpenAI(**client_kwargs)
                completion = client.chat.completions.create(
                    model=self.cfg.get("openai_chat_model", "gpt-3.5-turbo"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=mt,
                    temperature=temp,
                    top_p=tp
                )
                if (
                    completion.choices
                    and len(completion.choices) > 0
                    and completion.choices[0].message
                    and completion.choices[0].message.content
                ):
                    return completion.choices[0].message.content.strip()
                else:
                    raise ReActAgentError("LLM returned empty response")
            except Exception as e:
                logger.error(f"[ReActAgent] OpenAI call failed: {e}", exc_info=True)
                raise ReActAgentError(f"OpenAI call failed: {e}")
    
    def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            工具执行结果（字符串格式）
        """
        logger.info(f"[ReActAgent] Executing tool: {tool_name}, params: {params}")
        
        # 验证工具存在
        available_tools = [t["name"] for t in self.tools]
        if tool_name not in available_tools:
            raise ToolNotFoundError(tool_name)
        
        # 执行工具
        result = self.skill_manager.execute_skill(tool_name, **params)
        
        # 格式化结果
        formatted = self.skill_manager.format_skill_result(result)
        
        logger.debug(f"[ReActAgent] Tool result: {formatted[:200]}...")
        return formatted
    
    def reset(self) -> None:
        """重置 Agent 状态"""
        self.scratchpad.clear()
        logger.debug("[ReActAgent] Reset")
