"""
RAG Compliance Intelligence - Configuration Settings
"""
from pydantic import Field, BaseModel
from typing import List, Optional
import os

class Settings(BaseModel):
    # Qdrant Configuration
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    
    # Embedding Model
    embedding_model_name: str = Field(default="BAAI/bge-small-en-v1.5", env="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=384, env="EMBEDDING_DIMENSIONS")
    
    # Reranking Model
    reranker_model_name: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2", env="RERANKER_MODEL")
    
    # LLM Configuration
    llm_model_name: str = Field(default="llama3.2", env="LLM_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    
    # Application
    app_name: str = Field(default="RCI-API", env="APP_NAME")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # SSE Stages
    pipeline_stages: List[str] = Field(
        default=[
            "INGESTION", "PARSING", "CHUNKING", 
            "VECTOR_INDEX", "HYBRID_RETRIEVAL", 
            "RERANKING", "LLM_REASONING", "COMPLETE"
        ]
    )
    
    class Config:
        arbitrary_types = True

# Singleton instance
settings = Settings()

# Derived settings
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", settings.embedding_model_name)
RERANKER_MODEL_PATH = os.getenv("RERANKER_MODEL_PATH", settings.reranker_model_name)