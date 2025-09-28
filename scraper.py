import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse
import sys
from pathlib import Path
from typing import List

# Make sure project root and backend are on path for error imports
project_root = Path(__file__).resolve().parent
backend_path = project_root / "backend"
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))
try:
    from backend.core.errors import ScrapingError, NoReviewsFoundError  # preferred
except Exception:
    try:
        from .backend.core.errors import ScrapingError, NoReviewsFoundError  # fallback
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Unable to import error classes: {e}")

# --- Constants for Selectors ---
# AMAZON SELECTORS
AMAZON_REVIEWS_CONTAINER_SELECTOR = '#customerReviews'
AMAZON_REVIEW_SELECTORS = [
    '[data-hook="review"]',
    'div.a-section.review.aok-relative',
    'div[id^="customer_review-"]'
]
AMAZON_REVIEW_TEXT_SELECTOR = '[data-hook="review-body"] span'
AMAZON_NEXT_PAGE_SELECTOR = 'li.a-last a'
AMAZON_ALL_REVIEWS_LINK_SELECTOR = '[data-hook="see-all-reviews-link-foot"]'

# FLIPKART SELECTORS
FLIPKART_REVIEW_SELECTOR = 'div._27M-vq'
FLIPKART_REVIEW_TEXT_SELECTOR = 'div.t-ZTKy div div'
FLIPKART_NEXT_PAGE_SELECTOR = 'a._1LKTO3'
FLIPKART_ALL_REVIEWS_LINK_SELECTOR = 'div._3UAT2v._16PBlm a'

# --- Persistent Session Setup ---
# This directory will store session cookies to keep you logged in
USER_DATA_DIR = Path(__file__).resolve().parent / "playwright_user_data"


