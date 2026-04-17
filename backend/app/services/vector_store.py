
"""
Simple Chroma-backed vector store helpers
支持本地和云端嵌入模型
"""
import os
import shutil
from app.core.config import CHROMA_DIR, load_config, get_complete_config, ensure_data_dirs
import chromadb
from typing import List
import logging
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)

# 确保数据目录存在
ensure_data_dirs()

# 使用PersistentClient确保数据持久化
_client = None
_collection = None
_embedding_initialized = False


def _init_embedding_service():
    """初始化嵌入服务（懒加载）"""
    global _embedding_initialized
    if not _embedding_initialized:
        cfg = get_complete_config()
        mode = cfg.get("embedding_mode", "local")
        try:
            EmbeddingService.initialize(mode=mode, config=cfg)
            _embedding_initialized = True
            logger.info(f"嵌入服务初始化成功，模式: {mode}")
        except Exception as e:
            logger.error(f"嵌入服务初始化失败: {e}")
            raise


def get_client():
    """获取或创建ChromaDB客户端"""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def init_collection():
    """初始化或获取向量库集合，处理可能的损坏"""
    global _collection
    if _collection is None:
        client = get_client()
        try:
            _collection = client.get_or_create_collection("lab_docs")
        except Exception as e:
            logger.warning(f"Collection initialization error: {e}")
            # 如果集合损坏，尝试删除并重新创建
            try:
                client.delete_collection("lab_docs")
            except:
                pass
            _collection = client.get_or_create_collection("lab_docs")
    return _collection


def reset_collection():
    """重置集合（用于修复损坏或切换嵌入模型）"""
    global _collection, _client
    _collection = None
    client = get_client()
    try:
        client.delete_collection("lab_docs")
        logger.info("已删除旧的向量库集合")
    except Exception as e:
        logger.warning(f"删除集合时出错: {e}")
    _collection = client.get_or_create_collection("lab_docs")
    logger.info("已创建新的向量库集合")
    return _collection


# 初始化集合
try:
    _collection = init_collection()
except Exception as e:
    logger.error(f"Failed to initialize collection: {e}")
    _collection = None


def add_documents(ids: List[str], documents: List[str], metadatas: List[dict], provider: str = None):
    """
    添加文档到向量库
    
    Args:
        ids: 文档ID列表
        documents: 文档内容列表
        metadatas: 元数据列表
        provider: 已废弃，保留兼容性
    """
    # 初始化嵌入服务
    _init_embedding_service()
    
    try:
        # 使用统一的嵌入服务
        embeddings = EmbeddingService.embed_texts(documents)
        
        # ensure lists lengths match
        if len(embeddings) != len(documents):
            logger.warning(f"嵌入数量不匹配: {len(embeddings)} vs {len(documents)}")
            embeddings = None
        
        # 重新获取集合引用，确保使用最新的集合
        collection = init_collection()
        kwargs = {"ids": ids, "documents": documents, "metadatas": metadatas}
        if embeddings:
            kwargs["embeddings"] = embeddings
        
        # 处理可能的错误
        try:
            collection.add(**kwargs)
            logger.info(f"成功添加 {len(documents)} 个文档到向量库")
        except Exception as e:
            logger.error(f"Add documents error: {e}")
            
            # 检测 ChromaDB 索引损坏的各种错误
            error_str = str(e).lower()
            hnsw_errors = [
                "hnsw", "compaction", "segment reader", "loading index",
                "corrupt", "segment"
            ]
            
            is_index_corrupted = any(err in error_str for err in hnsw_errors)
            
            if is_index_corrupted:
                logger.warning("检测到向量库索引损坏，正在重置向量库...")
                reset_collection()
                collection = init_collection()
                collection.add(**kwargs)
                logger.info("已重置向量库并重新添加文档")
            # 如果是维度不匹配错误，重置集合并重新尝试
            elif "dimension" in error_str:
                logger.warning("Dimension mismatch error, resetting collection...")
                reset_collection()
                collection = init_collection()
                collection.add(**kwargs)
                logger.info("已重置集合并重新添加文档")
            # 如果是集合不存在错误，重置集合并重新尝试
            elif "collection" in error_str and "does not exist" in error_str:
                logger.warning("Collection not found, resetting collection...")
                reset_collection()
                collection = init_collection()
                collection.add(**kwargs)
                logger.info("已重置集合并重新添加文档")
            else:
                raise
                
    except Exception as e:
        logger.error(f"添加文档失败: {e}")
        raise


