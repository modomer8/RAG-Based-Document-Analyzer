"""
RAG Compliance Intelligence - FastAPI Application

Main application entry point with all API endpoints:
- Document ingestion and processing
- Hybrid retrieval (BM25 + Dense Vector) with Reciprocal Rank Fusion
- Cross-Encoder re-ranking for top-4 evidence selection
- Compliance audit execution
- SSE streaming pipeline stages
- Health checks
"""

import asyncio
import logging
import os
import sys
import uuid
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Add backend root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings

from app.models.schemas import (
    HealthCheckResponse,
    AuditReportResponse,
    ComplianceStatus,
    AuditFinding,
    EvidenceSnippet,
    DocumentUploadRequest,
)
from app.services.parser import DocumentParser, RecursiveChunker
from app.services.vector_store import QdrantVectorStore, BM25SparseIndex
from app.services.hybrid_retriever import HybridRetriever
from app.services.reranker import CrossEncoderReranker
from app.services.audit_engine import AuditEngine, AuditStage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global pipeline state for SSE streaming
pipeline_state: Dict[str, Any] = {
    "current_stage": "IDLE",
    "progress_percent": 0,
    "stage_details": "Ready",
    "step": "INGESTION",
    "completed_steps": [],
    "vector_count": 0,
}

# LLM client placeholder (None until Ollama/OpenAI client initialized)
llm_client = None


def get_pipeline_state() -> Dict[str, Any]:
    """Get current pipeline state for SSE streaming."""
    return pipeline_state


def update_pipeline_stage(stage: str, progress: int, details: str = ""):
    """Update the global pipeline state."""
    pipeline_state.update({
        "current_stage": stage,
        "progress_percent": progress,
        "stage_details": details,
    })


# ──────────────────────────────────────────────────────────────────────────
# LLM Client Wrapper
# ──────────────────────────────────────────────────────────────────────────

class SimpleLLMClient:
    """Simple LLM client placeholder for structured output."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from LLM - placeholder returning structured prompt guide."""
        # In production, this would call Ollama or OpenAI
        # For now, return a placeholder that indicates structured output
        return '{"control_id": "placeholder", "control_name": "placeholder", "status": "REQUIRES_REVIEW", "confidence_score": 0.5, "justification": "LLM placeholder - install Ollama or configure OpenAI key", "citations": []}'


