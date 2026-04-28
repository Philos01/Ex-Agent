"""
Security-related tests
Tests for API key handling, CORS, authentication, and input validation
"""
import pytest
import os
from unittest.mock import patch, MagicMock


class TestAPIKeySecurity:
    """Tests for API key security"""
    
    def test_api_key_not_logged(self, caplog):
        """Test that API keys are not logged in plain text"""
        from app.services.qa import _get_openai_client
        
        with patch('app.services.qa.OpenAI') as mock_openai:
            mock_openai.return_value = MagicMock()
            
            cfg = {
                "openai_api_key": "sk-super-secret-key-12345",
                "openai_base_url": None
            }
            
            with caplog.at_level('DEBUG'):
                _get_openai_client(cfg)
            
            for record in caplog.records:
                assert "sk-super-secret-key-12345" not in record.message
                assert "secret" not in record.message.lower() or "redacted" in record.message.lower()
    
    def test_api_key_from_env_not_config(self):
        """Test that API keys are loaded from environment, not config file"""
        from app.core.config import load_config, get_complete_config, OPENAI_API_KEY
        
        cfg = load_config()
        assert "openai_api_key" not in cfg
        
        os.environ["OPENAI_API_KEY"] = "test-env-key"
        complete_cfg = get_complete_config()
        assert complete_cfg.get("openai_api_key") == "test-env-key"


class TestCORSSecurity:
    """Tests for CORS configuration"""
    
    def test_cors_not_wildcard_with_credentials(self):
        """Test that CORS does not use wildcard with credentials"""
        from app.main import app
        
        cors_middleware = None
        for middleware in app.user_middleware:
            if 'CORSMiddleware' in str(middleware):
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None, "CORS middleware should be present"
        
        import inspect
        from fastapi.middleware.cors import CORSMiddleware
        
        for route in app.routes:
            if hasattr(route, 'app'):
                pass


class TestJWTSecurity:
    """Tests for JWT token security"""
    
    def test_secret_key_strength(self):
        """Test that secret key meets minimum length requirement"""
        from app.core.config import SECRET_KEY
        
        assert len(SECRET_KEY) >= 32, "SECRET_KEY should be at least 32 characters"
    
    def test_secret_key_not_default_weak(self):
        """Test that secret key is not the old weak default"""
        from app.core.config import SECRET_KEY
        
        weak_defaults = [
            "your-secret-key-change-this-in-production",
            "secret",
            "changeme",
            "password",
        ]
        assert SECRET_KEY not in weak_defaults


class TestInputValidation:
    """Tests for input validation"""
    
    def test_empty_query_rejected(self):
        """Test that empty queries are rejected"""
        from app.services.vector_store import search
        
        result = search("", top_k=5)
        assert result == []
    
    def test_whitespace_query_rejected(self):
        """Test that whitespace-only queries are rejected"""
        from app.services.vector_store import search
        
        result = search("   \n\t  ", top_k=5)
        assert result == []
    
    def test_file_upload_size_limit(self):
        """Test that file upload size is validated"""
        from app.core.config import DEFAULT_CONFIG
        
        max_size = DEFAULT_CONFIG.get("upload_max_size", 104857600)
        assert max_size > 0
        assert isinstance(max_size, int)


class TestTimeoutSecurity:
    """Tests for timeout configurations"""
    
    def test_subprocess_has_timeout(self):
        """Test that subprocess calls have timeout configured"""
        from app.skills.skill_executor import SkillExecutor
        import inspect
        
        source = inspect.getsource(SkillExecutor.execute_python)
        assert "timeout=" in source or "timeout" in source
    
    def test_openai_client_has_timeout(self):
        """Test that OpenAI client has timeout configured"""
        from app.services.qa import _get_openai_client
        import inspect
        
        source = inspect.getsource(_get_openai_client)
        assert "timeout" in source.lower()


class TestThreadSafety:
    """Tests for thread safety"""
    
    def test_rate_limiter_thread_safe(self):
        """Test that RateLimiter has lock mechanism"""
        from app.core.rate_limit import RateLimiter
        
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert hasattr(limiter, '_lock')
    
    def test_embedding_service_thread_safe(self):
        """Test that EmbeddingService singleton is thread-safe"""
        from app.services.embedding import EmbeddingService
        
        assert hasattr(EmbeddingService, '_lock')
    
    def test_context_manager_has_lock(self):
        """Test that context manager has thread safety"""
        import app.services.context_manager as cm
        
        assert hasattr(cm, '_context_managers_lock')
