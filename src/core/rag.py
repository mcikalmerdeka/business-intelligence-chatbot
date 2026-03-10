"""RAG (Retrieval-Augmented Generation) functionality"""

import os
import streamlit as st
from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import EMBEDDING_MODEL, FAISS_INDEX_PATH, SCHEMA_PATH_MULTI, logger_rag

logger = logger_rag


def load_schema_description(schema_path: str = None) -> str:
    """Load database schema description from a local file."""
    path = schema_path or SCHEMA_PATH_MULTI
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        st.error(f"Error reading schema file: {e}")
        return ""


def chunk_schema_text(content: str) -> List[str]:
    """
    Split schema text into meaningful chunks
    
    Args:
        content: Full schema text
        
    Returns:
        List of text chunks
    """
    # Split by major headings
    major_sections = content.split('\n#')
    
    chunks = []
    if major_sections[0]:
        chunks.append(major_sections[0])
    
    for section in major_sections[1:]:
        section = '#' + section
        
        # Further split table collection sections
        if "table collections" in section.lower():
            table_sections = section.split('\n ')
            for t_section in table_sections:
                if t_section.strip() and len(t_section) > 50:
                    chunks.append(t_section.strip())
        else:
            chunks.append(section.strip())
    
    return [chunk for chunk in chunks if chunk and len(chunk) > 50]


class RAGEngine:
    """Handle RAG operations for schema retrieval"""

    def __init__(self, recreate_index: bool = False, schema_path: str = None, index_path: str = None):
        """
        Initialize RAG engine.

        Args:
            recreate_index: Whether to recreate the FAISS index
            schema_path: Path to the schema markdown file (defaults to WRS)
            index_path: Path to store/load the FAISS index (defaults to FAISS_INDEX_PATH)
        """
        self.schema_path = schema_path or SCHEMA_PATH_MULTI
        self.index_path = index_path or FAISS_INDEX_PATH
        logger.info(f"Initializing RAG engine (schema={self.schema_path}, recreate={recreate_index})")
        self.embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        self.vector_store = self._load_or_create_index(recreate_index)

    def _load_or_create_index(self, recreate: bool = False) -> FAISS:
        """Load existing FAISS index from disk, or build and save a new one."""
        import shutil

        index_exists = os.path.exists(self.index_path) and os.path.isdir(self.index_path)

        if recreate and index_exists:
            try:
                shutil.rmtree(self.index_path)
                logger.info(f"Removed existing index at {self.index_path} for recreation")
                index_exists = False
            except Exception as e:
                logger.warning(f"Could not remove old index: {e}")

        # Load from disk if available — avoids hitting the embeddings API
        if index_exists:
            try:
                logger.info(f"Loading FAISS index from disk: {self.index_path}")
                vector_store = FAISS.load_local(
                    self.index_path,
                    self.embedding_model,
                    allow_dangerous_deserialization=True,
                )
                logger.info("FAISS index loaded from disk successfully")
                return vector_store
            except Exception as e:
                logger.warning(f"Failed to load index from disk, rebuilding: {e}")

        # Build from schema
        logger.info(f"Building FAISS index from schema: {self.schema_path}")
        schema_content = load_schema_description(self.schema_path)
        if not schema_content:
            logger.error("Failed to load schema description")
            st.error("Failed to load schema description!")
            return None

        chunks = chunk_schema_text(schema_content)
        logger.info(f"Created {len(chunks)} chunks from schema")
        if not chunks:
            logger.error("No valid chunks created from schema")
            st.error("No valid chunks created from schema!")
            return None

        vector_store = FAISS.from_texts(chunks, embedding=self.embedding_model)
        os.makedirs(self.index_path, exist_ok=True)
        vector_store.save_local(self.index_path)
        logger.info(f"FAISS index built and saved to {self.index_path}")
        return vector_store
    
    def retrieve_relevant_schema(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieve relevant schema chunks for a query
        
        Args:
            query: User question
            k: Number of chunks to retrieve
            
        Returns:
            List of relevant document chunks
        """
        if not self.vector_store:
            logger.error("Vector store not initialized")
            st.error("Vector store not initialized!")
            return []
        
        logger.debug(f"Retrieving schema for query: {query[:50]}...")
        results = self.vector_store.similarity_search(query, k=k)
        logger.info(f"Retrieved {len(results)} relevant schema chunks")
        return results
    
    def get_retrieved_schema_text(self, query: str, k: int = 5) -> str:
        """
        Get retrieved schema as concatenated text
        
        Args:
            query: User question
            k: Number of chunks to retrieve
            
        Returns:
            Concatenated schema text
        """
        docs = self.retrieve_relevant_schema(query, k)
        return "\n".join([doc.page_content for doc in docs])
