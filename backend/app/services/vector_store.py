"""
ChromaDB Vector Store with HNSW corruption prevention.

Root cause: ChromaDB 1.5.5 on Windows stores HNSW index cache in
UUID-named subdirectories under data/chroma/. These cache files
corrupt on every unclean process termination (SIGTERM/Ctrl+C).
The actual document+embedding data lives safely in chroma.sqlite3.

Fix: Delete HNSW cache directories on shutdown AND on startup if
corrupted. ChromaDB auto-rebuilds the index from SQLite data.
"""
import os
import json
import shutil
import logging
from typing import List

from app.core.config import CHROMA_DIR, load_config, get_complete_config, ensure_data_dirs
import chromadb
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)

ensure_data_dirs()

_client = None
_collection = None
_embedding_initialized = False
_startup_cleaned = False


def _clean_hnsw_cache():
    """
    Delete HNSW index cache directories under data/chroma/.

    In ChromaDB 1.5.5, UUID-named subdirectories (e.g. 0d83436a-...)
    contain only HNSW index cache files (index_metadata.pickle).
    The actual document data and embeddings are stored in chroma.sqlite3.

    Deleting these cache dirs is SAFE — ChromaDB rebuilds the HNSW
    index from SQLite data on next collection access.
    """
    chroma_path = CHROMA_DIR
    if not chroma_path.exists():
        return 0

    cleaned = 0
    for entry in chroma_path.iterdir():
        if entry.is_dir() and entry.name != "__pycache__":
            # UUID-named directories contain HNSW cache
            try:
                shutil.rmtree(entry)
                cleaned += 1
                logger.info(f"Cleaned HNSW cache directory: {entry.name}")
            except Exception as e:
                logger.warning(f"Failed to clean {entry.name}: {e}")

    if cleaned:
        logger.info(f"Cleaned {cleaned} HNSW cache directories. "
                     f"ChromaDB will rebuild indices from SQLite data on next access.")
    return cleaned


def _init_embedding_service():
    """初始化嵌入服务（懒加载）"""
    global _embedding_initialized
    if not _embedding_initialized:
        cfg = get_complete_config()
        mode = cfg.get("embedding_mode", "local")
        try:
            EmbeddingService.initialize(mode=mode, config=cfg)
            _embedding_initialized = True
            logger.debug("Embedding service initialized, mode: %s", mode)
        except Exception as e:
            logger.error(f"嵌入服务初始化失败: {e}")
            raise


def get_client():
    """获取或创建 ChromaDB 持久化客户端"""
    global _client, _startup_cleaned

    if _client is None:
        # Clean HNSW cache on first client creation (once per process lifetime)
        if not _startup_cleaned:
            _clean_hnsw_cache()
            _startup_cleaned = True

        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def _get_collection_name() -> str:
    """Collection name keyed by embedding dimension to prevent mismatch."""
    _init_embedding_service()
    dim = EmbeddingService.get_embedding_dimension()
    return f"lab_docs_{dim}d"


def init_collection():
    """初始化或获取向量库集合（自动适配嵌入维度）"""
    global _collection, _embedding_initialized
    if _collection is None:
        _init_embedding_service()
        client = get_client()
        name = _get_collection_name()
        try:
            _collection = client.get_or_create_collection(name)
            logger.info("Collection ready: %s (%d docs)", name, _collection.count())
        except Exception as e:
            logger.warning(f"Collection init error ({name}): {e}")
            _clean_hnsw_cache()
            try:
                _collection = client.get_or_create_collection(name)
                logger.info("Collection created after cache cleanup: %s", name)
            except Exception as e2:
                logger.error(f"Collection init failed after cleanup: {e2}")
                _collection = None
    return _collection


def startup_health_check() -> dict:
    """
    Check vector store health on startup.
    Cleans HNSW cache and verifies collection is accessible.

    Returns:
        {"healthy": bool, "doc_count": int, "message": str}
    """
    global _collection
    _init_embedding_service()
    name = _get_collection_name()
    client = get_client()

    try:
        _collection = client.get_or_create_collection(name)
        count = _collection.count()
        logger.info(f"Startup health check: OK, {count} documents in {name}")
        return {"healthy": True, "doc_count": count,
                "message": f"Vector store healthy ({name}), {count} documents"}
    except Exception as e:
        logger.warning(f"Startup health check: {name} access failed, "
                       f"attempting repair: {e}")
        _clean_hnsw_cache()
        try:
            _collection = client.get_or_create_collection(name)
            count = _collection.count()
            logger.info(f"Startup health check: repaired, {count} documents")
            return {"healthy": True, "doc_count": count,
                    "message": f"HNSW index rebuilt from SQLite, {count} documents preserved"}
        except Exception as e2:
            logger.error(f"Startup health check: repair failed: {e2}")
            return {"healthy": False, "doc_count": 0,
                    "message": f"Vector store unavailable: {e2}"}


