import uuid
import datetime
from typing import Dict, Any, List

from api.models import ErrorDetail
from adapters.nlp import analyze_reviews
from core.errors import BaseReviewRadarException

job_store: Dict[str, Dict[str, Any]] = {}


def enqueue_job(reviews: List[str]) -> str:
    """Creates a new job and immediately runs NLP analysis on provided reviews."""
    job_id = str(uuid.uuid4())
    job_store[job_id] = {
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at": datetime.datetime.now(datetime.timezone.utc),
    }

    try:
        # Run analysis directly (no scraping)
        analysis_result = analyze_reviews(reviews)

        job_store[job_id].update({
            "status": "done",
            "result": analysis_result,
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        })

    except BaseReviewRadarException as e:
        print(f"Job {job_id} failed with a known error: {e}")
        from core.errors import AnalysisError

        error_code = "internal_error"
        if isinstance(e, AnalysisError):
            error_code = "analysis_failed"

        job_store[job_id].update({
            "status": "error",
            "error": ErrorDetail(code=error_code, message=str(e)),
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        })

    except Exception as e:
        print(f"Job {job_id} failed with an unexpected error: {e}")
        job_store[job_id].update({
            "status": "error",
            "error": ErrorDetail(
                code="internal_server_error",
                message="An unexpected error occurred."
            ),
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        })

    return job_id


def get_job_or_fail(job_id: str) -> Dict[str, Any]:
    """Retrieves a job from the store or raises a JobNotFound error."""
    if job_id not in job_store:
        from core.errors import JobNotFound
        raise JobNotFound(f"Job with ID '{job_id}' not found.")
    return job_store[job_id]
