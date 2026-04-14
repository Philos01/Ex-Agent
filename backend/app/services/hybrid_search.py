
"""
混合检索 (Hybrid Search) 服务模块
整合 BM2.5、向量检索、重排序和查询改写功能
"""
import logging
import time
from typing import List, Dict, Any
from app.core.config import load_config
from app.services.vector_store import search as vector_search
from app.services.bm25_search import get_bm25_retriever, refresh_bm25_index
from app.services.rerank import get_rerank_service
from app.services.query_rewrite import get_query_rewrite_service

logger = logging.getLogger(__name__)


class HybridSearchService:
    """混合检索服务"""
    
    def __init__(self):
        self.cfg = load_config()
        self.hybrid_config = self.cfg.get("hybrid_search", {})
    
    def search(
        self, 
        query: str, 
        initial_count: int = None,
        final_count: int = None,
        bm25_weight: float = None,
        embedding_weight: float = None,
        provider: str = None,
        skip_query_rewrite: bool = False
    ) -> List[Dict]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            initial_count: 初始检索的文档数量
            final_count: 最终返回的文档数量
            bm25_weight: BM2.5 检索结果的权重
            embedding_weight: 向量检索结果的权重
            provider: LLM 提供商（用于查询改写）
            skip_query_rewrite: 是否跳过查询改写（用于避免重复执行）
            
        Returns:
            检索结果列表
        """
        # 检查原始查询是否为空
        if not query or not query.strip():
            logger.error("原始查询为空，无法执行混合检索")
            return []
        
        start_time = time.time()
        
        # 获取配置参数
        cfg = load_config()
        hybrid_config = cfg.get("hybrid_search", {})
        
        enabled = hybrid_config.get("enabled", True)
        if not enabled:
            logger.info("混合检索未启用，使用纯向量检索")
            return vector_search(query, top_k=hybrid_config.get("final_select_count", 3))
        
        initial_count = initial_count or hybrid_config.get("initial_retrieve_count", 20)
        final_count = final_count or hybrid_config.get("final_select_count", 3)
        bm25_weight = bm25_weight if bm25_weight is not None else hybrid_config.get("bm25_weight", 0.5)
        embedding_weight = embedding_weight if embedding_weight is not None else hybrid_config.get("embedding_weight", 0.5)
        
        logger.info(f"开始混合检索: query='{query}', initial_count={initial_count}, final_count={final_count}")
        
        # 1. 查询改写（除非被明确跳过）
        if not skip_query_rewrite:
            logger.info(f"[DEBUG] 开始查询改写，原始查询: '{query}', provider: {provider}")
            query_rewrite_service = get_query_rewrite_service()
            rewritten_query = query_rewrite_service.rewrite_query(query, provider=provider)
            
            # 二次验证改写后的查询，如果为空则使用原始查询
            if not rewritten_query or not rewritten_query.strip():
                logger.warning("改写后的查询为空，使用原始查询")
                rewritten_query = query
            
            if rewritten_query != query:
                logger.info(f"查询改写成功: '{query}' -> '{rewritten_query}'")
            else:
                logger.info(f"使用原始查询: '{query}'")
            
            logger.info(f"[DEBUG] 最终用于检索的查询: '{rewritten_query}'")
        else:
            logger.info(f"[DEBUG] 跳过查询改写，直接使用传入的查询: '{query}'")
            rewritten_query = query
            # 验证传入的查询
            if not rewritten_query or not rewritten_query.strip():
                logger.error("传入的查询为空，无法执行混合检索")
                return []
        
        # 2. 并行检索 BM2.5 和 向量
        bm25_docs = self._search_bm25(rewritten_query, initial_count)
        vector_docs = self._search_vector(rewritten_query, initial_count)
        
        # 3. 融合结果
        fused_docs = self._fuse_results(bm25_docs, vector_docs, bm25_weight, embedding_weight, initial_count)
        
        # 4. 重排序
        rerank_service = get_rerank_service()
        reranked_docs = rerank_service.rerank(rewritten_query, fused_docs, final_count)
        
        # 计算耗时
        elapsed_time = time.time() - start_time
        logger.info(f"混合检索完成，耗时 {elapsed_time:.2f}s，返回 {len(reranked_docs)} 个结果")
        
        return reranked_docs
    
    def _search_bm25(self, query: str, top_k: int) -> List[Dict]:
        """执行 BM2.5 检索"""
        try:
            logger.info(f"[DEBUG] BM2.5 检索使用查询: '{query}'")
            bm25_retriever = get_bm25_retriever()
            docs = bm25_retriever.search(query, top_k=top_k)
            # 标准化分数到 [0, 1]
            if docs:
                max_score = max(d.get("score", 0) for d in docs)
                if max_score > 0:
                    for doc in docs:
                        doc["score"] = doc["score"] / max_score
            logger.info(f"BM2.5 检索到 {len(docs)} 个结果")
            return docs
        except Exception as e:
            logger.error(f"BM2.5 检索失败: {e}")
            return []
    
    def _search_vector(self, query: str, top_k: int) -> List[Dict]:
        """执行向量检索"""
        try:
            logger.info(f"[DEBUG] 向量检索使用查询: '{query}'")
            docs = vector_search(query, top_k=top_k)
            # Chroma 返回的是距离，转换为相似度分数 [0, 1]
            # 距离越小越好，所以 1 - normalized_distance
            for i, doc in enumerate(docs):
                # 默认分数为位置权重
                doc["score"] = 1.0 - (i / len(docs)) if docs else 0.5
            logger.info(f"向量检索到 {len(docs)} 个结果")
            return docs
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    def _fuse_results(
        self, 
        bm25_docs: List[Dict], 
        vector_docs: List[Dict], 
        bm25_weight: float, 
        embedding_weight: float,
        top_k: int
    ) -> List[Dict]:
        """
        融合 BM2.5 和向量检索结果
        
        使用 Reciprocal Rank Fusion (RRF) 算法
        """
        doc_scores = {}
        
        # 处理 BM2.5 结果
        for rank, doc in enumerate(bm25_docs):
            doc_id = doc.get("id", "") or doc.get("text", "")[:100]  # 使用 id 或文本前100字符作为标识
            rrf_score = 1.0 / (rank + 60)  # RRF 公式，k=60
            weighted_score = rrf_score * bm25_weight
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "id": doc.get("id", ""),
                    "score": 0.0,
                    "source": []
                }
            
            doc_scores[doc_id]["score"] += weighted_score
            doc_scores[doc_id]["source"].append("bm25")
        
        # 处理向量检索结果
        for rank, doc in enumerate(vector_docs):
            doc_id = doc.get("id", "") or doc.get("text", "")[:100]
            rrf_score = 1.0 / (rank + 60)
            weighted_score = rrf_score * embedding_weight
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "id": doc.get("id", ""),
                    "score": 0.0,
                    "source": []
                }
            
            doc_scores[doc_id]["score"] += weighted_score
            doc_scores[doc_id]["source"].append("vector")
        
        # 按分数排序
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)
        
        # 取前 top_k 个
        result = sorted_docs[:top_k]
        
        logger.info(f"结果融合完成，共有 {len(result)} 个唯一文档")
        return result


# 全局混合检索服务实例
_hybrid_search_service = None


def get_hybrid_search_service() -> HybridSearchService:
    """
    获取或创建全局混合检索服务实例
    
    Returns:
        HybridSearchService 实例
    """
    global _hybrid_search_service
    if _hybrid_search_service is None:
        _hybrid_search_service = HybridSearchService()
    return _hybrid_search_service


def hybrid_search(
    query: str, 
    initial_count: int = None,
    final_count: int = None,
    bm25_weight: float = None,
    embedding_weight: float = None,
    provider: str = None,
    skip_query_rewrite: bool = False
) -> List[Dict]:
    """
    便捷函数：执行混合检索
    
    Args:
        query: 查询文本
        initial_count: 初始检索的文档数量
        final_count: 最终返回的文档数量
        bm25_weight: BM2.5 检索结果的权重
        embedding_weight: 向量检索结果的权重
        provider: LLM 提供商（用于查询改写）
        skip_query_rewrite: 是否跳过查询改写（用于避免重复执行）
        
    Returns:
        检索结果列表
    """
    service = get_hybrid_search_service()
    return service.search(
        query=query,
        initial_count=initial_count,
        final_count=final_count,
        bm25_weight=bm25_weight,
        embedding_weight=embedding_weight,
        provider=provider,
        skip_query_rewrite=skip_query_rewrite
    )

