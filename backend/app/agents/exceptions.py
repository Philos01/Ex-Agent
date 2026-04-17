"""
ReAct Agent 自定义异常类
"""
import logging

logger = logging.getLogger(__name__)


class ReActAgentError(Exception):
    """ReAct Agent 基础异常类"""
    
    def __init__(self, message: str):
        super().__init__(message)
        logger.error(f"[ReActAgentError] {message}")


class OutputParseError(ReActAgentError):
    """LLM 输出解析错误"""
    
    def __init__(self, message: str, raw_output: str = None):
        super().__init__(message)
        self.raw_output = raw_output
        if raw_output:
            logger.debug(f"[OutputParseError] Raw output: {raw_output[:200]}...")


class MaxIterationsReached(ReActAgentError):
    """达到最大迭代次数"""
    
    def __init__(self, max_iterations: int):
        super().__init__(f"Reached maximum iterations: {max_iterations}")
        self.max_iterations = max_iterations


class ToolNotFoundError(ReActAgentError):
    """工具未找到"""
    
    def __init__(self, tool_name: str):
        super().__init__(f"Tool not found: {tool_name}")
        self.tool_name = tool_name


class ToolExecutionError(ReActAgentError):
    """工具执行错误"""
    
    def __init__(self, tool_name: str, error: str):
        super().__init__(f"Tool '{tool_name}' execution failed: {error}")
        self.tool_name = tool_name
        self.error = error