# ──────────────────────────────────────────────────────────────────────────
# Lifespan / Startup
# ──────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler for startup/shutdown.
    Initializes components that need to be alive for the app to function.
    """
    # Initialize LLM client
    global llm_client
    llm_client = SimpleLLMClient(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("LLM_MODEL", "llama3.2")
    )
    
    # Try to initialize Qdrant vector store
    from backend.app.services.vector_store import QdrantVectorStore
    vector_store = QdrantVectorStore(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
        api_key=None,
        collection_name="compliance_audit",
        embedding_dim=384,
    )
    
    # Store in app state
    app.state.vector_store = vector_store
    app.state.hybrid_retriever = None
    app.state.bm25_index = None
    app.state.audit_engine = None
    app.state.chunker = RecursiveChunker()
    app.state.parser = DocumentParser()
    
    logger.info("RCI Backend started successfully")
    logger.info(f"Vector store: {vector_store.collection_name}")
    
    yield
    
    logger.info("RCI Backend shutting down")


# ──────────────────────────────────────────────────────────────────────────
# FastAPI Application Setup
# ──────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RCI - RAG Compliance Intelligence API",
    description="""
    Enterprise AI platform for automated RFP & Compliance Auditing.
    
    Features:
    - Hybrid search (BM25 + Dense Vector) with Reciprocal Rank Fusion
    - Cross-Encoder re-ranking for top-4 evidence selection
    - Structured LLM reasoning with Pydantic-constrained JSON output
    - Traceable audit findings with source citations
    - Ragas evaluation harness
    """,
    version="1.0.0",
    terms_of_service="https://freebuff.com/terms",
    contact={
        "name": "RCI Support",
        "email": "support@freebuff.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """System health check endpoint."""
    vector_store = getattr(app.state, "vector_store", None)
    vector_count = 0
    model_loaded = False
    qdrant_connected = False
    
    if vector_store is not None:
        info = vector_store.get_collection_info()
        if info:
            vector_count = info.get("vectors_count", 0)
        qdrant_connected = True
    
    # Check if model is available
    try:
        from sentence_transformers import SentenceTransformer
        _ = SentenceTransformer("BAAI/bge-small-en-v1.5")
        model_loaded = True
    except Exception:
        model_loaded = False
    
    return HealthCheckResponse(
        status="healthy" if qdrant_connected or model_loaded else "degraded",
        vector_count=vector_count,
        model_loaded=model_loaded,
        qdrant_connected=qdrant_connected,
    )


@app.post("/api/v1/documents/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    request: Request = None,
) -> Dict[str, Any]:
    """
    Ingest and process uploaded documents.
    
    Workflow:
    1. Parse PDF/DOCX files
    2. Recursive chunking (512 tokens, 64 overlap)
    3. Generate embeddings (BGE-small-en-v1.5)
    4. Index into Qdrant + BM25 sparse index
    """
    pipeline_state.update({
        "current_stage": "INGESTION",
        "progress_percent": 5,
        "stage_details": "Starting document ingestion...",
        "step": "INGESTION",
        "completed_steps": [],
    })
    
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    try:
        parser = getattr(app.state, "parser", DocumentParser())
        chunker = getattr(app.state, "chunker", RecursiveChunker())
        vector_store = getattr(app.state, "vector_store", None)
        
        all_chunks = []
        processed_files = []
        
        for uploaded_file in files:
            file_id = str(uuid.uuid4())
            filename = uploaded_file.filename or "unknown"
            
            logger.info(f"Processing uploaded file: {filename}")
            
            # Save uploaded file temporarily
            temp_path = f"/tmp/rci_{file_id}_{filename}"
            content = await uploaded_file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            
            try:
                # Step 1: Extract text
                pipeline_state.update({
                    "current_stage": "PARSING",
                    "progress_percent": 15,
                    "stage_details": f"Parsing {filename}...",
                    "step": "PARSING",
                    "completed_steps": ["INGESTION"],
                })
                
                documents = parser.extract_text(temp_path)
                
                # Step 2: Chunk with metadata
                pipeline_state.update({
                    "current_stage": "CHUNKING",
                    "progress_percent": 30,
                    "stage_details": f"Chunking {filename}...",
                    "step": "CHUNKING",
                    "completed_steps": ["INGESTION", "PARSING"],
                })
                
                document_id = file_id
                chunks = chunker.chunk_documents(
                    documents=documents,
                    document_id=document_id,
                    filename=filename,
                )
                
                all_chunks.extend(chunks)
                processed_files.append(filename)
                
                # Step 3: Index into Qdrant (dense vectors)
                if vector_store is not None and vector_store.client is not None:
                    pipeline_state.update({
                        "current_stage": "VECTOR_INDEX",
                        "progress_percent": 55,
                        "stage_details": "Indexing vectors into Qdrant...",
                        "step": "VECTOR_INDEX",
                        "completed_steps": ["INGESTION", "PARSING", "CHUNKING"],
                    })
                    
                    # Prepare points for Qdrant upsert
                    points = []
                    bm25_tokenized = []
                    bm25_metadata = []
                    bm25_ids = []
                    
                    for chunk_idx, chunk in enumerate(chunks):
                        chunk_text = chunk["text"]
                        chunk_metadata = chunk["metadata"]
                        
                        # Generate embedding
                        embedding = vector_store._get_embedding(chunk_text)
                        
                        # Create Qdrant point
                        from qdrant_client.models import PointStruct
                        point = PointStruct(
                            id=hash(chunk_text) % (2**31),
                            vector={
                                "dense": embedding,
                                "bm25": [chunk_text.lower().split()],  # sparse format
                            },
                            payload={
                                "document_name": filename,
                                "chunk_text": chunk_text,
                                "page_number": chunk_metadata.get("page_number"),
                                "chunk_id": chunk_metadata.get("chunk_id"),
                                "chunk_index": chunk_metadata.get("chunk_index"),
                                "document_id": document_id,
                            },
                        )
                        points.append(point)
                        
                        # BM25 metadata
                        bm25_tokenized.append(chunk_text.lower().split())
                        bm25_metadata.append({
                            "document_name": filename,
                            "chunk_text": chunk_text,
                            "chunk_id": chunk_metadata.get("chunk_id"),
                        })
                        bm25_ids.append(chunk_metadata.get("chunk_id", f"chunk-{chunk_idx}"))
                    
                    # Upsert to Qdrant
                    if points:
                        vector_store.upsert_points(points)
                    
                    # Initialize BM25 index
                    if vector_store.bm25 is None:
                        vector_store.bm25 = BM25SparseIndex(bm25_tokenized)
                        vector_store.metadata = bm25_metadata
                        vector_store.document_ids = bm25_ids
                    else:
                        # Add to existing index
                        vector_store.add_documents(
                            bm25_tokenized[:100],  # Limit for demo
                            bm25_metadata[:100],
                            bm25_ids[:100],
                        )
                
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                # Continue with other files
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                continue
        
        # Update hybrid retriever if we have new chunks
        if all_chunks and vector_store is not None:
            # Reinitialize hybrid retriever with new data
            from sentence_transformers import SentenceTransformer
            
            try:
                hybrid_retriever = HybridRetriever(
                    qdrant_store=vector_store,
                    bm25_index=vector_store.bm25,
                    dense_model=SentenceTransformer("BAAI/bge-small-en-v1.5"),
                    reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
                    top_k_retrieve=20,
                    top_k_rerank=4,
                )
                app.state.hybrid_retriever = hybrid_retriever
                
                total_chunks = len(all_chunks)
                pipeline_state.update({
                    "current_stage": "COMPLETE",
                    "progress_percent": 100,
                    "stage_details": f"Ingestion complete: {total_chunks} chunks indexed",
                    "step": "COMPLETE",
                    "completed_steps": ["INGESTION", "PARSING", "CHUNKING", "VECTOR_INDEX"],
                })
                
                return {
                    "message": f"Document ingestion complete",
                    "total_files": len(processed_files),
                    "total_chunks": total_chunks,
                    "stage": "COMPLETE",
                    "pipeline_state": pipeline_state,
                }
                
            except Exception as e:
                logger.error(f"Failed to initialize hybrid retriever: {e}")
                raise
        
        pipeline_state.update({
            "current_stage": "COMPLETE",
            "progress_percent": 100,
            "stage_details": "Ingestion complete (no vector store)",
            "step": "COMPLETE",
            "completed_steps": ["INGESTION", "PARSING", "CHUNKING"],
        })
        
        return {
            "message": "Document ingestion processed",
            "total_files": len(processed_files),
            "total_chunks": len(all_chunks),
            "stage": "COMPLETE",
        }
        
    except Exception as e:
        logger.error(f"Document upload endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/audit/execute")
async def execute_audit(
    request: Request,
    checklist: Optional[List[Dict[str, Any]]] = None,
    control_filter: Optional[List[str]] = None,
) -> AuditReportResponse:
    """
    Execute compliance audit against indexed documents.
    
    End-to-end audit pipeline:
    1. Retrieve top evidence per control via hybrid search
    2. Cross-Encoder reranking
    3. LLM reasoning with Pydantic JSON output
    4. Aggregated audit report
    """
    pipeline_state.update({
        "current_stage": "INGESTION",
        "progress_percent": 0,
        "stage_details": "Starting audit execution...",
        "step": "INGESTION",
    })
    
    try:
        audit_engine = AuditEngine(
            hybrid_retriever=getattr(app.state, "hybrid_retriever", None),
            llm_client=llm_client,
            model_name=settings.llm_model_name,
        )
        
        # Execute audit
        report = audit_engine.execute_audit(
            checklist=checklist,
            control_filter=control_filter,
            top_evidence_per_control=4,
        )
        
        # Update pipeline state
        pipeline_state.update({
            "current_stage": "COMPLETE",
            "progress_percent": 100,
            "stage_details": "Audit execution complete",
            "step": "COMPLETE",
        })
        
        return report
        
    except Exception as e:
        logger.error(f"Audit execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/audit/stream")
async def audit_stream():
    """
    Server-Sent Events (SSE) stream for real-time pipeline stage progression.
    
    Streams: INGESTION -> PARSING -> CHUNKING -> VECTOR_INDEX ->
    HYBRID_RETRIEVAL -> RERANKING -> LLM_REASONING -> COMPLETE
    """
    
    async def event_generator():
        """Generate SSE events based on pipeline state changes."""
        max_iterations = 120  # 2 minutes max at 1s intervals
        iteration = 0
        
        while iteration < max_iterations:
            current = get_pipeline_state()
            
            # Format SSE event
            event_data = current
            event_str = f"data: {str(event_data)}\n\n"
            
            yield event_str
            
            # Check if complete
            if current.get("current_stage") in ("COMPLETE", "IDLE"):
                # Send final completion event
                final_event = 'data: {"current_stage": "COMPLETE", "progress_percent": 100, "detail": "Audit pipeline complete"}\n\n'
                yield final_event
                break
            
            # Wait and check again
            await asyncio.sleep(1.0)
            iteration += 1
        
        if iteration >= max_iterations:
            # Timeout - send status
            timeout_event = 'data: {"current_stage": "TIMEOUT", "progress_percent": 0, "detail": "Stream timeout"}\n\n'
            yield timeout_event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


# ──────────────────────────────────────────────────────────────────────────
# Utility endpoint for pipeline control
# ──────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/pipeline/control")
async def pipeline_control(
    action: str,
    value: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Control pipeline stages for testing/debugging.
    
    Supported actions: reset, advance, set_stage
    """
    try:
        if action == "reset":
            pipeline_state.update({
                "current_stage": "IDLE",
                "progress_percent": 0,
                "stage_details": "Ready",
                "step": "INGESTION",
                "completed_steps": [],
            })
            return {"status": "reset", "pipeline_state": pipeline_state}
        
        elif action == "set_stage":
            if value and "stage" in value:
                pipeline_state.update({
                    "current_stage": value["stage"],
                    "progress_percent": value.get("progress", 0),
                    "stage_details": value.get("details", ""),
                    "step": value.get("step", "INGESTION"),
                    "completed_steps": value.get("completed_steps", []),
                })
                return {"status": "stage_set", "pipeline_state": pipeline_state}
        
        elif action == "advance":
            current = pipeline_state.get("step", "INGESTION")
            steps = pipeline_state.get("completed_steps", [])
            
            # Advance to next step
            step_order = [
                "INGESTION", "PARSING", "CHUNKING", 
                "VECTOR_INDEX", "HYBRID_RETRIEVAL", 
                "RERANKING", "LLM_REASONING", "COMPLETE"
            ]
            
            if current in step_order:
                current_idx = step_order.index(current)
                if current_idx < len(step_order) - 1:
                    next_step = step_order[current_idx + 1]
                    new_progress = int((current_idx + 1) / len(step_order) * 100)
                    
                    new_completed = steps + [current] if current not in steps else steps
                    
                    pipeline_state.update({
                        "step": next_step,
                        "progress_percent": new_progress,
                        "stage_details": f"Advancing to {next_step}",
                        "completed_steps": new_completed,
                    })
            
            return {"status": "advanced", "pipeline_state": pipeline_state}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    
    except Exception as e:
        logger.error(f"Pipeline control failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))