def reset_collection():
    """
    Reset collection (e.g., for embedding mode switch).
    Deletes the CURRENT dimension's collection and recreates it.
    Old collections with other dimensions are preserved on disk.
    """
    global _collection
    _collection = None
    _init_embedding_service()
    name = _get_collection_name()
    client = get_client()
    try:
        client.delete_collection(name)
        logger.info("Deleted collection: %s", name)
    except Exception:
        pass
    _collection = client.get_or_create_collection(name)
    logger.info("Recreated collection: %s", name)
    return _collection


# ── CRUD operations ────────────────────────────────────

def add_documents(ids: List[str], documents: List[str],
                  metadatas: List[dict], provider: str = None):
    """添加文档到向量库"""
    _init_embedding_service()

    try:
        embeddings = EmbeddingService.embed_texts(documents)
        if len(embeddings) != len(documents):
            logger.warning(f"嵌入数量不匹配: {len(embeddings)} vs {len(documents)}")
            embeddings = None

        collection = init_collection()
        if collection is None:
            raise RuntimeError("向量库集合不可用")

        kwargs = {"ids": ids, "documents": documents, "metadatas": metadatas}
        if embeddings:
            kwargs["embeddings"] = embeddings

        try:
            collection.add(**kwargs)
            logger.debug("Added %d documents to vector store", len(documents))
        except Exception as e:
            error_str = str(e).lower()

            # Dimension mismatch: switch to the correct collection for this model
            if "dimension" in error_str or "expecting embedding" in error_str:
                current_dim = EmbeddingService.get_embedding_dimension()
                logger.warning(
                    "Embedding dimension mismatch. Recreating collection for %dd. Error: %s",
                    current_dim, e,
                )
                global _collection
                client = get_client()
                name = _get_collection_name()
                try:
                    client.delete_collection(name)
                except Exception:
                    pass
                _collection = client.get_or_create_collection(name)
                _collection.add(**kwargs)
                logger.info("文档已添加到新集合: %s", name)
                return

            hnsw_keywords = ["hnsw", "compaction", "segment reader",
                             "loading index", "backfill", "corrupt"]
            is_hnsw = any(kw in error_str for kw in hnsw_keywords)

            if is_hnsw or ("collection" in error_str and "does not exist" in error_str):
                logger.warning(f"向量库异常，清理 HNSW 缓存后重试: {e}")
                _clean_hnsw_cache()
                collection = init_collection()
                if collection:
                    collection.add(**kwargs)
                    logger.info("已清理缓存并重新添加文档")
                else:
                    raise RuntimeError("向量库恢复失败")
            else:
                raise

    except Exception as e:
        logger.error(f"添加文档失败: {e}")
        raise


def search(query: str, top_k: int = 5, provider: str = None):
    """向量搜索"""
    if not query or not query.strip():
        return []

    collection = init_collection()
    if collection is None:
        logger.error("向量库集合不可用")
        return []

    try:
        _init_embedding_service()
        q_emb = EmbeddingService.embed_texts([query])

        if not q_emb or not q_emb[0]:
            res = collection.query(query_texts=[query], n_results=top_k,
                                   include=["documents", "metadatas"])
        else:
            res = collection.query(query_embeddings=q_emb, n_results=top_k,
                                   include=["documents", "metadatas", "distances"])

        docs = []
        docs_list = res.get("documents", [[]])[0]
        metas_list = res.get("metadatas", [[]])[0]
        for d, m in zip(docs_list, metas_list):
            docs.append({"text": d, "metadata": m})
        logger.debug("Search returned %d results", len(docs))
        return docs

    except Exception as e:
        logger.error("Search error: %s", e)
        return []


