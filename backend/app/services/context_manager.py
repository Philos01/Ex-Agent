"""
上下文历史管理服务
管理对话历史，包括轮次控制、错误内容筛选和上下文污染检测
"""
import logging
import re
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
import threading

logger = logging.getLogger(__name__)


class MessageQuality(Enum):
    """消息质量枚举"""
    GOOD = "good"
    QUESTIONABLE = "questionable"
    BAD = "bad"


@dataclass
class ContextMessage:
    """上下文消息"""
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: str
    quality: MessageQuality = MessageQuality.GOOD
    is_error: bool = False
    error_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["quality"] = self.quality.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextMessage':
        """从字典创建"""
        quality_str = data.get("quality", "good")
        try:
            quality = MessageQuality(quality_str)
        except ValueError:
            quality = MessageQuality.GOOD
        
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
            quality=quality,
            is_error=data.get("is_error", False),
            error_reason=data.get("error_reason")
        )


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self.history: List[ContextMessage] = []
        
        # 错误内容检测关键词
        self.error_keywords = [
            "抱歉", "对不起", "无法", "不能", "错误", "失败", 
            "不知道", "不清楚", "没有找到", "无法回答", 
            "连接失败", "网络错误", "API错误"
        ]
        
        # 上下文污染检测模式
        self.contamination_patterns = [
            r"根据提供的检索内容，暂时无法找到",
            r"根据我的专业知识范围",
            r"资料里提到",
            r"资料未提及"
        ]
    
    def add_message(
        self, 
        role: str, 
        content: str, 
        timestamp: Optional[str] = None
    ) -> ContextMessage:
        """
        添加消息到历史
        
        Args:
            role: 角色（"user" 或 "assistant"）
            content: 消息内容
            timestamp: 时间戳
            
        Returns:
            创建的ContextMessage对象
        """
        import datetime
        
        if timestamp is None:
            timestamp = datetime.datetime.utcnow().isoformat()
        
        # 评估消息质量
        quality, is_error, error_reason = self._assess_message_quality(role, content)
        
        message = ContextMessage(
            role=role,
            content=content,
            timestamp=timestamp,
            quality=quality,
            is_error=is_error,
            error_reason=error_reason
        )
        
        self.history.append(message)
        
        # 保持历史长度
        self._trim_history()
        
        logger.debug(f"添加消息到历史: role={role}, quality={quality.value}, is_error={is_error}")
        
        return message
    
    def get_filtered_history(
        self, 
        exclude_errors: bool = True,
        exclude_questionable: bool = False,
        max_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取过滤后的历史记录
        
        Args:
            exclude_errors: 是否排除错误消息
            exclude_questionable: 是否排除可疑消息
            max_count: 最大返回数量
            
        Returns:
            过滤后的消息列表
        """
        filtered = []
        
        for msg in self.history:
            if exclude_errors and msg.is_error:
                continue
            if exclude_questionable and msg.quality == MessageQuality.QUESTIONABLE:
                continue
            filtered.append(msg)
        
        # 限制数量
        if max_count is None:
            max_count = self.max_history
        
        # 只保留最近的N轮对话（user-assistant为一轮）
        return self._extract_recent_conversations(filtered, max_count)
    
    def _extract_recent_conversations(
        self, 
        messages: List[ContextMessage], 
        max_rounds: int
    ) -> List[Dict[str, Any]]:
        """
        提取最近的对话轮次
        
        Args:
            messages: 消息列表
            max_rounds: 最大轮次
            
        Returns:
            格式化的消息列表
        """
        if not messages:
            return []
        
        result = []
        rounds_found = 0
        i = len(messages) - 1
        
        # 从后往前查找完整的对话轮次
        while i >= 0 and rounds_found < max_rounds:
            msg = messages[i]
            
            if msg.role == "assistant":
                # 找到一个assistant消息，往前找对应的user消息
                result.insert(0, msg.to_dict())
                
                # 往前找user消息
                j = i - 1
                while j >= 0:
                    if messages[j].role == "user":
                        result.insert(0, messages[j].to_dict())
                        rounds_found += 1
                        i = j - 1
                        break
                    j -= 1
                else:
                    # 没有找到对应的user消息，只保留assistant
                    i = j
            else:
                # user消息，直接添加
                result.insert(0, msg.to_dict())
                i -= 1
        
        # 如果没有找到完整轮次，返回所有消息
        if not result:
            return [m.to_dict() for m in messages[-max_rounds*2:]]
        
        return result
    
    def _assess_message_quality(
        self, 
        role: str, 
        content: str
    ) -> tuple[MessageQuality, bool, Optional[str]]:
        """
        评估消息质量
        
        Args:
            role: 角色
            content: 内容
            
        Returns:
            (质量等级, 是否错误, 错误原因)
        """
        quality = MessageQuality.GOOD
        is_error = False
        error_reason = None
        
        if role != "assistant":
            return quality, is_error, error_reason
        
        # 检查错误关键词
        error_count = 0
        for keyword in self.error_keywords:
            if keyword in content:
                error_count += 1
        
        if error_count >= 2:
            quality = MessageQuality.BAD
            is_error = True
            error_reason = "包含多个错误关键词"
        elif error_count == 1:
            quality = MessageQuality.QUESTIONABLE
        
        # 检查上下文污染模式
        contamination_count = 0
        for pattern in self.contamination_patterns:
            if re.search(pattern, content):
                contamination_count += 1
        
        if contamination_count >= 1:
            quality = MessageQuality.QUESTIONABLE
            if not is_error:
                error_reason = "检测到上下文污染模式"
        
        return quality, is_error, error_reason
    
    def _trim_history(self):
        """修剪历史记录，保持合理长度"""
        # 保留最多 max_history * 2 条消息（每轮2条）
        max_messages = self.max_history * 4
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]
            logger.debug(f"历史记录已修剪，保留 {len(self.history)} 条消息")
    
    def clear_history(self):
        """清空历史"""
        self.history = []
        logger.info("上下文历史已清空")
    
    def get_history_stats(self) -> Dict[str, Any]:
        """
        获取历史统计信息
        
        Returns:
            统计信息字典
        """
        total = len(self.history)
        good_count = sum(1 for m in self.history if m.quality == MessageQuality.GOOD)
        questionable_count = sum(1 for m in self.history if m.quality == MessageQuality.QUESTIONABLE)
        bad_count = sum(1 for m in self.history if m.quality == MessageQuality.BAD)
        error_count = sum(1 for m in self.history if m.is_error)
        
        return {
            "total_messages": total,
            "good_count": good_count,
            "questionable_count": questionable_count,
            "bad_count": bad_count,
            "error_count": error_count,
            "max_history": self.max_history
        }
    
    def save_to_file(self, filepath: str):
        """保存历史到文件"""
        try:
            data = {
                "max_history": self.max_history,
                "history": [m.to_dict() for m in self.history]
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"上下文历史已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存历史失败: {e}")
    
    def load_from_file(self, filepath: str):
        """从文件加载历史"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.max_history = data.get("max_history", 5)
            self.history = [ContextMessage.from_dict(m) for m in data.get("history", [])]
            
            logger.info(f"上下文历史已从文件加载: {filepath}")
        except Exception as e:
            logger.error(f"加载历史失败: {e}")


# 全局上下文管理器实例
_context_managers: Dict[str, ContextManager] = {}
_context_managers_lock = threading.Lock()
_context_managers_timestamps: Dict[str, float] = {}
_MAX_CONTEXT_MANAGERS = 100
_CONTEXT_TTL_SECONDS = 3600


def _evict_expired_contexts():
    """Evict expired context managers based on TTL"""
    now = time.time()
    expired = [
        sid for sid, ts in _context_managers_timestamps.items()
        if now - ts > _CONTEXT_TTL_SECONDS
    ]
    for sid in expired:
        del _context_managers[sid]
        del _context_managers_timestamps[sid]
        logger.info(f"已淘汰过期上下文管理器: {sid}")


def get_context_manager(session_id: str = "default", max_history: int = 5) -> ContextManager:
    with _context_managers_lock:
        _evict_expired_contexts()
        if session_id not in _context_managers:
            if len(_context_managers) >= _MAX_CONTEXT_MANAGERS:
                oldest_sid = min(_context_managers_timestamps, key=_context_managers_timestamps.get)
                del _context_managers[oldest_sid]
                del _context_managers_timestamps[oldest_sid]
                logger.info(f"已淘汰最旧上下文管理器: {oldest_sid}")
            _context_managers[session_id] = ContextManager(max_history=max_history)
        _context_managers_timestamps[session_id] = time.time()
        return _context_managers[session_id]


def clear_context_manager(session_id: str = "default"):
    """
    清除指定会话的上下文管理器
    
    Args:
        session_id: 会话ID
    """
    if session_id in _context_managers:
        del _context_managers[session_id]
        logger.info(f"上下文管理器已清除: {session_id}")
