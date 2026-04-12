"""Application settings and configuration"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Database Configuration — Neon Postgres
# DATABASE_URL is the primary connection method (pooler endpoint for Neon)
DATABASE_URL = os.getenv("DATABASE_URL")

# Model Configuration
MODEL_OPTIONS = {
    "GPT-4.1 mini": "gpt-4.1-mini",
    "Claude Haiku 4.5": "claude-haiku-4-5-20251001"
}

# Embedding Model
EMBEDDING_MODEL = "text-embedding-3-large"

# Vector Store base directory
_FAISS_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faiss_index_store")
FAISS_INDEX_PATH = _FAISS_BASE  # kept for backward compat (single-table RAG)

# Multi-table dataset configurations
DATASET_CONFIGS = {
    "WRS EHR Database": {
        "schema_path": "datasets/dataset_multiple_tables/wrs_ehr_db/ehr_database_docs.md",
        "schema_prefix": "wrs",
        "faiss_path": os.path.join(_FAISS_BASE, "wrs"),
    },
    "Olist E-Commerce": {
        "schema_path": "datasets/dataset_multiple_tables/olist_db/olist_database_docs.md",
        "schema_prefix": "olist",
        "faiss_path": os.path.join(_FAISS_BASE, "olist"),
    },
}

# App Configuration
SHOW_DEBUG_INFO = True  # Show SQL queries and results for debugging
