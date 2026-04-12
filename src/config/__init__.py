"""Configuration package for the Business Intelligence Chatbot"""

from .settings import (
    DATABASE_URL,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    MODEL_OPTIONS,
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
    DATASET_CONFIGS,
    SHOW_DEBUG_INFO,
)
from .logging_config import setup_logger, get_logger, logger_db, logger_rag, logger_llm, logger_app

__all__ = [
    "DATABASE_URL",
    "DATASET_CONFIGS",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "MODEL_OPTIONS",
    "EMBEDDING_MODEL",
    "FAISS_INDEX_PATH",
    "SHOW_DEBUG_INFO",
    "setup_logger",
    "get_logger",
    "logger_db",
    "logger_rag",
    "logger_llm",
    "logger_app",
]
