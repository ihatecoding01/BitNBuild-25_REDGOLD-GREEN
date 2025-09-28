from typing import List
from ..core.errors import ScrapingError, NoReviewsFoundError

# Re-export the real async scraper defined at project root (scraper.py)
# to keep adapter import path stable for the job manager.
try:
    from scraper import scrape_reviews  # type: ignore
except Exception as e:  # pragma: no cover
    raise ScrapingError(f"Failed to import real scraper implementation: {e}")

__all__ = ["scrape_reviews"]
