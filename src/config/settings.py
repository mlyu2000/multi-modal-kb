#!/usr/bin/env python3
"""Configuration settings for Trading KB."""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Paths
DATA_DIR = PROJECT_ROOT / "data"
VIDEOS_DIR = DATA_DIR / "videos"
EXTRACTED_DIR = DATA_DIR / "extracted"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = PROJECT_ROOT / "db"
CHROMA_DIR = DB_DIR / "chroma"

# Database paths
SQLITE_PATH = DB_DIR / "metadata.sqlite"


class Settings:
    """Application settings loaded from environment and config."""
    
    def __init__(self):
        # Neo4j
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "")
        
        # ChromaDB
        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(CHROMA_DIR))
        
        # SQLite
        self.sqlite_path = os.getenv("SQLITE_PATH", str(SQLITE_PATH))
        
        # Qwen model
        self.qwen_api_base = os.getenv("QWEN_API_BASE", "http://localhost:11434/v1")
        self.qwen_api_key = os.getenv("QWEN_API_KEY", "local")
        self.qwen_model = os.getenv("QWEN_MODEL", "qwen3-next-80b")
        
        # Gemma model
        self.gemma_api_base = os.getenv("GEMMA_API_BASE", "http://localhost:11434/v1")
        self.gemma_api_key = os.getenv("GEMMA_API_KEY", "local")
        self.gemma_model = os.getenv("GEMMA_MODEL", "gemma4-31b")
        
        # Processing settings
        self.whisper_model = os.getenv("WHISPER_MODEL", "medium")
        self.device = os.getenv("DEVICE", "auto")
        self.frame_interval_seconds = int(os.getenv("FRAME_INTERVAL_SECONDS", "5"))
        self.segment_min_seconds = int(os.getenv("SEGMENT_MIN_SECONDS", "60"))
        self.segment_max_seconds = int(os.getenv("SEGMENT_MAX_SECONDS", "180"))
    
    def to_dict(self):
        """Return settings as dictionary."""
        return {
            "neo4j_uri": self.neo4j_uri,
            "neo4j_user": self.neo4j_user,
            "neo4j_password": self.neo4j_password,
            "chroma_persist_dir": self.chroma_persist_dir,
            "sqlite_path": self.sqlite_path,
            "qwen_api_base": self.qwen_api_base,
            "qwen_api_key": self.qwen_api_key,
            "qwen_model": self.qwen_model,
            "gemma_api_base": self.gemma_api_base,
            "gemma_api_key": self.gemma_api_key,
            "gemma_model": self.gemma_model,
            "whisper_model": self.whisper_model,
            "device": self.device,
            "frame_interval_seconds": self.frame_interval_seconds,
            "segment_min_seconds": self.segment_min_seconds,
            "segment_max_seconds": self.segment_max_seconds,
        }


# Global settings instance
settings = Settings()


def load_config_yaml(path: str = None) -> dict:
    """Load config from YAML file."""
    if path is None:
        path = PROJECT_ROOT / "config.yaml"
    
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}
