import asyncio
import random
from typing import List
from urllib.parse import urlparse
from core.errors import ScrapingError, ScrapeDisallowed, NoReviewsFoundError

async def scrape_reviews(url: str, max_reviews: int) -> List[str]:
    """
    Mock scraper function.
    - Simulates network delay.
    - Returns synthetic review data.
    - Simulates common failure modes based on URL.
    """
    print(f"MOCK SCRAPER: Starting scrape for '{url}' (max: {max_reviews} reviews)...")
    await asyncio.sleep(random.uniform(2, 5))  # Simulate network latency

    hostname = urlparse(url).hostname

    if "fail-scrape.com" in hostname:
        raise ScrapingError("Mock error: Site structure changed, scraper failed.")
    if "robots-blocked.com" in hostname:
        raise ScrapeDisallowed("Mock error: Blocked by robots.txt.")
    if "no-reviews.com" in hostname:
        raise NoReviewsFoundError("Mock error: Scraper ran but found no review elements.")
    if "ecommerce.com" not in hostname:
        # A simple validation check example
        raise ScrapingError("Mock error: This scraper only works on 'ecommerce.com' domains.")

    # Generate synthetic positive and negative reviews
    positive_reviews = [
        "Absolutely love this product! The battery life is incredible.",
        "Best purchase of the year. The screen is gorgeous and so responsive.",
        "Exceeded my expectations. Build quality is top-notch.",
        "Five stars! The setup was a breeze and it works perfectly.",
        "Highly recommended. The performance is outstanding for the price.",
    ]
    negative_reviews = [
        "Very disappointed. The battery dies way too quickly.",
        "The screen arrived with a dead pixel. Customer service was unhelpful.",
        "Broke after just one week of use. Poor build quality.",
        "The software is buggy and crashes frequently. A total waste of money.",
        "Terrible customer service experience when I tried to return it.",
    ]

    # Mix reviews to create a larger list
    all_reviews = []
    for i in range(max_reviews):
        if random.random() < 0.8: # 80% positive sentiment
            all_reviews.append(random.choice(positive_reviews) + f" (Review #{i+1})")
        else:
            all_reviews.append(random.choice(negative_reviews) + f" (Review #{i+1})")
    
    print(f"MOCK SCRAPER: Successfully scraped {len(all_reviews)} reviews.")
    return all_reviews[:max_reviews]
