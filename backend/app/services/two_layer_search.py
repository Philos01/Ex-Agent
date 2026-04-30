"""
双层检索服务
先检索文件摘要，再根据相关性决定是否检索完整内容
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from app.core.config import load_config
from app.services.summary_store import get_summary_store
from app.services.vector_store import search as vector_search
from app.services.bm25_search import get_bm25_retriever
from app.services.hybrid_search import get_hybrid_search_service
from app.services.query_rewrite import get_query_rewrite_service

logger = logging.getLogger(__name__)


class TwoLayerRetriever:
    """双层检索器"""
    
    def __init__(self):
        self.cfg = load_config()
        self.summary_config = self.cfg.get("summary_search", {})
        self.relevance_threshold = self.summary_config.get("relevance_threshold", 0.6)
        self.summary_top_k = self.summary_config.get("summary_top_k", 5)
        self.content_top_k = self.summary_config.get("content_top_k", 3)
        self._summary_bm25 = None
        self._summary_bm25_hash = None
    
    def search(
        self, 
        query: str, 
        provider: str = "openai",
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        执行双层检索
        
        Args:
            query: 查询文本
            provider: LLM提供商
            use_hybrid: 是否使用混合检索
            
        Returns:
            检索结果列表
        """
        logger.debug("[TwoLayerRetriever.search] Called, query: '%s...'", query[:50])
        
        # 检查原始查询是否为空
        if not query or not query.strip():
            logger.error("Query is empty")
            return []
        
        logger.info("Two-layer search: query='%s'", query)
        
        # 1. 查询改写 - 在摘要检索前优化查询
        logger.debug("Rewriting query...")
        query_rewrite_service = get_query_rewrite_service()
        rewritten_query = query_rewrite_service.rewrite_query(query, provider=provider, use_summary_config=True)
        
        # 二次验证改写后的查询，如果为空则使用原始查询
        if not rewritten_query or not rewritten_query.strip():
            logger.warning("Rewritten query is empty, using original")
            rewritten_query = query
        
        # 第一层：检索摘要，找到相关文件（使用改写后的查询）
        summary_results = self._search_summaries(rewritten_query, provider)
        
        logger.debug("Summary search results: %s", summary_results)
        
        if not summary_results:
            logger.info("No summary results, searching full content directly")
            return self._search_full_content(rewritten_query, provider, use_hybrid)
        
        # 获取所有摘要检索到的文件名
        relevant_filenames = []
        for result in summary_results:
            metadata = result.get("metadata", {})
            filename = metadata.get("filename")
            if filename and filename not in relevant_filenames:
                relevant_filenames.append(filename)
        
        logger.info("Summary found %d relevant files: %s", len(relevant_filenames), relevant_filenames)
        
        # 第二层：在这些相关文件中检索正文内容（使用改写后的查询）
        logger.debug("Searching full content in relevant files...")
        try:
            from app.services.vector_store import search_by_filenames
            content_results = search_by_filenames(
                rewritten_query, 
                relevant_filenames, 
                top_k=self.content_top_k,
                provider=provider
            )
            
            if content_results:
                logger.info("Content search found %d results in relevant files", len(content_results))
                return content_results
            else:
                logger.info("No content found in relevant files, falling back to global search")
                return self._search_full_content(rewritten_query, provider, use_hybrid)
                
        except Exception as e:
            logger.error("Content search in relevant files failed, fallback to global: %s", e)
            return self._search_full_content(rewritten_query, provider, use_hybrid)
    
    def _search_summaries(self, query: str, provider: str = "openai") -> List[Dict[str, Any]]:
        """
        第一层：检索摘要

        Args:
            query: 查询文本
            provider: LLM提供商

        Returns:
            摘要检索结果，包含相关性分数
        """
        logger.debug("[_search_summaries] Starting, query: '%s...'", query[:50])
        store = get_summary_store()
        all_summaries = store.get_all_summaries()

        logger.debug("[_search_summaries] Got %d summaries", len(all_summaries))

        if not all_summaries:
            logger.info("No summaries available")
            return []

        logger.debug("Total %d summaries to search", len(all_summaries))

        try:
            current_hash = hash(tuple(s.filename for s in all_summaries))
            if self._summary_bm25 is None or self._summary_bm25_hash != current_hash:
                summary_texts = []
                summary_metas = []
                summary_ids = []
                for idx, summary in enumerate(all_summaries):
                    summary_text = f"标题: {summary.filename}\n"
                    summary_text += f"摘要: {summary.summary}\n"
                    summary_text += f"主题: {', '.join(summary.key_topics)}\n"
                    summary_text += f"要点: {', '.join(summary.key_points)}\n"
                    summary_text += f"结论: {', '.join(summary.main_conclusions)}\n"
                    summary_text += f"术语: {', '.join(summary.technical_terms)}\n"
                    if hasattr(summary, 'authors') and summary.authors:
                        summary_text += f"作者: {', '.join(summary.authors)}\n"
                    if hasattr(summary, 'publication_year') and summary.publication_year:
                        summary_text += f"发表年份: {summary.publication_year}\n"
                    if hasattr(summary, 'venue') and summary.venue:
                        summary_text += f"期刊/会议: {summary.venue}\n"

                    summary_texts.append(summary_text)
                    summary_metas.append({
                        "filename": summary.filename,
                        "summary": summary.summary,
                        "key_topics": summary.key_topics,
                        "quality_score": summary.quality_score,
                        "is_summary": True
                    })
                    summary_ids.append(str(uuid.uuid4()))

                from app.services.bm25_search import BM25Retriever
                self._summary_bm25 = BM25Retriever()
                self._summary_bm25._build_index(summary_texts, summary_metas, summary_ids)
                self._summary_bm25_hash = current_hash

            results = self._summary_bm25.search(query, top_k=self.summary_top_k)

            logger.debug("BM25 raw results: %s", results)

            filtered_results = []
            for result in results:
                score = result.get("score", 0.0)
                result["relevance_score"] = score
                if score >= self.relevance_threshold:
                    filtered_results.append(result)

            if len(filtered_results) < len(results):
                logger.info("Summary search: %d/%d passed relevance threshold (%.2f)", len(filtered_results), len(results), self.relevance_threshold)

            logger.info("Summary search completed, returning %d results", len(filtered_results))
            return filtered_results

        except Exception as e:
            logger.error("Summary search failed: %s", e, exc_info=True)
            return []
    
    def _search_full_content(
        self, 
        query: str, 
        provider: str = "openai",
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        第二层：检索完整内容
        
        Args:
            query: 查询文本（应该已经是改写后的查询）
            provider: LLM提供商
            use_hybrid: 是否使用混合检索
            
        Returns:
            完整内容检索结果
        """
        if use_hybrid:
            try:
                hybrid_service = get_hybrid_search_service()
                # 注意：传入的query已经是改写后的，所以跳过再次改写
                return hybrid_service.search(
                    query,
                    final_count=self.content_top_k,
                    provider=provider,
                    skip_query_rewrite=True
                )
            except Exception as e:
                logger.error(f"混合检索失败，回退到向量检索: {e}")
        
        return vector_search(query, top_k=self.content_top_k, provider=provider)
    
    def _convert_summary_results_to_docs(self, summary_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将摘要检索结果转换为文档格式
        
        Args:
            summary_results: 摘要检索结果
            
        Returns:
            文档格式的结果
        """
        docs = []
        for result in summary_results:
            metadata = result.get("metadata", {})
            docs.append({
                "text": metadata.get("summary", ""),
                "metadata": metadata,
                "score": result.get("score", 0.0),
                "id": result.get("id", "")
            })
        return docs


# 全局双层检索器实例
_two_layer_retriever = None


def get_two_layer_retriever() -> TwoLayerRetriever:
    """
    获取或创建全局双层检索器实例
    
    Returns:
        TwoLayerRetriever 实例
    """
    global _two_layer_retriever
    if _two_layer_retriever is None:
        _two_layer_retriever = TwoLayerRetriever()
    return _two_layer_retriever


def two_layer_search(
    query: str, 
    provider: str = "openai",
    use_hybrid: bool = True
) -> List[Dict[str, Any]]:
    """
    便捷函数：执行双层检索
    
    Args:
        query: 查询文本
        provider: LLM提供商
        use_hybrid: 是否使用混合检索
        
    Returns:
        检索结果列表
    """
    retriever = get_two_layer_retriever()
    return retriever.search(query, provider, use_hybrid)
