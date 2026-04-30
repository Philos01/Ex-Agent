
"""
查询改写 (Query Rewrite) 服务模块
使用大模型优化用户查询，提升检索效果
"""
import logging
from typing import Optional
from app.core.config import get_complete_config
from openai import OpenAI
import requests
import json

logger = logging.getLogger(__name__)


class QueryRewriteService:
    """查询改写服务"""
    
    def __init__(self):
        self.cfg = get_complete_config()
    
    def rewrite_query(self, query: str, provider: str = None, use_summary_config: bool = False) -> str:
        """
        改写用户查询
        
        Args:
            query: 原始查询
            provider: LLM 提供商，默认使用配置中的
            use_summary_config: 是否使用摘要检索配置而不是混合检索配置
            
        Returns:
            改写后的查询
        """
        cfg = get_complete_config()
        provider = provider or cfg.get("provider", "openai")
        
        # 检查是否启用查询改写（根据配置来源）
        if use_summary_config:
            summary_config = cfg.get("summary_search", {})
            enabled = summary_config.get("enable_query_rewrite", True)
        else:
            hybrid_config = cfg.get("hybrid_search", {})
            enabled = hybrid_config.get("enable_query_rewrite", True)
        
        if not enabled:
            logger.info("查询改写未启用，返回原始查询")
            return query
        
        # 构建改写提示
        system_prompt = """你是一个专业的查询优化助手，专门用于改进检索系统的查询效果。

你的任务是将用户的原始查询改写为更适合检索系统的查询，遵循以下原则：
1. 保持原始查询的核心意图不变
2. 补充相关的关键词和专业术语（如果适用）
3. 将口语化表达转换为更正式的书面表达
4. 拆分复杂问题为更清晰的检索关键词组合
5. 对于中文查询，考虑中英文关键词结合（如专业术语）
6. 保持查询简洁，不要过长

请直接输出改写后的查询，不要包含任何额外的说明或解释。"""

        user_prompt = f"请改写以下查询，使其更适合检索系统,只输出结果即可，不要输出其他任何内容：\n\n{query}"
                
        try:
            if provider == "ollama":
                result = self._rewrite_with_ollama(cfg, system_prompt, user_prompt, query)
            else:
                result = self._rewrite_with_openai(cfg, system_prompt, user_prompt, query)
            
            # 检查改写结果是否为空，如果是则返回原始查询
            if not result or not result.strip():
                logger.warning(f"查询改写返回空结果，使用原始查询: '{query}'")
                return query
            
            logger.info(f"[DEBUG] 查询改写返回: '{result}'")
            return result
        
        except Exception as e:
            logger.error(f"查询改写失败: {e}")
            return query
    
    def _rewrite_with_openai(self, cfg, system_prompt: str, user_prompt: str, original_query: str) -> str:
        """使用 OpenAI 风格 API 改写查询"""
        try:
            key = cfg.get("openai_api_key")
            base_url = cfg.get("openai_base_url")
            
            client_kwargs = {}
            if key:
                client_kwargs["api_key"] = key
            if base_url:
                client_kwargs["base_url"] = base_url
            
            client = OpenAI(**client_kwargs)
            
            completion = client.chat.completions.create(
                model=cfg.get("openai_chat_model", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=256,
                temperature=0.7,
            )
            
            if (
                completion.choices 
                and len(completion.choices) > 0 
                and completion.choices[0].message 
                and completion.choices[0].message.content
            ):
                rewritten = completion.choices[0].message.content.strip()
                logger.info(f"查询改写成功: '{original_query}' -> '{rewritten}'")
                return rewritten
            
            return original_query
            
        except Exception as e:
            logger.error(f"OpenAI 查询改写失败: {e}")
            return original_query
    
    def _rewrite_with_ollama(self, cfg, system_prompt: str, user_prompt: str, original_query: str) -> str:
        """使用 Ollama 改写查询"""
        from ollama import chat  # 确保在需要时才导入 Ollama SDK
        try:
            response = chat(
                              model="qwen3:4b-instruct",  # 可以从配置中获取模型名称
                              messages=[
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": user_prompt}
                                        ],
                              think=cfg.get("enable_thinking", False),
                              stream=False,
                            )
            # endpoint = cfg.get("ollama_url", "http://localhost:11434").rstrip("/") + "/api/chat"
            # print(f"[DEBUG] Ollama endpoint: {endpoint}")
            # response = requests.post(
            #     endpoint,
            #     json={
            #         "model": cfg.get("ollama_model", "llama2"),
            #         "messages": [
            #             {"role": "system", "content": system_prompt},
            #             {"role": "user", "content": user_prompt}
            #         ],
            #         "think": False, 
            #         "stream": False,
            #         "options": {
            #             "temperature": 0.7
            #         }
            #     },
            #     timeout=30
            # )
            # 正确访问 response 对象的属性
            if hasattr(response, "message") and hasattr(response.message, "content"):
                rewritten = response.message.content.strip()
                logger.debug("Rewritten query: %s", rewritten)
                logger.info(f"查询改写成功: '{original_query}' -> '{rewritten}'")
                return rewritten
            
            return original_query
            
        except Exception as e:
            logger.error(f"Ollama 查询改写失败: {e}")
            return original_query


# 全局查询改写服务实例
_query_rewrite_service = None


def get_query_rewrite_service() -> QueryRewriteService:
    """
    获取或创建全局查询改写服务实例
    
    Returns:
        QueryRewriteService 实例
    """
    global _query_rewrite_service
    if _query_rewrite_service is None:
        _query_rewrite_service = QueryRewriteService()
    return _query_rewrite_service

