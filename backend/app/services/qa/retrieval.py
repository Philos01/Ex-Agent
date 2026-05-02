"""
Document retrieval — orchestrates parent / two-layer / hybrid / vector search strategies.
"""
import logging
from app.services.vector_store import search
from app.core.config import get_complete_config

logger = logging.getLogger(__name__)


def retrieve_documents(question: str, provider: str = "openai", top_k: int = 5):
    """
    Retrieve relevant documents using the configured search strategy.
    Falls back through: parent document → two-layer → hybrid → vector.
    """
    cfg = get_complete_config()

    logger.debug("[retrieval] Starting for: %s...", question[:50])

    pdr_config = cfg.get("parent_document_retrieval", {})
    use_parent_retrieval = pdr_config.get("enabled", False)

    if use_parent_retrieval:
        try:
            from app.services.parent_retriever import get_parent_retriever
            retriever = get_parent_retriever()
            results = retriever.retrieve(question)
            if results:
                logger.info("Parent document retrieval returned %d results", len(results))
                return results
            logger.info("Parent document retrieval returned no results, falling back to hybrid")
        except Exception as e:
            logger.error("Parent document retrieval failed: %s", e, exc_info=True)

    summary_config = cfg.get("summary_search", {})
    use_two_layer = summary_config.get("enabled", False)

    if use_two_layer:
        try:
            from app.services.two_layer_search import two_layer_search
            logger.info("Using two-layer search")
            result = two_layer_search(question, provider=provider)
            logger.info("Two-layer search returned %d results", len(result))
            return result
        except Exception as e:
            logger.error("Two-layer search failed: %s", e, exc_info=True)

    hybrid_config = cfg.get("hybrid_search", {})
    use_hybrid = hybrid_config.get("enabled", True)

    if use_hybrid:
        try:
            from app.services.hybrid_search import hybrid_search
            logger.info("Using hybrid search")
            return hybrid_search(question, provider=provider)
        except Exception as e:
            logger.error("Hybrid search failed, falling back to vector: %s", e)

    logger.info("Using vector search")
    return search(question, top_k=top_k, provider=provider)
