import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from urllib.parse import urlparse
from pathlib import Path
import random
import re
import sys

# Allow imports from the parent directory
sys.path.append('.')
from core.errors import ScrapingError, NoReviewsFoundError

# --- Constants for Selectors ---
# Amazon
AMAZON_REVIEW_SELECTORS = [
    '[data-hook="review"]',
    'div.a-section.review.aok-relative',
    'div[id^="customer_review-"]'
]
AMAZON_REVIEW_TEXT_SELECTORS = [
    '[data-hook="review-body"] span',
    '[data-hook="review-body"]'
]
AMAZON_NEXT_PAGE_SELECTOR = 'li.a-last a'
AMAZON_REVIEWS_CONTAINER_SELECTOR = '#customerReviews'

# Flipkart - NEW
FLIPKART_ALL_REVIEWS_LINK_SELECTOR = "a[href*='all-reviews']" # Looks for a link containing 'all-reviews'
FLIPKART_REVIEW_SELECTORS = ['div._27M-vq']
FLIPKART_REVIEW_TEXT_SELECTORS = ['div.t-ZTKy div div', 'div.t-ZTKy'] # Primary selector and a fallback
FLIPKART_NEXT_PAGE_SELECTOR = "a._1LKTO3" # Selector for the 'Next' page button

# --- Persistent session directory ---
USER_DATA_DIR = Path(__file__).resolve().parent / "playwright_user_data"

# --- Helper: Extract ASIN ---
def get_amazon_asin(url: str) -> str | None:
    """Extracts the Amazon Standard Identification Number (ASIN) from a URL."""
    match = re.search(r"/(dp|gp/product)/(\w{10})", url)
    if match:
        return match.group(2)
    return None

# --- Main scraper ---
async def scrape_reviews(url: str, max_reviews: int, headless: bool = True) -> list[str]:
    """
    Scrapes customer reviews from a product page.
    Supports Amazon and Flipkart.
    """
    hostname = urlparse(url).hostname or ""
    all_reviews: list[str] = []

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=headless,
            args=['--no-sandbox'],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("SCRAPER: Applying stealth measures to evade bot detection...")
        await stealth_async(page)

        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font"] else route.continue_())

        try:
            base_url = f"{urlparse(url).scheme}://{hostname}"
            print(f"SCRAPER: First, visiting base URL: {base_url} to warm up session...")
            await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(random.uniform(2000, 4000))

            if "amazon" in hostname:
                asin = get_amazon_asin(url)
                if not asin:
                    raise ScrapingError("Could not extract product ASIN from Amazon URL.")
                
                reviews_url = f"{base_url}/product-reviews/{asin}"
                
                print(f"SCRAPER: Navigating directly to Amazon reviews page: {reviews_url}")
                await page.goto(reviews_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector(AMAZON_REVIEWS_CONTAINER_SELECTOR, timeout=30000)
                print("SCRAPER: Amazon reviews page loaded successfully.")
                
                # ... Amazon scraping loop ...
                page_num = 1
                while len(all_reviews) < max_reviews:
                    await page.locator(AMAZON_REVIEW_SELECTORS[0]).first.wait_for(timeout=30000)
                    review_elements = await page.locator(AMAZON_REVIEW_SELECTORS[0]).all()
                    
                    if not review_elements: break
                    
                    for review_el in review_elements:
                        if len(all_reviews) >= max_reviews: break
                        text = None
                        for text_selector in AMAZON_REVIEW_TEXT_SELECTORS:
                            try:
                                text = await review_el.locator(text_selector).first.text_content(timeout=2000)
                                if text:
                                    all_reviews.append(text.strip())
                                    break
                            except Exception: continue
                    
                    if len(all_reviews) >= max_reviews: break
                    
                    next_page_button = page.locator(AMAZON_NEXT_PAGE_SELECTOR).first
                    if await next_page_button.is_disabled(timeout=5000): break
                    
                    if await next_page_button.is_visible():
                        current_url = page.url
                        await next_page_button.click()
                        await page.wait_for_url(lambda url: url != current_url, timeout=30000)
                        page_num += 1
                    else: break

            elif "flipkart" in hostname:
                print(f"SCRAPER: Navigating to Flipkart product page: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # --- NEW: Human-like browsing simulation ---
                print("SCRAPER: Simulating human browsing to avoid detection...")
                for _ in range(random.randint(2, 4)):
                    scroll_y = random.randint(300, 700)
                    await page.evaluate(f"window.scrollBy(0, {scroll_y})")
                    await page.wait_for_timeout(random.uniform(500, 1500))
                await page.mouse.move(random.randint(100, 800), random.randint(200, 600))
                await page.wait_for_timeout(random.uniform(1000, 2000))
                
                print("SCRAPER: Looking for 'All reviews' link on Flipkart page...")
                all_reviews_link = page.locator(FLIPKART_ALL_REVIEWS_LINK_SELECTOR).first
                if await all_reviews_link.is_visible(timeout=20000):
                    await all_reviews_link.click()
                    await page.wait_for_load_state("domcontentloaded", timeout=30000)
                    print("SCRAPER: Navigated to dedicated reviews page.")
                else:
                    raise ScrapingError("Could not find 'All reviews' link after browsing.")

                # --- Flipkart Scraping Loop ---
                page_num = 1
                while len(all_reviews) < max_reviews:
                    print(f"SCRAPER: Scraping page {page_num}...")
                    await page.locator(FLIPKART_REVIEW_SELECTORS[0]).first.wait_for(timeout=30000)
                    review_elements = await page.locator(FLIPKART_REVIEW_SELECTORS[0]).all()

                    if not review_elements: break

                    for review_el in review_elements:
                        if len(all_reviews) >= max_reviews: break
                        text = None
                        for text_selector in FLIPKART_REVIEW_TEXT_SELECTORS:
                            try:
                                text = await review_el.locator(text_selector).first.text_content(timeout=2000)
                                if text:
                                    all_reviews.append(text.strip())
                                    break
                            except Exception: continue
                    
                    if len(all_reviews) >= max_reviews: break

                    next_page_button = page.locator(f"{FLIPKART_NEXT_PAGE_SELECTOR} >> text=Next").first
                    if not await next_page_button.is_visible(timeout=5000):
                        print("SCRAPER: No 'Next' button found. Reached last page.")
                        break
                    
                    await next_page_button.click()
                    await page.wait_for_load_state("domcontentloaded", timeout=30000)
                    page_num += 1

            else:
                 raise ScrapingError(f"Unsupported domain: {hostname}. Now supports Amazon & Flipkart.")

        finally:
            await context.close()
        
        if not all_reviews:
            raise NoReviewsFoundError("Scraper ran but could not find any review texts.")
        
        print(f"SCRAPER: Finished. Successfully scraped {len(all_reviews)} reviews.")
        return all_reviews

# --- Debug runner ---
if __name__ == "__main__":
    # --- CHOOSE A URL TO TEST ---
    # Amazon
    # test_url = "https://www.amazon.in/Cetaphil-Sulphate-Free-Hydrating-Niacinamide-Sensitive/dp/B01CCGW4OE/"
    # Flipkart
    test_url = "https://www.flipkart.com/motorola-g34-5g-ocean-green-128-gb/p/itm6b1a33b9d91a1"
    
    # To see the browser, change headless=True to headless=False
    reviews = asyncio.run(scrape_reviews(test_url, max_reviews=25, headless=False))
    print(f"\nFINAL RESULT: Scraped {len(reviews)} reviews.")