def search_with_distances(query: str, top_k: int = 5, provider: str = None):
    """向量搜索（含距离）"""
    if not query or not query.strip():
        return []

    collection = init_collection()
    if collection is None:
        return []

    try:
        _init_embedding_service()
        q_emb = EmbeddingService.embed_texts([query])

        if not q_emb or not q_emb[0]:
            res = collection.query(query_texts=[query], n_results=top_k,
                                   include=["documents", "metadatas", "distances"])
        else:
            res = collection.query(query_embeddings=q_emb, n_results=top_k,
                                   include=["documents", "metadatas", "distances"])

        docs = []
        docs_list = res.get("documents", [[]])[0]
        metas_list = res.get("metadatas", [[]])[0]
        dists_list = res.get("distances", [[]])[0]
        for d, m, dist in zip(docs_list, metas_list, dists_list):
            docs.append({"text": d, "metadata": m, "distance": dist})
        logger.debug("Search (with distances) returned %d results", len(docs))
        return docs

    except Exception as e:
        logger.error("Search error: %s", e)
        return []


def search_by_filenames(query: str, filenames: List[str],
                        top_k: int = 5, provider: str = None):
    """按文件名范围搜索"""
    if not query or not query.strip():
        return []

    collection = init_collection()
    if collection is None:
        return []

    try:
        _init_embedding_service()
        logger.debug("Searching in %d files: %s", len(filenames), filenames)
        q_emb = EmbeddingService.embed_texts([query])

        if not q_emb or not q_emb[0]:
            res = collection.query(query_texts=[query], n_results=top_k * 2,
                                   include=["documents", "metadatas"])
        else:
            res = collection.query(query_embeddings=q_emb, n_results=top_k * 2,
                                   include=["documents", "metadatas", "distances"])

        docs = []
        docs_list = res.get("documents", [[]])[0]
        metas_list = res.get("metadatas", [[]])[0]
        for d, m in zip(docs_list, metas_list):
            if m and m.get("source") in filenames:
                docs.append({"text": d, "metadata": m})
                if len(docs) >= top_k:
                    break
        logger.debug("Search by filenames returned %d results", len(docs))
        return docs

    except Exception as e:
        logger.error(f"按文件名搜索错误（数据已保全）: {e}")
        return []


def clear_all():
    """清空向量库"""
    global _collection
    client = get_client()
    try:
        client.delete_collection("lab_docs")
    except Exception:
        pass
    _collection = client.get_or_create_collection("lab_docs")


def delete_documents_by_filename(filename: str):
    """按文件名删除文档"""
    try:
        collection = init_collection()
        if collection is None:
            return 0
        try:
            collection.delete(where={"source": filename})
            return 1
        except Exception:
            pass

        all_docs = collection.get(include=["metadatas"])
        if not all_docs or not all_docs.get("ids"):
            return 0

        ids_to_delete = [
            all_docs["ids"][i] for i, m in enumerate(all_docs.get("metadatas", []))
            if m and m.get("source") == filename
        ]
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            return len(ids_to_delete)
        return 0
    except Exception as e:
        logger.error(f"按文件名删除文档失败: {e}")
        return 0


def get_collection_info():
    """获取向量库信息"""
    collection = init_collection()
    if collection is None:
        return {"error": "Collection not available", "count": 0}
    try:
        count = collection.count()
        _init_embedding_service()
        dim = EmbeddingService.get_embedding_dimension()
        return {
            "count": count,
            "name": collection.name,
            "embedding_dimension": dim,
            "persist_directory": str(CHROMA_DIR),
            "embedding_mode": load_config().get("embedding_mode", "local"),
        }
    except Exception as e:
        return {"error": str(e), "count": 0}


def get_collection():
    """获取向量库集合（别名）"""
    return init_collection()


def shutdown_vector_store():
    """
    Graceful shutdown: clean HNSW cache so next startup rebuilds
    fresh indices from SQLite data. This is the key fix for the
    Windows restart corruption issue.
    """
    global _client, _collection
    try:
        _collection = None
        if _client is not None:
            logger.info("正在关闭 ChromaDB...")
            _client = None

        # Clean HNSW cache dirs on shutdown.
        # On next startup, ChromaDB will rebuild indices from chroma.sqlite3.
        _clean_hnsw_cache()
        logger.info("ChromaDB 已关闭，HNSW 缓存已清理，数据安全存储在 chroma.sqlite3 中")
    except Exception as e:
        logger.error(f"关闭 ChromaDB 时出错: {e}")
