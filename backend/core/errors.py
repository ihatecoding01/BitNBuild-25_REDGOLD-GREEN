from fastapi import Request, status
from fastapi.responses import JSONResponse

class BaseReviewRadarException(Exception):
    """Base exception for the application."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class JobNotFound(BaseReviewRadarException):
    """Raised when a job_id is not found in the store."""
    pass


class ScrapingError(BaseReviewRadarException):
    """Raised for general scraping failures."""
    def __init__(self, message: str = "Failed to scrape reviews from the target URL."):
        super().__init__(message)

class ScrapeDisallowed(BaseReviewRadarException):
    """Raised when scraping is blocked (e.g., by robots.txt)."""
    def __init__(self, message: str = "Scraping is disallowed for this URL."):
        super().__init__(message)
        
class NoReviewsFoundError(BaseReviewRadarException):
    """Raised when the scraper runs successfully but finds no reviews."""
    def __init__(self, message: str = "No reviews were found on the page."):
        super().__init__(message)

class AnalysisError(BaseReviewRadarException):
    """Raised for failures during the NLP analysis phase."""
    def __init__(self, message: str = "An internal error occurred during review analysis."):
        super().__init__(message)


async def job_not_found_handler(request: Request, exc: JobNotFound):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": {"code": "not_found", "message": exc.message}},
    )
