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
        print(f"[DEBUG TwoLayerRetriever.search] 双层检索已被调用，查询: '{query[:50]}...'")
        
        # 检查原始查询是否为空
        if not query or not query.strip():
            logger.error("原始查询为空，无法执行检索")
            print(f"[DEBUG TwoLayerRetriever.search] 错误：查询为空")
            return []
        
        logger.info(f"开始双层检索: query='{query}'")
        print(f"[DEBUG TwoLayerRetriever.search] 开始双层检索，原始查询: '{query}'")
        
        # 1. 查询改写 - 在摘要检索前优化查询
        logger.info(f"[DEBUG] 开始查询改写，原始查询: '{query}', provider: {provider}")
        print(f"[DEBUG TwoLayerRetriever.search] 开始查询改写...")
        query_rewrite_service = get_query_rewrite_service()
        rewritten_query = query_rewrite_service.rewrite_query(query, provider=provider, use_summary_config=True)
        
        # 二次验证改写后的查询，如果为空则使用原始查询
        if not rewritten_query or not rewritten_query.strip():
            logger.warning("改写后的查询为空，使用原始查询")
            rewritten_query = query
        
        # 第一层：检索摘要，找到相关文件（使用改写后的查询）
        summary_results = self._search_summaries(rewritten_query, provider)
        
        logger.debug(f"摘要检索结果: {summary_results}")
        
        if not summary_results:
            logger.info("摘要检索无结果，直接检索完整内容")
            return self._search_full_content(rewritten_query, provider, use_hybrid)
        
        # 获取所有摘要检索到的文件名
        relevant_filenames = []
        for result in summary_results:
            metadata = result.get("metadata", {})
            filename = metadata.get("filename")
            if filename and filename not in relevant_filenames:
                relevant_filenames.append(filename)
        
        logger.info(f"摘要检索到 {len(relevant_filenames)} 个相关文件: {relevant_filenames}")
        
        # 第二层：在这些相关文件中检索正文内容（使用改写后的查询）
        logger.info("正在检索相关文件的正文内容...")
        try:
            from app.services.vector_store import search_by_filenames
            content_results = search_by_filenames(
                rewritten_query, 
                relevant_filenames, 
                top_k=self.content_top_k,
                provider=provider
            )
            
            if content_results:
                logger.info(f"从相关文件中检索到 {len(content_results)} 个正文片段")
                return content_results
            else:
                logger.info("相关文件中未找到正文内容，回退到全局检索")
                return self._search_full_content(rewritten_query, provider, use_hybrid)
                
        except Exception as e:
            logger.error(f"检索相关文件正文失败，回退到全局检索: {e}")
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
        print(f"[DEBUG TwoLayerRetriever._search_summaries] 开始检索摘要，查询: '{query[:50]}...'")
        store = get_summary_store()
        all_summaries = store.get_all_summaries()
        
        print(f"[DEBUG TwoLayerRetriever._search_summaries] 获取到 {len(all_summaries)} 个摘要")
        
        if not all_summaries:
            logger.info("没有可用的文档摘要")
            print(f"[DEBUG TwoLayerRetriever._search_summaries] 没有可用的文档摘要")
            return []
        
        logger.info(f"共有 {len(all_summaries)} 个文档摘要待检索")
        
        # 使用BM2.5对摘要进行检索
        try:
            bm25_retriever = get_bm25_retriever()
            
            # 构建摘要索引
            summary_texts = []
            summary_metas = []
            for summary in all_summaries:
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
            
            # 临时构建BM2.5索引进行检索
            # 注意：这里我们直接使用BM2.5的搜索，但不修改全局索引
            from app.services.bm25_search import BM25Retriever
            temp_retriever = BM25Retriever()
            
            # 生成临时 ID
            summary_ids = [str(uuid.uuid4()) for _ in range(len(summary_texts))]
            temp_retriever._build_index(summary_texts, summary_metas, summary_ids)
            
            results = temp_retriever.search(query, top_k=self.summary_top_k)
            
            logger.debug(f"BM2.5 原始搜索结果: {results}")
            
            # 添加相关性分数（基于BM2.5分数）
            for result in results:
                result["relevance_score"] = result.get("score", 0.0)
            
            logger.info(f"摘要检索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"摘要检索失败: {e}")
            import traceback
            traceback.print_exc()
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
