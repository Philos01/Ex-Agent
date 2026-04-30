
"""
BM2.5 检索服务模块
提供基于关键词的文本检索功能
"""
import logging
import math
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
import jieba
from app.services.vector_store import get_client, init_collection, reset_collection

logger = logging.getLogger(__name__)


class BM25Retriever:
    """BM2.5 检索器"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化 BM2.5 检索器
        
        Args:
            k1: 控制词频饱和度的参数，通常在 1.2-2.0 之间
            b: 控制文档长度归一化的参数，通常为 0.75
        """
        self.k1 = k1
        self.b = b
        self.documents = []  # 存储文档文本
        self.doc_metadatas = []  # 存储文档元数据
        self.doc_ids = []  # 存储文档ID
        self.doc_lengths = []  # 存储每个文档的长度
        self.avg_doc_length = 0  # 平均文档长度
        self.term_freqs = []  # 每个文档的词频统计
        self.doc_count = 0  # 文档总数
        self.term_doc_count = defaultdict(int)  # 每个词出现在多少文档中
        self.initialized = False
    
    def _is_hnsw_error(self, error: Exception) -> bool:
        """
        检测错误是否为 HNSW 索引损坏相关错误
        
        Args:
            error: 异常对象
            
        Returns:
            是否为 HNSW 索引损坏错误
        """
        error_str = str(error).lower()
        hnsw_error_keywords = [
            "hnsw", "compaction", "compactor", "segment reader",
            "loading index", "backfill", "corrupt", "segment",
            "error executing plan"
        ]
        return any(keyword in error_str for keyword in hnsw_error_keywords)
    
    def _try_load_with_recovery(self, max_retries: int = 2) -> bool:
        """
        尝试从向量库加载文档到 BM2.5 索引。

        HNSW 索引损坏时不会自动重置（数据保全策略），
        仅记录错误并返回 False。修复需通过重启服务触发 startup_health_check。
        """
        for attempt in range(max_retries + 1):
            try:
                collection = init_collection()
                if not collection:
                    logger.warning("无法获取向量库集合")
                    return False

                results = collection.get(include=["documents", "metadatas"])
                if not results or not results.get("documents"):
                    logger.warning("向量库中没有文档")
                    return False

                documents = results.get("documents", [])
                metadatas = results.get("metadatas", [])
                ids = results.get("ids", [])

                self._build_index(documents, metadatas, ids)
                logger.debug("Loaded %d documents from vector store into BM25 index", self.doc_count)
                return True

            except Exception as e:
                if self._is_hnsw_error(e):
                    logger.warning(
                        f"检测到 HNSW 索引损坏（尝试 {attempt + 1}/{max_retries + 1}），"
                        f"数据已保全。请重启服务以触发自动修复。错误: {e}"
                    )
                    break  # 不重置，保全数据
                else:
                    logger.error(f"从向量库加载文档失败: {e}")
                    break

        return False
    
    def load_from_vector_store(self) -> bool:
        """
        从 Chroma 向量库加载文档到 BM2.5 索引
        包含 HNSW 索引损坏自动恢复机制
        
        Returns:
            是否成功加载
        """
        try:
            return self._try_load_with_recovery(max_retries=2)
        except Exception as e:
            logger.error(f"从向量库加载文档失败: {e}")
            return False
    
    def _build_index(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        """
        构建 BM2.5 索引
        
        Args:
            documents: 文档文本列表
            metadatas: 文档元数据列表
            ids: 文档ID列表
        """
        self.documents = documents
        self.doc_metadatas = metadatas
        self.doc_ids = ids
        self.doc_count = len(documents)
        
        # 处理每个文档
        self.term_freqs = []
        self.doc_lengths = []
        self.term_doc_count.clear()
        
        for doc in documents:
            # 分词
            tokens = self._tokenize(doc)
            # 统计词频
            freq = Counter(tokens)
            self.term_freqs.append(freq)
            self.doc_lengths.append(len(tokens))
            # 更新词的文档频率
            for term in freq:
                self.term_doc_count[term] += 1
        
        # 计算平均文档长度
        if self.doc_count > 0:
            self.avg_doc_length = sum(self.doc_lengths) / self.doc_count
        
        self.initialized = True
    
    def _tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词（支持中英文）
        
        Args:
            text: 待分词的文本
            
        Returns:
            分词后的列表
        """
        # 使用 jieba 进行中文分词
        tokens = jieba.lcut(text)
        # 过滤掉太短的词和标点符号
        tokens = [token.strip().lower() for token in tokens if len(token.strip()) > 1 and re.match(r'[\w\u4e00-\u9fa5]+', token)]
        return tokens
    
    def _compute_idf(self, term: str) -> float:
        """
        计算逆文档频率 IDF
        
        Args:
            term: 词项
            
        Returns:
            IDF 值
        """
        # 使用 BM25 的 IDF 计算公式
        n_q = self.term_doc_count.get(term, 0)
        numerator = self.doc_count - n_q + 0.5
        denominator = n_q + 0.5
        return math.log((numerator / denominator) + 1)
    
    def _compute_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """
        计算查询与文档的 BM25 分数
        
        Args:
            query_tokens: 查询词列表
            doc_idx: 文档索引
            
        Returns:
            BM25 分数
        """
        score = 0.0
        doc_len = self.doc_lengths[doc_idx] if doc_idx < len(self.doc_lengths) else 0
        doc_freq = self.term_freqs[doc_idx] if doc_idx < len(self.term_freqs) else Counter()
        
        for term in query_tokens:
            if term not in doc_freq:
                continue
            
            f_qd = doc_freq[term]
            idf = self._compute_idf(term)
            
            numerator = f_qd * (self.k1 + 1)
            denominator = f_qd + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_length if self.avg_doc_length > 0 else 1))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        使用 BM2.5 进行检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表，每个结果包含 text, metadata, score
        """
        if not self.initialized:
            logger.warning("BM2.5 索引未初始化，尝试从向量库加载...")
            if not self.load_from_vector_store():
                logger.error("无法初始化 BM2.5 索引")
                return []
        
        # 对查询进行分词
        query_tokens = self._tokenize(query)
        if not query_tokens:
            logger.warning("查询分词后为空")
            return []
        
        # 计算每个文档的分数
        scores = []
        for i in range(self.doc_count):
            score = self._compute_score(query_tokens, i)
            if score > 0:
                scores.append((i, score))
        
        # 按分数降序排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 取 top_k 个结果
        results = []
        for idx, score in scores[:top_k]:
            results.append({
                "text": self.documents[idx] if idx < len(self.documents) else "",
                "metadata": self.doc_metadatas[idx] if idx < len(self.doc_metadatas) else {},
                "score": score,
                "id": self.doc_ids[idx] if idx < len(self.doc_ids) else ""
            })
        
        logger.debug("BM25 search returned %d results", len(results))
        return results


# 全局 BM2.5 检索器实例
_bm25_retriever = None


def get_bm25_retriever() -> BM25Retriever:
    """
    获取或创建全局 BM2.5 检索器实例
    
    Returns:
        BM25Retriever 实例
    """
    global _bm25_retriever
    if _bm25_retriever is None:
        _bm25_retriever = BM25Retriever()
        # 尝试从向量库加载
        try:
            _bm25_retriever.load_from_vector_store()
        except Exception as e:
            logger.warning(f"初始化 BM2.5 检索器时加载文档失败: {e}")
    return _bm25_retriever


def refresh_bm25_index():
    """
    刷新 BM2.5 索引（重新从向量库加载文档）
    
    Returns:
        是否成功刷新
    """
    global _bm25_retriever
    try:
        if _bm25_retriever:
            success = _bm25_retriever.load_from_vector_store()
            logger.info(f"BM2.5 索引刷新{'成功' if success else '失败'}")
            return success
        else:
            get_bm25_retriever()
            return True
    except Exception as e:
        logger.error(f"刷新 BM2.5 索引失败: {e}")
        return False