async def scrape_reviews(
    url: str,
    max_reviews: int,
    *,
    headless: bool | None = None,
    per_page_delay: float = 0.0,
    distinct: bool = True,
) -> List[str]:
    """Scrape reviews from an Amazon or Flipkart product page.

    Parameters
    ----------
    url : str
        Product page URL.
    max_reviews : int
        Maximum number of reviews to collect (best effort).
    headless : bool | None
        Override headless mode. Defaults to False for first run so user can login.
    """
    if not isinstance(url, str) or not url.startswith('http'):
        raise ScrapingError("URL must be a valid http(s) string")
    if max_reviews <= 0:
        raise ScrapingError("max_reviews must be > 0")
    if headless is None:
        headless = False
    print(f"SCRAPER: Starting scrape for '{url}' (max: {max_reviews} reviews, headless={headless}, delay={per_page_delay})")

    async def _is_visible(locator, timeout_ms: int) -> bool:
        """Robust visibility check with explicit wait; returns False on timeout."""
        try:
            await locator.wait_for(state='visible', timeout=timeout_ms)
            return True
        except PlaywrightTimeoutError:
            return False
        except Exception:
            return False
    hostname = urlparse(url).hostname

    async with async_playwright() as p:
        # Using a persistent context allows us to save login cookies between runs.
        # For the first run, you will need to log in to Amazon manually.
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=headless,
            args=['--no-sandbox'],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        await page.route("**/*", lambda route:
            route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"]
            else route.continue_()
        )
        
        all_reviews = []
        try:
            try:
                await page.goto(url, timeout=90000, wait_until='domcontentloaded')
            except PlaywrightTimeoutError:
                raise ScrapingError("Initial navigation timeout. Page did not load in 90s.")

            # --- Site-Specific Selector Setup ---
            review_selectors_to_try = []
            review_text_selector = ""
            next_page_selector = ""
            
            if hostname and 'amazon' in hostname:
                review_selectors_to_try = AMAZON_REVIEW_SELECTORS
                review_text_selector = AMAZON_REVIEW_TEXT_SELECTOR
                next_page_selector = AMAZON_NEXT_PAGE_SELECTOR
                all_reviews_link_selector = AMAZON_ALL_REVIEWS_LINK_SELECTOR
                
                print("SCRAPER: On Amazon page, attempting to navigate to reviews section...")
                try:
                    all_reviews_link = page.locator(all_reviews_link_selector).first
                    if await _is_visible(all_reviews_link, 20000):
                        print("SCRAPER: Found 'See all reviews' link. Clicking...")
                        await all_reviews_link.click()
                        try:
                            await page.wait_for_selector(AMAZON_REVIEWS_CONTAINER_SELECTOR, timeout=90000)
                        except PlaywrightTimeoutError:
                            raise ScrapingError("Timed out waiting for Amazon reviews container after clicking 'See all reviews'.")
                        print("SCRAPER: Navigated to dedicated reviews page and found container.")
                    else:
                        print("SCRAPER: 'See all reviews' link not found, checking for container on current page...")
                        try:
                            await page.wait_for_selector(AMAZON_REVIEWS_CONTAINER_SELECTOR, timeout=60000)
                        except PlaywrightTimeoutError:
                            raise ScrapingError("Timed out waiting for Amazon reviews container on product page.")
                    
                    print("SCRAPER: Main reviews container loaded successfully.")
                except Exception as e:
                    print("SCRAPER: FAILED to find main reviews container. Saving screenshot for debugging.")
                    screenshot_path = "debug_container_fail.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"SCRAPER: Screenshot saved to '{screenshot_path}'. Please check this image.")
                    raise e

            elif hostname and 'flipkart' in hostname:
                # ... (Flipkart logic remains the same)
                review_selectors_to_try = [FLIPKART_REVIEW_SELECTOR]
                review_text_selector = FLIPKART_REVIEW_TEXT_SELECTOR
                next_page_selector = FLIPKART_NEXT_PAGE_SELECTOR
                all_reviews_link_selector = FLIPKART_ALL_REVIEWS_LINK_SELECTOR

                print("SCRAPER: On Flipkart page, looking for 'All reviews' link...")
                all_reviews_link = page.locator(all_reviews_link_selector).first
                if await _is_visible(all_reviews_link, 30000):
                    await all_reviews_link.click()
                    try:
                        await page.wait_for_load_state('domcontentloaded', timeout=60000)
                    except PlaywrightTimeoutError:
                        raise ScrapingError("Timed out waiting for Flipkart reviews page load.")
                    print("SCRAPER: Navigated to dedicated reviews page.")
                else:
                    print("SCRAPER: Already on reviews page or link not found, proceeding...")
            else:
                raise ScrapingError(f"Unsupported or unparseable domain: {hostname}.")

            # --- Main Scraping Loop ---
            page_num = 1
            while len(all_reviews) < max_reviews:
                print(f"SCRAPER: Scraping page {page_num}...")
                
                review_elements = []
                for selector in review_selectors_to_try:
                    review_elements = await page.locator(selector).all()
                    if review_elements:
                        print(f"SCRAPER: Found {len(review_elements)} reviews using selector: '{selector}'")
                        break
                
                if not review_elements:
                    print("SCRAPER: No review elements found on this page. Ending scrape.")
                    screenshot_path = "debug_screenshot.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"SCRAPER: A screenshot has been saved to '{screenshot_path}' for debugging.")
                    break
                
                for review_el in review_elements:
                    if len(all_reviews) >= max_reviews:
                        break
                    try:
                        text_content_el = review_el.locator(review_text_selector).first
                        text = await text_content_el.inner_text()
                        if text:
                            cleaned = ' '.join(text.split())
                            all_reviews.append(cleaned)
                    except Exception:
                        pass
                
                print(f"SCRAPER: Collected {len(all_reviews)} reviews so far.")
                
                next_page_button = page.locator(next_page_selector).last
                visible = await _is_visible(next_page_button, 8000)
                if not visible:
                    print("SCRAPER: No 'next page' button found. Reached the last page.")
                    break

                try:
                    await next_page_button.click()
                    await page.wait_for_load_state('domcontentloaded', timeout=60000)
                except PlaywrightTimeoutError:
                    print("SCRAPER: Timeout after clicking next page; stopping.")
                    break
                page_num += 1
                if per_page_delay > 0:
                    await asyncio.sleep(per_page_delay)

        finally:
            # Ensures the browser context is always closed
            await context.close()
        
        if not all_reviews:
            raise NoReviewsFoundError("Scraper ran but found no review texts.")

        if distinct:
            before = len(all_reviews)
            deduped = []
            seen = set()
            for r in all_reviews:
                if r not in seen:
                    seen.add(r)
                    deduped.append(r)
            all_reviews = deduped
            if len(all_reviews) != before:
                print(f"SCRAPER: Deduplicated {before-len(all_reviews)} duplicate reviews.")

        if len(all_reviews) > max_reviews:
            all_reviews = all_reviews[:max_reviews]
        print(f"SCRAPER: Successfully scraped {len(all_reviews)} reviews (returned).")
        return all_reviews


