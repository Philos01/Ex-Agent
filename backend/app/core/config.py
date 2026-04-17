"""
Configuration utilities with security auditing
"""
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Set up security logger
security_logger = logging.getLogger("security_audit")
security_logger.setLevel(logging.INFO)
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[SECURITY] %(asctime)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
METADATA_PATH = DATA_DIR / "metadata.json"
CONFIG_PATH = ROOT / "config.json"
DB_PATH = DATA_DIR / "lab_agent.db"

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# SQLAlchemy Base
Base = declarative_base()

# Database configuration - SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DB_PATH}"
)

# SQLAlchemy Engine for SQLite
# SQLite doesn't need connection pooling, use simple configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 特殊配置
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# JWT Configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "your-secret-key-change-this-in-production-please-use-a-strong-key"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# OpenAI API Configuration - ONLY from environment variables, NO persistence
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# API key access tracking
_api_key_access_count = 0
_last_api_key_access: Optional[datetime] = None

DEFAULT_CONFIG: Dict = {
    "provider": "openai",
    "embedding_mode": "local",
    "local_embedding_model": "BAAI/bge-small-zh-v1.5",
    "local_model_cache_dir": "",
    "openai_base_url": OPENAI_BASE_URL,
    "openai_embedding_model": "text-embedding-3-small",
    "openai_chat_model": "gpt-3.5-turbo",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "",
    "chunk_size": 1500,
    "chunk_overlap": 100,
    "temperature": 0.7,
    "top_k": 5,
    "top_p": 0.9,
    "max_tokens": 2048,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "max_history": 10,
    "upload_max_size": 104857600,
    "allow_user_registration": False,
    "allow_pdf_conversion": False,
    "hybrid_search": {
        "enabled": True,
        "initial_retrieve_count": 20,
        "final_select_count": 3,
        "bm25_weight": 0.5,
        "embedding_weight": 0.5,
        "rerank_model": "BAAI/bge-reranker-v2-m3",
        "enable_query_rewrite": True
    },
    "summary_search": {
        "enabled": True,
        "relevance_threshold": 0.6,
        "summary_top_k": 5,
        "content_top_k": 3,
        "auto_generate_summary": True,
        "enable_query_rewrite": True
    },
    "context_management": {
        "enabled": True,
        "max_history_rounds": 5,
        "exclude_error_messages": True,
        "exclude_questionable_messages": False
    }
}


def ensure_data_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    if not METADATA_PATH.exists():
        METADATA_PATH.write_text("[]", encoding="utf-8")


def load_config() -> Dict:
    """Load configuration from disk, excluding sensitive credentials"""
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        # Ensure API key is not loaded from disk
        if "openai_api_key" in cfg:
            del cfg["openai_api_key"]
        return cfg
    except Exception:
        # Return a copy of DEFAULT_CONFIG without API key
        cfg = DEFAULT_CONFIG.copy()
        if "openai_api_key" in cfg:
            del cfg["openai_api_key"]
        return cfg


def save_config(cfg: Dict):
    """Save configuration to disk, ensuring sensitive credentials are NOT saved"""
    # Create a copy of the config to avoid modifying the original
    safe_cfg = cfg.copy()
    # Remove sensitive fields before saving
    if "openai_api_key" in safe_cfg:
        del safe_cfg["openai_api_key"]
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(safe_cfg, f, indent=2, ensure_ascii=False)


def _log_api_key_access():
    """Log API key access for security auditing"""
    global _api_key_access_count, _last_api_key_access
    
    _api_key_access_count += 1
    _last_api_key_access = datetime.now()
    
    security_logger.info(
        f"API key accessed - Total accesses: {_api_key_access_count}, "
        f"Last access: {_last_api_key_access.isoformat()}"
    )
    
    # Check for abnormal access patterns (example: more than 100 accesses per hour)
    # This is a simple heuristic - in production, you may want more sophisticated monitoring
    if _api_key_access_count > 100:
        security_logger.warning(
            f"High API key access count detected: {_api_key_access_count}"
        )


def get_complete_config() -> Dict:
    """Get complete configuration with sensitive credentials from environment variables"""
    cfg = load_config()
    # Add sensitive credentials from environment variables
    if OPENAI_API_KEY:
        _log_api_key_access()
        cfg["openai_api_key"] = OPENAI_API_KEY
    if OPENAI_BASE_URL:
        cfg["openai_base_url"] = OPENAI_BASE_URL
    return cfg


def get_api_key_access_stats() -> Dict:
    """Get statistics about API key access"""
    return {
        "access_count": _api_key_access_count,
        "last_access": _last_api_key_access.isoformat() if _last_api_key_access else None
    }
