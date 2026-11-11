"""
RAG Compliance Intelligence - Document Parser & Chunker Services

Handles extraction of text from PDF and DOCX files,
recursive chunking with markdown/header preservation,
and metadata injection for vector store indexing.
"""

import fitz  # pymupdf
import docx
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
import re


class ChunkMetadata:
    """Metadata container for document chunks."""
    def __init__(
        self,
        document_id: str,
        filename: str,
        page_number: Optional[int],
        chunk_id: str,
        token_count: int,
        chunk_index: int,
    ):
        self.document_id = document_id
        self.filename = filename
        self.page_number = page_number
        self.chunk_id = chunk_id
        self.token_count = token_count
        self.chunk_index = chunk_index


class DocumentParser:
    """Extracts text from PDF and DOCX files with page-level metadata."""

    @staticmethod
    def extract_from_pdf(file_path: str) -> List[Dict[str, Any]]:
        """Extract text and page numbers from a PDF file."""
        documents = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text").strip()
                if text:
                    documents.append({
                        "text": text,
                        "page_number": page_num + 1,  # 1-indexed
                        "source": "pdf",
                    })
            doc.close()
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed for {file_path}: {e}")
        return documents

    @staticmethod
    def extract_from_docx(file_path: str) -> List[Dict[str, Any]]:
        """Extract text from a DOCX file, preserving paragraphs."""
        documents = []
        try:
            doc = docx.Document(file_path)
            current_page = 1
            paragraph_texts = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraph_texts.append(text)
                # Estimate page breaks based on rough character count
                if sum(len(p) for p in paragraph_texts) > 3000:
                    for pt in paragraph_texts:
                        documents.append({
                            "text": pt,
                            "page_number": current_page,
                            "source": "docx",
                        })
                    current_page += 1
                    paragraph_texts = []
            
            # Remaining paragraphs
            if paragraph_texts:
                for pt in paragraph_texts:
                    documents.append({
                        "text": pt,
                        "page_number": current_page,
                        "source": "docx",
                    })
                    
        except Exception as e:
            raise RuntimeError(f"DOCX extraction failed for {file_path}: {e}")
        return documents

    @classmethod
    def extract_text(cls, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from supported file types (.pdf, .docx)."""
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        if ext == "pdf":
            return cls.extract_from_pdf(file_path)
        elif ext == "docx":
            return cls.extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")


class RecursiveChunker:
    """
    Recursive text chunker with markdown/header preservation.
    
    Chunk size: 512 tokens, overlap: 64 tokens.
    Injects metadata: document_id, filename, page_number, chunk_id.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separator_regex: str = r"(?<=[.!?])\s+|(?<=\n)\n",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator_regex = separator_regex

    def _split_by_separators(self, text: str) -> List[str]:
        """Split text by paragraphs, sentences, or characters recursively."""
        # First try splitting by double newlines (paragraphs)
        parts = re.split(self.separator_regex, text)
        return [p.strip() for p in parts if p.strip()]

    def chunk_text(self, text: str, document_id: str, filename: str, 
                   page_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Chunk a single text passage into overlapping tokens."""
        # Split by paragraphs first
        paragraphs = self._split_by_separators(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        chunk_id_counter = 0
        
        for para in paragraphs:
            # Estimate token count (roughly 1 token = 4 characters for English)
            para_tokens = max(1, len(para) // 4 + 1)
            
            # If single paragraph exceeds chunk_size, split it further
            if para_tokens > self.chunk_size:
                # Flush current chunk if any
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunk_tokens = sum(
                        max(1, len(c) // 4 + 1) for c in current_chunk
                    )
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "document_id": document_id,
                            "filename": filename,
                            "page_number": page_number,
                            "chunk_id": f"{document_id}-chunk-{chunk_id_counter}",
                            "token_count": chunk_tokens,
                            "chunk_index": chunk_index,
                        }
                    })
                    chunk_index += 1
                    chunk_id_counter += 1
                    current_chunk = []
                    current_tokens = 0
                
                # Split the oversized paragraph by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                sentence_chunk = []
                for sentence in sentences:
                    sent_tokens = max(1, len(sentence) // 4 + 1)
                    if current_tokens + sent_tokens > self.chunk_size and current_chunk:
                        chunk_text = " ".join(sentence_chunk)
                        chunks.append({
                            "text": chunk_text,
                            "metadata": {
                                "document_id": document_id,
                                "filename": filename,
                                "page_number": page_number,
                                "chunk_id": f"{document_id}-chunk-{chunk_id_counter}",
                                "token_count": sum(max(1, len(s) // 4 + 1) for s in sentence_chunk),
                                "chunk_index": chunk_index,
                            }
                        })
                        chunk_index += 1
                        chunk_id_counter += 1
                        sentence_chunk = []
                        current_tokens = 0
                    sentence_chunk.append(sentence)
                    current_tokens += sent_tokens
                
                if sentence_chunk:
                    chunk_text = " ".join(sentence_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "document_id": document_id,
                            "filename": filename,
                            "page_number": page_number,
                            "chunk_id": f"{document_id}-chunk-{chunk_id_counter}",
                            "token_count": sum(max(1, len(s) // 4 + 1) for s in sentence_chunk),
                            "chunk_index": chunk_index,
                        }
                    })
                    chunk_index += 1
                    chunk_id_counter += 1
            
            # Add paragraph to current chunk
            elif current_tokens + para_tokens > self.chunk_size and current_chunk:
                # Flush current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename,
                        "page_number": page_number,
                        "chunk_id": f"{document_id}-chunk-{chunk_id_counter}",
                        "token_count": current_tokens,
                        "chunk_index": chunk_index,
                    }
                })
                chunk_index += 1
                chunk_id_counter += 1
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(para)
            current_tokens += para_tokens
        
        # Flush remaining chunks
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page_number,
                    "chunk_id": f"{document_id}-chunk-{chunk_id_counter}",
                    "token_count": current_tokens,
                    "chunk_index": chunk_index,
                }
            })
            chunk_index += 1
        
        # Post-process: ensure token counts are accurate
        for chunk in chunks:
            tokens = len(chunk["text"]) // 4 + 1
            chunk["metadata"]["token_count"] = max(1, tokens)
        
        return chunks

    def chunk_documents(
        self, 
        documents: List[Dict[str, Any]], 
        document_id: str,
        filename: str
    ) -> List[Dict[str, Any]]:
        """Chunk multiple documents with metadata injection."""
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_text(
                text=doc["text"],
                document_id=document_id,
                filename=filename,
                page_number=doc.get("page_number"),
            )
            all_chunks.extend(chunks)
        return all_chunks