def search(query: str, top_k: int = 5, provider: str = None):
    """
    在向量库中搜索
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        provider: 已废弃，保留兼容性
        
    Returns:
        搜索结果列表
    """
    # 检查查询是否为空
    if not query or not query.strip():
        logger.error("查询为空，无法执行向量检索")
        return []
    
    collection = init_collection()
    
    try:
        # 初始化嵌入服务
        _init_embedding_service()
        
        # 使用统一的嵌入服务
        q_emb = EmbeddingService.embed_texts([query])
        
        if not q_emb or not q_emb[0]:
            logger.warning("嵌入失败，使用文本查询")
            res = collection.query(query_texts=[query], n_results=top_k, include=["documents", "metadatas"])
        else:
            res = collection.query(query_embeddings=q_emb, n_results=top_k, include=["documents", "metadatas", "distances"])
        
        docs = []
        docs_list = res.get("documents", [[]])[0]
        metas_list = res.get("metadatas", [[]])[0]
        for d, m in zip(docs_list, metas_list):
            docs.append({"text": d, "metadata": m})
        
        logger.info(f"搜索完成，返回 {len(docs)} 个结果")
        return docs
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        # 不再自动重置集合，避免清空知识库
        if "hnsw" in str(e).lower() or "segment" in str(e).lower():
            logger.warning("HNSW索引错误，但不自动重置集合")
        return []


def search_by_filenames(query: str, filenames: List[str], top_k: int = 5, provider: str = None):
    """
    在指定文件中搜索
    
    Args:
        query: 查询文本
        filenames: 文件名列表
        top_k: 返回结果数量
        provider: 已废弃，保留兼容性
        
    Returns:
        搜索结果列表
    """
    # 检查查询是否为空
    if not query or not query.strip():
        logger.error("查询为空，无法执行向量检索")
        return []
    
    collection = init_collection()
    
    try:
        # 初始化嵌入服务
        _init_embedding_service()
        
        logger.info(f"在 {len(filenames)} 个文件中检索: {filenames}")
        
        # 使用统一的嵌入服务
        q_emb = EmbeddingService.embed_texts([query])
        
        if not q_emb or not q_emb[0]:
            logger.warning("嵌入失败，使用文本查询")
            res = collection.query(
                query_texts=[query], 
                n_results=top_k * 2,  # 获取更多结果用于过滤
                include=["documents", "metadatas"]
            )
        else:
            res = collection.query(
                query_embeddings=q_emb, 
                n_results=top_k * 2,  # 获取更多结果用于过滤
                include=["documents", "metadatas", "distances"]
            )
        
        docs = []
        docs_list = res.get("documents", [[]])[0]
        metas_list = res.get("metadatas", [[]])[0]
        
        # 只保留指定文件的结果
        for d, m in zip(docs_list, metas_list):
            if m and m.get("source") in filenames:
                docs.append({"text": d, "metadata": m})
                if len(docs) >= top_k:
                    break
        
        logger.info(f"在指定文件中搜索完成，返回 {len(docs)} 个结果")
        return docs
        
    except Exception as e:
        logger.error(f"按文件名搜索错误: {e}")
        return []


def clear_all():
    """清空向量库"""
    global _collection
    # delete and recreate collection
    client = get_client()
    try:
        client.delete_collection("lab_docs")
        logger.info("已清空向量库")
    except Exception:
        pass
    _collection = client.get_or_create_collection("lab_docs")


def delete_documents_by_filename(filename: str):
    """
    按文件名删除向量库中的文档
    
    Args:
        filename: 文件名
        
    Returns:
        删除的文档数量
    """
    try:
        collection = init_collection()
        
        # 获取所有文档，查找匹配的文件名
        all_docs = collection.get(include=["metadatas"])
        
        if not all_docs or not all_docs.get("ids"):
            return 0
        
        # 找出所有匹配的文档 ID
        ids_to_delete = []
        for i, metadata in enumerate(all_docs.get("metadatas", [])):
            if metadata and metadata.get("source") == filename:
                ids_to_delete.append(all_docs["ids"][i])
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"已从向量库删除文件名 {filename} 的 {len(ids_to_delete)} 个文档")
            return len(ids_to_delete)
        
        return 0
    except Exception as e:
        logger.error(f"按文件名删除文档失败: {e}")
        return 0


def get_collection_info():
    """获取向量库信息，用于调试"""
    collection = init_collection()
    try:
        count = collection.count()
        cfg = load_config()
        mode = cfg.get("embedding_mode", "local")
        
        info = {
            "count": count,
            "name": collection.name,
            "persist_directory": str(CHROMA_DIR),
            "embedding_mode": mode
        }
        
        # 如果嵌入服务已初始化，添加更多信息
        try:
            if mode == "local":
                info["local_model"] = cfg.get("local_embedding_model", "BAAI/bge-small-zh-v1.5")
        except:
            pass
            
        return info
    except Exception as e:
        return {"error": str(e)}
