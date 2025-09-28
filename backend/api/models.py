from pydantic import BaseModel, Field
from typing import List, Union, Literal
from datetime import datetime
import uuid

# --- Request Models ---

class AnalyzeRequest(BaseModel):
    """Request body for the /analyze endpoint."""
    reviews: List[str] = Field(
        ..., 
        min_items=1, 
        description="Raw review texts extracted from the product page."
    )

# --- Response Models & Schemas ---

class AnalyzeJobSubmissionResponse(BaseModel):
    """Immediate response after submitting reviews for analysis."""
    job_id: str = Field(..., example=str(uuid.uuid4()))

class ErrorDetail(BaseModel):
    """Structured error information."""
    code: str = Field(..., example="analysis_failed")
    message: str = Field(..., example="The analysis could not process the provided reviews.")

class SentimentBreakdown(BaseModel):
    positive: float = Field(..., ge=0, le=1, example=0.82)
    neutral: float = Field(..., ge=0, le=1, example=0.10)
    negative: float = Field(..., ge=0, le=1, example=0.08)

class ReviewCounts(BaseModel):
    positive: int = Field(..., ge=0, example=1018)
    neutral: int = Field(..., ge=0, example=124)
    negative: int = Field(..., ge=0, example=98)

class TopTerm(BaseModel):
    term: str = Field(..., example="battery life")
    score: float = Field(..., example=0.31)

# --- Job Status Response Models ---

class BaseJobResponse(BaseModel):
    job_id: str

class PendingJobResponse(BaseModel):
    job_id: str
    status: Literal["pending"] = "pending"

class DoneJobResponse(BaseModel):
    job_id: str
    status: Literal["done"] = "done"
    sentiment: SentimentBreakdown
    counts: ReviewCounts
    top_positive: List[TopTerm]
    top_negative: List[TopTerm]
    n_reviews: int = Field(..., example=1240)
    generated_at: datetime

class ErrorJobResponse(BaseModel):
    job_id: str
    status: Literal["error"] = "error"
    error: ErrorDetail

# Union model for OpenAPI documentation to show all possible responses
JobResultResponse = Union[DoneJobResponse, PendingJobResponse, ErrorJobResponse]

class StatusOnlyResponse(BaseModel):
    status: str
