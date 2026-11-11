"""
RAG Compliance Intelligence - Vector Store Service

Handles Qdrant vector database operations:
- Collection management (create/update)
- Vector upsert (embeddings + metadata)
- Hybrid search capabilities (dense + sparse)
- Similarity search with filters
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    Range,
)
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Qdrant vector store for compliance document embeddings."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        collection_name: str = "compliance_audit",
        embedding_dim: int = 384,
    ):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        try:
            self.client = QdrantClient(
                host=host, port=port, api_key=api_key
            )
            self._ensure_collection()
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant at {host}:{port}: {e}")
            self.client = None

    def _ensure_collection(self):
        """Create or verify the collection exists with correct settings."""
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return
        
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE,
                    ),
                    sparse_vectors={"bm25": "BM25"},
                )
                logger.info(
                    f"Created Qdrant collection '{self.collection_name}' "
                    f"with dimension {self.embedding_dim}"
                )
            else:
                logger.info(
                    f"Qdrant collection '{self.collection_name}' already exists"
                )
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a text string."""
        try:
            model = SentenceTransformer("BAAI/bge-small-en-v1.5")
            embedding = model.encode(text, normalize_embeddings=True).tolist()
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dim

    def upsert_points(
        self,
        points: List[PointStruct],
        wait: bool = True,
    ) -> bool:
        """Upload points (vectors + metadata) to Qdrant."""
        if self.client is None:
            logger.error("Qdrant client not connected")
            return False
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=wait,
            )
            logger.info(
                f"Upserted {len(points)} points to "
                f"collection '{self.collection_name}'"
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant upsert failed: {e}")
            return False

    def search(
        self,
        query_vector: List[float],
        limit: int = 20,
        filter_conditions: Optional[Filter] = None,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Perform dense vector similarity search."""
        if self.client is None:
            return []
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                filter=filter_conditions,
                score_threshold=score_threshold,
            )
            return results
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get collection statistics and info."""
        if self.client is None:
            return None
        
        try:
            info = self.client.get_collection(
                collection_name=self.collection_name
            )
            return {
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "config": {
                    "vectors": info.config.vectors,
                } if info.config else None,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None


class BM25SparseIndex:
    """BM25 sparse index for keyword-based search within document chunks."""

    def __init__(self, tokenized_documents: List[List[str]]):
        self.bm25 = BM25Okapi(tokenized_documents)
        self.metadata: List[Dict[str, Any]] = []
        self.document_ids: List[str] = []

    def add_documents(
        self, 
        tokenized_docs: List[List[str]], 
        metadata: List[Dict[str, Any]],
        doc_ids: List[str],
    ):
        """Add tokenized documents to the BM25 index."""
        self.metadata.extend(metadata)
        self.document_ids.extend(doc_ids)
        # Refit BM25 with new documents
        if self.bm25 is None:
            self.bm25 = BM25Okapi(tokenized_docs)
        else:
            # BM25Okapi doesn't support incremental updates easily
            # Recreate the index
            self.bm25 = BM25Okapi(tokenized_docs)

    def search(self, query: str, top_n: int = 20) -> List[Dict[str, Any]]:
        """Search using BM25 keyword matching."""
        if not self.bm25 or not self.document_ids:
            return []
        
        try:
            tokenized_query = query.lower().split()
            scores = self.bm25.get_scores(tokenized_query)
            
            # Get top N indices
            import numpy as np
            top_indices = np.argsort(-scores)[:top_n]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    results.append({
                        "id": self.document_ids[idx],
                        "score": float(scores[idx]),
                        "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
                    })
            
            return results
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []