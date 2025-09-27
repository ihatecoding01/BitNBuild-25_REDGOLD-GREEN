from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional, Literal, Union
from datetime import datetime
import uuid

# --- Request Models ---

class AnalyzeRequest(BaseModel):
    """Request body for the /analyze endpoint."""
    url: HttpUrl = Field(..., example="https://www.example-ecommerce.com/product/123")
    max_reviews: Optional[int] = Field(
        default=None, 
        gt=0, 
        description="Max reviews to scrape. Overrides server default if provided."
    )

# --- Response Models & Schemas ---

class AnalyzeJobSubmissionResponse(BaseModel):
    """Immediate response after submitting a URL for analysis."""
    job_id: str = Field(..., example=str(uuid.uuid4()))

class ErrorDetail(BaseModel):
    """Structured error information."""
    code: str = Field(..., example="scrape_failed")
    message: str = Field(..., example="The scraper could not extract reviews from the provided URL.")

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
