"""
Configuration utilities
"""
import json
import os
from pathlib import Path
from typing import Dict

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
METADATA_PATH = DATA_DIR / "metadata.json"
CONFIG_PATH = ROOT / "config.json"
DB_PATH = DATA_DIR / "lab_agent.db"

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


DEFAULT_CONFIG: Dict = {
    "provider": "openai",
    "embedding_mode": "local",
    "local_embedding_model": "BAAI/bge-small-zh-v1.5",
    "local_model_cache_dir": "",
    "openai_api_key": "sk-NnC7r0bWpYfmqcmYxFSkuI4YdyFD2M4EJlZ2XXWuMwMA5Ul6",
    "openai_base_url": "https://sg.uiuiapi.com/v1",
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
    "upload_max_size": 104857600
}


def ensure_data_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    if not METADATA_PATH.exists():
        METADATA_PATH.write_text("[]", encoding="utf-8")


def load_config() -> Dict:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
