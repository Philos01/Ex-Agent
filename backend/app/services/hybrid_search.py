
"""
混合检索 (Hybrid Search) 服务模块
整合 BM2.5、向量检索、重排序和查询改写功能
"""
import logging
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    
    def _search_by_filename_keywords(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        额外通过文件名关键词进行搜索：如果查询中有相关关键词，优先把相关文档找出来
        
        Args:
            query: 查询文本
            top_k: 返回的最大文档数量
            
        Returns:
            搜索结果列表
        """
        try:
            from app.services.vector_store import init_collection
            collection = init_collection()
            if not collection:
                return []
            
            # 查询相关关键词
            keywords = [
                "通讯录", "名单", "名录", "成员", "组员",
                "人员", "名单", "联系方式", "联系",
                "工作单位", "单位", "公司", "企业",
                "姓名", "名字"
            ]
            
            # 检查查询是否包含这些关键词
            has_keyword = any(keyword in query for keyword in keywords)
            if not has_keyword:
                return []
            
            # 获取所有文档元数据
            all_docs = collection.get(include=["metadatas"])
            if not all_docs or not all_docs.get("metadatas"):
                return []
            
            # 找到文件名包含相关关键词的文档
            filename_scores = []
            seen_filenames = set()
            
            for meta in all_docs["metadatas"]:
                if not meta:
                    continue
                filename = meta.get("source", "")
                if not filename or filename in seen_filenames:
                    continue
                
                # 计算文件名匹配分数
                score = 0
                for keyword in keywords:
                    if keyword in filename:
                        score += 1
                
                # 如果有匹配，添加进去
                if score > 0:
                    seen_filenames.add(filename)
                    filename_scores.append((filename, score))
            
            # 按分数排序
            filename_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 获取这些文件的文档 chunks
            results = []
            for filename, _ in filename_scores[:top_k]:
                try:
                    # 获取该文件的前 3 个 chunks
                    doc_result = collection.get(
                        where={"source": filename},
                        include=["documents", "metadatas"],
                        limit=3
                    )
                    if doc_result and doc_result.get("documents"):
                        for doc, meta in zip(doc_result["documents"], doc_result["metadatas"]):
                            results.append({
                                "text": doc,
                                "metadata": meta,
                                "score": 1.0  # 高优先级
                            })
                except Exception:
                    continue
            
            logger.info(f"找到 {len(results)} 个文件名匹配的 chunks")
            return results
        except Exception as e:
            logger.error(f"通过文件名搜索失败: {e}")
            return []
    
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
            logger.info("Hybrid search disabled, using pure vector search")
            return vector_search(query, top_k=hybrid_config.get("final_select_count", 3))
        
        initial_count = initial_count or hybrid_config.get("initial_retrieve_count", 20)
        final_count = final_count or hybrid_config.get("final_select_count", 5)  # 稍微增加最终返回的数量
        bm25_weight = bm25_weight if bm25_weight is not None else hybrid_config.get("bm25_weight", 0.5)
        embedding_weight = embedding_weight if embedding_weight is not None else hybrid_config.get("embedding_weight", 0.5)
        
        logger.info("Hybrid search: query='%s', initial=%d, final=%d", query, initial_count, final_count)
        
        # 1. 先进行文件名关键词搜索，找到明显相关的文档
        filename_matches = self._search_by_filename_keywords(query, top_k=3)
        
        # 2. 查询改写（除非被明确跳过）
        if not skip_query_rewrite:
            logger.debug("Rewriting query: '%s'", query)
            query_rewrite_service = get_query_rewrite_service()
            rewritten_query = query_rewrite_service.rewrite_query(query, provider=provider)
            
            # 二次验证改写后的查询，如果为空则使用原始查询
            if not rewritten_query or not rewritten_query.strip():
                logger.warning("改写后的查询为空，使用原始查询")
                rewritten_query = query
            
            if rewritten_query != query:
                logger.debug("Query rewritten: '%s' -> '%s'", query, rewritten_query)
            else:
                logger.debug("Using original query: '%s'", query)

            logger.debug("Final search query: '%s'", rewritten_query)
        else:
            logger.debug("Skip query rewrite, using: '%s'", query)
            rewritten_query = query
            # 验证传入的查询
            if not rewritten_query or not rewritten_query.strip():
                logger.error("传入的查询为空，无法执行混合检索")
                return []
        
        # 3. 并行检索 BM2.5 和 向量
        with ThreadPoolExecutor(max_workers=2) as executor:
            bm25_future = executor.submit(self._search_bm25, rewritten_query, initial_count)
            vector_future = executor.submit(self._search_vector, rewritten_query, initial_count)
            bm25_docs = bm25_future.result()
            vector_docs = vector_future.result()
        
        # 4. 融合结果
        fused_docs = self._fuse_results(bm25_docs, vector_docs, bm25_weight, embedding_weight, initial_count)
        
        # 5. 把文件名匹配的结果合并进去，放在前面
        if filename_matches:
            logger.info(f"合并 {len(filename_matches)} 个文件名匹配的结果到检索结果中")
            # 先去重
            seen_texts = set()
            unique_filename_matches = []
            for doc in filename_matches:
                text = doc.get("text", "")
                if text not in seen_texts:
                    seen_texts.add(text)
                    unique_filename_matches.append(doc)
            
            # 把文件名匹配的结果放在最前面
            fused_docs = unique_filename_matches + fused_docs
        
        # 6. 重排序
        rerank_service = get_rerank_service()
        reranked_docs = rerank_service.rerank(rewritten_query, fused_docs, final_count)
        
        # 计算耗时
        elapsed_time = time.time() - start_time
        logger.info("Hybrid search done in %.2fs, returned %d results", elapsed_time, len(reranked_docs))
        
        return reranked_docs
    
    def _search_bm25(self, query: str, top_k: int) -> List[Dict]:
        """执行 BM2.5 检索"""
        try:
            logger.debug("BM25 search using: '%s'", query)
            bm25_retriever = get_bm25_retriever()
            docs = bm25_retriever.search(query, top_k=top_k)
            # 标准化分数到 [0, 1]
            if docs:
                max_score = max(d.get("score", 0) for d in docs)
                if max_score > 0:
                    for doc in docs:
                        doc["score"] = doc["score"] / max_score
            logger.debug("BM25 returned %d results", len(docs))
            return docs
        except Exception as e:
            logger.error(f"BM2.5 检索失败: {e}")
            return []
    
    def _search_vector(self, query: str, top_k: int) -> List[Dict]:
        """执行向量检索"""
        try:
            logger.debug("Vector search using: '%s'", query)
            from app.services.vector_store import search_with_distances
            results = search_with_distances(query, top_k=top_k)
            if results:
                for doc in results:
                    distance = doc.get("distance", 1.0)
                    doc["score"] = 1.0 / (1.0 + distance)
            logger.debug("Vector search returned %d results", len(results))
            return results
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
        
        for rank, doc in enumerate(bm25_docs):
            doc_id = doc.get("id", "") or doc.get("metadata", {}).get("chunk_id", "") or doc.get("text", "")[:100]
            rrf_score = 1.0 / (rank + 60)
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
        
        for rank, doc in enumerate(vector_docs):
            doc_id = doc.get("id", "") or doc.get("metadata", {}).get("chunk_id", "") or doc.get("text", "")[:100]
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
        
        logger.debug("Fusion done: %d unique docs", len(result))
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

