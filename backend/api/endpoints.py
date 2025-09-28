from fastapi import APIRouter, Depends, Header, HTTPException, status
from typing import Optional

from .models import (
    AnalyzeRequest, AnalyzeJobSubmissionResponse, JobResultResponse,
    DoneJobResponse, PendingJobResponse, ErrorJobResponse, StatusOnlyResponse
)
from jobs import manager
from core.config import settings

router = APIRouter()


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Dependency to verify API key if it's enabled in settings."""
    if settings.ENABLE_API_KEY:
        if not x_api_key or x_api_key != settings.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key"
            )
    return x_api_key


@router.get("/health", tags=["General"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.post(
    "/analyze",
    response_model=AnalyzeJobSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Analysis"],
    dependencies=[Depends(verify_api_key)]
)
async def analyze_reviews(request: AnalyzeRequest):
    """
    Accepts a list of reviews for analysis.
    This endpoint immediately returns a job ID while analysis runs synchronously.
    """
    if not request.reviews or len(request.reviews) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No reviews provided for analysis."
        )

    job_id = manager.enqueue_job(request.reviews)
    return AnalyzeJobSubmissionResponse(job_id=job_id)


@router.get(
    "/results/{job_id}",
    response_model=JobResultResponse,
    tags=["Analysis"],
    responses={
        200: {"model": DoneJobResponse},
        202: {"model": PendingJobResponse},
        404: {"description": "Job not found"},
        500: {"model": ErrorJobResponse, "description": "Job failed with an error"}
    }
)
async def get_results(job_id: str):
    """
    Retrieves the status and results of an analysis job.
    - Returns 202 if the job is pending.
    - Returns 200 with the full analysis if the job is done.
    - Returns 500 if the job failed, with error details.
    """
    job = manager.get_job_or_fail(job_id)

    if job["status"] == "pending":
        return PendingJobResponse(job_id=job_id, status="pending")

    if job["status"] == "error":
        return ErrorJobResponse(job_id=job_id, status="error", error=job["error"])

    result_data = job["result"]
    return DoneJobResponse(
        job_id=job_id,
        status="done",
        sentiment=result_data["sentiment"],
        counts=result_data["counts"],
        top_positive=result_data["top_positive"],
        top_negative=result_data["top_negative"],
        n_reviews=result_data["n_reviews"],
        generated_at=job["updated_at"]
    )


@router.get(
    "/status/{job_id}",
    response_model=StatusOnlyResponse,
    tags=["Analysis"]
)
async def get_status(job_id: str):
    """A lightweight endpoint to only check the status of a job."""
    job = manager.get_job_or_fail(job_id)
    return StatusOnlyResponse(status=job["status"])
