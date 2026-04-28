"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-do-not-use-in-production")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def test_config():
    """Test configuration fixture"""
    return {
        "provider": "openai",
        "embedding_mode": "local",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "temperature": 0.7,
        "top_k": 5,
    }


@pytest.fixture
def mock_openai_key(monkeypatch):
    """Mock OpenAI API key for testing"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-for-testing")


@pytest.fixture
def mock_secret_key(monkeypatch):
    """Mock secret key for testing"""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only")
