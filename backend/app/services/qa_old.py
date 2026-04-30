
"""
Question-answer logic: retrieve and call LLM

该文件已重构为模块化架构，保持向后兼容性
所有功能委托给 app.services.qa 模块中的协调器
"""

import logging
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


def _get_coordinator():
    """获取QA协调器实例"""
    from app.core.config import get_complete_config
    from app.services.qa import QACoordinator
    config = get_complete_config()
    return QACoordinator(config)


def answer_question(question: str, provider: str = "openai",
                   top_k: int = 5, session_id: str = "default") -&gt; Tuple[str, List[Dict[str, Any]]]:
    """
    回答用户问题 - 向后兼容接口

    该函数已重构，将工作委托给 QACoordinator
    """
    logger.info("[qa.py] answer_question (backward compatible)")
    coordinator = _get_coordinator()
    return coordinator.answer_question(question, provider, top_k, session_id)


def stream_answer(question: str, provider: str = "openai",
                 top_k: int = 5, temperature: float = None,
                 top_p: float = None, max_tokens: int = None,
                 presence_penalty: float = None, frequency_penalty: float = None,
                 enable_thinking: bool = None, use_react: bool = None,
                 messages: List[Dict[str, Any]] = None, include_state: bool = False,
                 use_skill: bool = None, skill_name: str = None,
                 skill_params: dict = None):
    """
    流式回答问题 - 向后兼容接口

    该函数已重构，将工作委托给 QACoordinator
    """
    logger.info("[qa.py] stream_answer (backward compatible)")
    coordinator = _get_coordinator()
    return coordinator.stream_answer(
        question, provider, top_k, temperature, top_p, max_tokens,
        presence_penalty, frequency_penalty, enable_thinking, use_react,
        messages, include_state, use_skill, skill_name, skill_params
    )


def _retrieve_documents(question: str, provider: str = "openai", top_k: int = 5):
    """
    检索文档 - 向后兼容接口

    该函数已重构，将工作委托给 RetrievalStrategy
    """
    from app.core.config import get_complete_config
    from app.services.qa import RetrievalStrategyFactory
    config = get_complete_config()
    strategy = RetrievalStrategyFactory.create(config)
    return strategy.retrieve(question, provider, top_k)


def _format_conversation_history(messages: list):
    """
    格式化对话历史 - 向后兼容接口

    该函数已重构，将工作委托给 HistoryFormatter
    """
    from app.services.qa import HistoryFormatter
    formatter = HistoryFormatter()
    return formatter.format(messages)


def _build_knowledge_base_overview():
    """
    构建知识库概览 - 向后兼容接口

    该函数已重构，将工作委托给 KnowledgeBuilder
    """
    from app.services.qa import KnowledgeBuilder
    builder = KnowledgeBuilder()
    return builder.build_overview()


def regularize_output(text: str):
    """
    正则化输出 - 向后兼容接口

    该函数已重构，将工作委托给 OutputFormatter
    """
    from app.services.qa import OutputFormatter
    formatter = OutputFormatter()
    return formatter.format(text)


def _get_client_for_provider(cfg: dict, provider: str, enable_thinking: bool = False):
    """
    获取LLM客户端 - 向后兼容接口

    该函数已重构，建议使用 LLMClientFactory
    """
    from app.services.qa import LLMClientFactory
    client = LLMClientFactory.create(cfg, provider, enable_thinking)
    # 保持原有返回格式
    if provider == "ollama":
        return None, cfg.get("ollama_model", "")
    model_name = cfg.get("openai_chat_model", "gpt-3.5-turbo")
    if provider == "deepseek":
        model_name = cfg.get("deepseek_chat_model", "deepseek-chat")
    return client, model_name


def _get_openai_client(cfg):
    """获取OpenAI客户端 - 向后兼容接口"""
    from app.services.qa import LLMClientFactory
    return LLMClientFactory.create(cfg, "openai"), cfg.get("openai_chat_model", "gpt-3.5-turbo")


def _stream_answer_react(question: str, provider: str = "openai",
                        messages: List[Dict[str, Any]] = None, max_tokens: int = None,
                        enable_thinking: bool = False):
    """
    ReAct流式回答 - 向后兼容接口

    该函数已重构，将工作委托给 ReActAdapter
    """
    from app.core.config import get_complete_config
    from app.services.qa import ReActAdapter, HistoryFormatter
    config = get_complete_config()
    adapter = ReActAdapter(config, HistoryFormatter())
    return adapter.stream_answer(question, provider, messages, max_tokens, enable_thinking)


def _get_filtered_history(session_id: str = "default"):
    """
    获取过滤后的历史 - 向后兼容接口

    该函数已重构，使用新的上下文管理器
    """
    coordinator = _get_coordinator()
    return coordinator._get_filtered_history(session_id)


def _add_to_history(role: str, content: str, session_id: str = "default"):
    """
    添加消息到历史 - 向后兼容接口

    该函数已重构，使用新的上下文管理器
    """
    coordinator = _get_coordinator()
    return coordinator._add_to_history(role, content, session_id)

