"""
Memory & Scratchpad - 记忆与暂存器管理
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MemoryScratchpad:
    """
    Agent 暂存器 - 存储当前任务的"思考-行动-观察"链
    
    功能:
    - 记录每一轮的 Thought/Action/Action Input/Observation
    - 提供格式化的字符串输出，用于 Prompt 构建
    - 支持清空和重置
    """
    
    def __init__(self):
        self._steps: List[Dict[str, Any]] = []
        logger.debug("[MemoryScratchpad] Initialized")
    
    def add_step(
        self,
        thought: str,
        action: Optional[str] = None,
        action_input: Optional[Dict[str, Any]] = None,
        observation: Optional[str] = None
    ) -> None:
        """
        添加一个步骤到暂存器
        
        Args:
            thought: 思考内容
            action: 行动名称（可选）
            action_input: 行动参数（可选）
            observation: 观察结果（可选）
        """
        step = {
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation
        }
        self._steps.append(step)
        logger.debug(f"[MemoryScratchpad] Added step: thought={thought[:50]}...")
    
    def get_scratchpad_text(self) -> str:
        """
        获取格式化的暂存器文本，用于构建 Prompt
        
        Returns:
            格式化的暂存器字符串
        """
        if not self._steps:
            return ""
        
        lines = []
        for i, step in enumerate(self._steps, 1):
            lines.append(f"Thought: {step['thought']}")
            
            if step.get("action"):
                lines.append(f"Action: {step['action']}")
            
            if step.get("action_input"):
                import json
                lines.append(f"Action Input: {json.dumps(step['action_input'], ensure_ascii=False)}")
            
            if step.get("observation"):
                lines.append(f"Observation: {step['observation']}")
            
            if i < len(self._steps):
                lines.append("---")
        
        scratchpad_text = "\n".join(lines)
        logger.debug(f"[MemoryScratchpad] Scratchpad text generated ({len(scratchpad_text)} chars)")
        return scratchpad_text
    
    def get_steps(self) -> List[Dict[str, Any]]:
        """
        获取所有步骤（用于调试和前端展示）
        
        Returns:
            步骤列表
        """
        return self._steps.copy()
    
    def clear(self) -> None:
        """清空暂存器"""
        self._steps = []
        logger.debug("[MemoryScratchpad] Cleared")
    
    def __len__(self) -> int:
        """获取步骤数量"""
        return len(self._steps)
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.get_scratchpad_text()
