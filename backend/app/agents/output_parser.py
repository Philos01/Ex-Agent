"""
Output Parser - 结构化输出解析器
支持 JSON 和文本两种模式
"""
import logging
import json
import re
from typing import Dict, Any, Optional
from app.agents.exceptions import OutputParseError

logger = logging.getLogger(__name__)


class OutputParser:
    """
    LLM 输出解析器
    
    支持两种模式:
    - JSON 模式（推荐）: 解析 JSON 格式的输出
    - 文本模式: 使用正则表达式解析文本格式
    """
    
    def __init__(self, mode: str = "json"):
        """
        初始化解析器
        
        Args:
            mode: 解析模式，"json" 或 "text"
        """
        self.mode = mode.lower()
        if self.mode not in ["json", "text"]:
            self.mode = "json"
        logger.debug(f"[OutputParser] Initialized with mode: {self.mode}")
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        解析 LLM 输出
        
        Args:
            text: LLM 输出文本
            
        Returns:
            解析后的字典，包含以下字段:
            - thought: 思考内容
            - action: 行动名称（或 None）
            - action_input: 行动参数（或 None）
            - is_final_answer: 是否为最终答案
            - final_answer: 最终答案内容（或 None）
            
        Raises:
            OutputParseError: 当解析失败时
        """
        logger.debug(f"[OutputParser] Parsing output (mode={self.mode}): {text[:100]}...")
        
        if self.mode == "json":
            try:
                return self._parse_json(text)
            except OutputParseError:
                logger.warning("[OutputParser] JSON parse failed, falling back to text mode")
                return self._parse_text(text)
        else:
            return self._parse_text(text)
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """
        解析 JSON 格式的输出
        
        Args:
            text: 包含 JSON 的文本
            
        Returns:
            解析后的字典
        """
        # 尝试提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # 如果没有代码块，尝试直接解析整个文本
            json_str = text.strip()
        
        try:
            result = json.loads(json_str)
            return self._normalize_result(result)
        except json.JSONDecodeError as e:
            logger.warning(f"[OutputParser] JSON parse failed: {e}")
            raise OutputParseError(f"Failed to parse JSON: {e}", raw_output=text)
    
    def _parse_text(self, text: str) -> Dict[str, Any]:
        """
        解析文本格式的输出（使用正则表达式）
        
        Args:
            text: 文本格式的输出
            
        Returns:
            解析后的字典
        """
        result = {
            "thought": "",
            "action": None,
            "action_input": None,
            "is_final_answer": False,
            "final_answer": None
        }
        
        # 提取 Thought
        thought_match = re.search(r'Thought:\s*(.*?)(?=\n\w+:|$)', text, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        
        # 检查是否是最终答案
        final_answer_match = re.search(r'Final Answer:\s*(.*)', text, re.DOTALL)
        if final_answer_match:
            result["is_final_answer"] = True
            result["final_answer"] = final_answer_match.group(1).strip()
            return result
        
        # 提取 Action
        action_match = re.search(r'Action:\s*(.*?)(?=\n|$)', text)
        if action_match:
            action = action_match.group(1).strip()
            if action.lower() != "null" and action.lower() != "none":
                result["action"] = action
        
        # 提取 Action Input
        action_input_match = re.search(r'Action Input:\s*(.*?)(?=\n\w+:|$)', text, re.DOTALL)
        if action_input_match:
            input_str = action_input_match.group(1).strip()
            try:
                result["action_input"] = json.loads(input_str)
            except json.JSONDecodeError:
                # 如果不是 JSON，就作为字符串
                result["action_input"] = input_str
        
        # 如果没有 Thought，尝试使用整个文本作为 Thought
        if not result["thought"] and not result["is_final_answer"]:
            result["thought"] = text.strip()
        
        return result
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化解析结果
        
        Args:
            result: 原始解析结果
            
        Returns:
            标准化后的结果
        """
        normalized = {
            "thought": result.get("thought", ""),
            "action": result.get("action"),
            "action_input": result.get("action_input"),
            "is_final_answer": bool(result.get("is_final_answer", False)),
            "final_answer": result.get("final_answer")
        }
        
        # 处理 action 为 "null" 或 "none" 的情况
        if normalized["action"] in ["null", "none", "None", None]:
            normalized["action"] = None
        
        # 确保 action_input 是字典或 None
        if normalized["action_input"] in ["null", "none", "None"]:
            normalized["action_input"] = None
        
        logger.debug(f"[OutputParser] Normalized result: {normalized}")
        return normalized
