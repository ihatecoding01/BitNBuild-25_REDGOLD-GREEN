import uuid
import datetime
from typing import Dict, Any

from api.models import ErrorDetail
from adapters.scraper import scrape_reviews
from adapters.nlp import analyze_reviews
from core.errors import BaseReviewRadarException

# In-memory store for job status and results.
# In a real application, this would be Redis, a database, etc.
job_store: Dict[str, Dict[str, Any]] = {}

def create_job() -> str:
    """Generates a unique job ID and initializes its state in the store."""
    job_id = str(uuid.uuid4())
    job_store[job_id] = {
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at": datetime.datetime.now(datetime.timezone.utc),
    }
    return job_id

def get_job_or_fail(job_id: str) -> Dict[str, Any]:
    """Retrieves a job from the store or raises a JobNotFound error."""
    if job_id not in job_store:
        from core.errors import JobNotFound
        raise JobNotFound(f"Job with ID '{job_id}' not found.")
    return job_store[job_id]

async def run_analysis_pipeline(job_id: str, url: str, max_reviews: int):
    """
    The core background task for a single analysis job.
    It orchestrates the scraping and NLP analysis, handling errors and updating the job store.
    """
    try:
        # 1. Scrape reviews from the URL
        reviews = await scrape_reviews(url, max_reviews)
        
        # 2. Analyze the scraped reviews
        analysis_result = analyze_reviews(reviews)
        
        # 3. Store the successful result
        job_store[job_id].update({
            "status": "done",
            "result": analysis_result,
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        })

    except BaseReviewRadarException as e:
        # Catch known exceptions from our application (scraper, nlp)
        # and map them to structured errors.
        print(f"Job {job_id} failed with a known error: {e}")
        from core.errors import ScrapeDisallowed, ScrapingError, AnalysisError, NoReviewsFoundError
        
        error_code = "internal_error"
        if isinstance(e, ScrapeDisallowed):
            error_code = "scrape_disallowed"
        elif isinstance(e, (ScrapingError, NoReviewsFoundError)):
            error_code = "scrape_failed"
        elif isinstance(e, AnalysisError):
            error_code = "analysis_failed"

        job_store[job_id].update({
            "status": "error",
            "error": ErrorDetail(code=error_code, message=str(e)),
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        })
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Job {job_id} failed with an unexpected error: {e}")
        job_store[job_id].update({
            "status": "error",
            "error": ErrorDetail(code="internal_server_error", message="An unexpected error occurred."),
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        })
