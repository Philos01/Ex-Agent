
"""
重排序 (Rerank) 服务模块
使用 BAAI/bge-reranker-v2-m3 模型对检索结果进行重排序
"""
import logging
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.core.config import load_config

logger = logging.getLogger(__name__)


class RerankService:
    """重排序服务"""
    
    def __init__(self, model_name: str = None):
        """
        初始化重排序服务
        
        Args:
            model_name: 重排序模型名称，默认为 BAAI/bge-reranker-v2-m3
        """
        cfg = load_config()
        hybrid_config = cfg.get("hybrid_search", {})
        self.model_name = model_name or hybrid_config.get("rerank_model", "BAAI/bge-reranker-v2-m3")
        
        self.tokenizer = None
        self.model = None
        self.device = None
        self.initialized = False
    
    def _initialize(self):
        """懒加载初始化模型"""
        if self.initialized:
            return
        
        try:
            logger.info(f"正在加载重排序模型: {self.model_name}")
            
            # 检测设备
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"使用设备: {self.device}")
            
            # 加载 tokenizer 和模型
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.initialized = True
            logger.info(f"重排序模型 {self.model_name} 加载成功")
            
        except Exception as e:
            logger.error(f"加载重排序模型失败: {e}")
            raise
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = None) -> List[Dict]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档包含 text 和 metadata 字段
            top_k: 返回的文档数量，None 表示返回所有
            
        Returns:
            重排序后的文档列表，按相关性从高到低排序
        """
        if not documents:
            return []
        
        try:
            self._initialize()
        except Exception as e:
            logger.warning(f"重排序模型初始化失败，返回原始结果: {e}")
            return documents[:top_k] if top_k else documents
        
        # 准备输入对
        pairs = [[query, doc.get("text", "")] for doc in documents]
        
        try:
            # 计算相似度分数
            with torch.no_grad():
                inputs = self.tokenizer(
                    pairs,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                    max_length=1024
                ).to(self.device)
                
                outputs = self.model(**inputs)
                scores = outputs.logits.squeeze(-1).cpu().numpy()
            
            # 将分数与文档关联并排序
            results = []
            for i, (doc, score) in enumerate(zip(documents, scores)):
                results.append({
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": float(score),
                    "original_index": i,
                    "id": doc.get("id", "")
                })
            
            # 按分数降序排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # 取 top_k
            if top_k and top_k > 0:
                results = results[:top_k]
            
            logger.info(f"重排序完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"重排序过程出错: {e}")
            # 出错时返回原始文档
            return documents[:top_k] if top_k else documents


# 全局重排序服务实例
_rerank_service = None


def get_rerank_service() -> RerankService:
    """
    获取或创建全局重排序服务实例
    
    Returns:
        RerankService 实例
    """
    global _rerank_service
    if _rerank_service is None:
        _rerank_service = RerankService()
    return _rerank_service

