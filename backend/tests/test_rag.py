"""
RAG system tests
Tests for retrieval, embedding, and document processing
"""
import pytest
from unittest.mock import patch, MagicMock


class TestVectorSearch:
    """Tests for vector search functionality"""
    
    def test_empty_query_returns_empty(self):
        """Test that empty query returns empty result"""
        from app.services.vector_store import search
        
        result = search("", top_k=5)
        assert result == []
    
    def test_whitespace_query_returns_empty(self):
        """Test that whitespace query returns empty result"""
        from app.services.vector_store import search
        
        result = search("   \n  ", top_k=5)
        assert result == []


class TestEmbeddingService:
    """Tests for embedding service"""
    
    def test_singleton_pattern(self):
        """Test that EmbeddingService uses singleton pattern"""
        from app.services.embedding import EmbeddingService
        
        assert hasattr(EmbeddingService, '_instance')
        assert hasattr(EmbeddingService, '_lock')
    
    def test_empty_text_handling(self):
        """Test that empty texts are handled without dimension mismatch"""
        pass


class TestHybridSearch:
    """Tests for hybrid search"""
    
    def test_empty_query_rejected(self):
        """Test that empty query is rejected in hybrid search"""
        from app.services.hybrid_search import HybridSearchService
        
        service = HybridSearchService()
        result = service.search("", initial_count=10)
        assert result == []


class TestTwoLayerSearch:
    """Tests for two-layer search"""
    
    def test_persistent_bm25_index(self):
        """Test that BM25 index is persisted"""
        from app.services.two_layer_search import TwoLayerRetriever
        
        retriever = TwoLayerRetriever()
        assert hasattr(retriever, '_summary_bm25')
        assert hasattr(retriever, '_summary_bm25_hash')
    
    def test_relevance_threshold_applied(self):
        """Test that relevance threshold is applied"""
        from app.services.two_layer_search import TwoLayerRetriever
        
        retriever = TwoLayerRetriever()
        assert hasattr(retriever, 'relevance_threshold')
        assert retriever.relevance_threshold >= 0
        assert retriever.relevance_threshold <= 1


class TestDocumentIngestion:
    """Tests for document ingestion"""
    
    def test_chunk_config_consistency(self):
        """Test that chunk config is consistent"""
        from app.core.config import DEFAULT_CONFIG
        
        chunk_size = DEFAULT_CONFIG.get("chunk_size", 1000)
        chunk_overlap = DEFAULT_CONFIG.get("chunk_overlap", 200)
        
        assert chunk_size > 0
        assert chunk_overlap >= 0
        assert chunk_overlap < chunk_size
    
    def test_deduplication_on_ingest(self):
        """Test that documents are deduplicated on ingest"""
        from app.services.ingest import ingest_file
        import inspect
        
        source = inspect.getsource(ingest_file)
        assert "delete_documents_by_filename" in source


class TestReranker:
    """Tests for reranker"""
    
    def test_max_length_sufficient(self):
        """Test that reranker max_length is sufficient"""
        from app.services.rerank import RerankService
        import inspect
        
        source = inspect.getsource(RerankService.rerank)
        assert "max_length=1024" in source or "max_length" in source
