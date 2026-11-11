"""
RAG Compliance Intelligence - Pydantic Schemas
Defines all data models for compliance audit, evidence, and audit reports.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ComplianceStatus(str, Enum):
    """Enumeration of compliance status values."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class EvidenceSnippet(BaseModel):
    """A snippet of evidence extracted from a source document."""
    document_name: str = Field(..., description="Name of the source document")
    page_number: Optional[int] = Field(default=None, description="Page number within the document")
    clause_text: str = Field(..., description="The actual clause or text passage")
    relevance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Relevance score 0.0-1.0"
    )

    @validator("relevance_score")
    def score_must_be_between_0_and_1(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("relevance_score must be between 0.0 and 1.0")
        return v


class AuditFinding(BaseModel):
    """A single audit finding/result for a compliance control."""
    control_id: str = Field(..., description="Unique control identifier (e.g., AC-1, SC-13)")
    control_name: str = Field(..., description="Human-readable control name")
    status: ComplianceStatus = Field(..., description="Compliance status")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )
    justification: str = Field(..., description="LLM justification for the status")
    citations: List[EvidenceSnippet] = Field(
        default_factory=list, description="Supporting evidence snippets"
    )

    @validator("confidence_score")
    def score_must_be_between_0_and_1(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return v


class AuditReportResponse(BaseModel):
    """Complete audit report response structure."""
    overall_score: float = Field(
        ge=0.0, le=1.0, description="Overall compliance score 0.0-1.0"
    )
    total_controls: int = Field(..., description="Total number of controls audited")
    compliant_count: int = Field(
        default=0, description="Number of COMPLIANT controls"
    )
    non_compliant_count: int = Field(
        default=0, description="Number of NON_COMPLIANT controls"
    )
    review_count: int = Field(
        default=0, description="Number of REQUIRES_REVIEW controls"
    )
    findings: List[AuditFinding] = Field(
        default_factory=list, description="List of audit findings"
    )

    @property
    def success_rate(self) -> float:
        """Calculate compliance success rate as percentage."""
        if self.total_controls == 0:
            return 0.0
        return round((self.compliant_count / self.total_controls) * 100, 2)

    @property
    def failure_rate(self) -> float:
        """Calculate non-compliance rate as percentage."""
        if self.total_controls == 0:
            return 0.0
        return round((self.non_compliant_count / self.total_controls) * 100, 2)


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload endpoint."""
    filenames: Optional[List[str]] = Field(
        default=None, description="Optional list of filenames to process"
    )


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy", description="System status")
    vector_count: int = Field(default=0, description="Number of indexed vectors")
    model_loaded: bool = Field(default=False, description="Embedding model loaded")
    qdrant_connected: bool = Field(default=False, description="Qdrant connectivity")
    uptime: Optional[float] = Field(default=None, description="Service uptime in seconds")