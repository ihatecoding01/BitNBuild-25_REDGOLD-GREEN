// content_script.js
console.log("Revuze content script injected.");

// --- Review selectors ---
const AMAZON_REVIEW_TEXT_SELECTORS = [
    'span[data-hook="review-body"]',
    'div.review-text-content span',
    'div[data-hook="review-collapsed"]',
    '.review-text-content span',
    '.cr-original-review-text',
    '[data-hook="review-body"] > span'
];

const AMAZON_LOAD_MORE_SELECTORS = [
    '[data-hook="see-all-reviews-link-foot"]',
    'a[data-hook="see-all-reviews-link"]',
    '[data-hook="reviews-medley-footer"] a',
    '.a-pagination .a-last a',
    'a[aria-label="Next page"]'
];

const FLIPKART_REVIEW_TEXT_SELECTORS = [
    'div.t-ZTKy div div',
    'div.t-ZTKy',
    'div._6K-7Co'
];

// --- Auto-expand reviews and load more ---
function expandAndLoadMoreReviews(maxAttempts = 2) {
    return new Promise(async (resolve) => {
        let attempts = 0;
        let totalReviews = scrapeReviewsFromPage(); // Start with current reviews
        const initialCount = totalReviews.length;
        
        console.log(`Starting expansion with ${initialCount} reviews`);

        while (attempts < maxAttempts) {
            attempts++;
            console.log(`Expansion attempt ${attempts}/${maxAttempts}`);

            // First, try to expand "Read more" links within individual reviews
            const readMoreButtons = document.querySelectorAll('[data-hook="expand-collapse-content"]');
            let expandedAny = false;
            readMoreButtons.forEach(button => {
                if (button.innerText.includes('Read more')) {
                    button.click();
                    expandedAny = true;
                }
            });

            if (expandedAny) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            // Try to load more reviews
            let loadMoreFound = false;
            for (const selector of AMAZON_LOAD_MORE_SELECTORS) {
                const loadMoreBtn = document.querySelector(selector);
                if (loadMoreBtn && loadMoreBtn.offsetParent !== null && !loadMoreBtn.classList.contains('clicked')) {
                    console.log(`Clicking load more button: ${selector}`);
                    loadMoreBtn.classList.add('clicked'); // Prevent multiple clicks
                    loadMoreBtn.click();
                    loadMoreFound = true;
                    break;
                }
            }

            if (!loadMoreFound) {
                console.log('No more load buttons found');
                break;
            }

            // Wait for new content to load
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Check if we got new reviews
            const currentReviews = scrapeReviewsFromPage();
            if (currentReviews.length > totalReviews.length) {
                totalReviews = currentReviews;
                console.log(`Now have ${totalReviews.length} reviews (+${totalReviews.length - initialCount})`);
            } else {
                console.log('No new reviews found in this attempt');
                break;
            }
        }

        console.log(`Expansion complete: ${initialCount} → ${totalReviews.length} reviews`);
        resolve(totalReviews);
    });
}

// --- Enhanced review scraping with deduplication ---
function scrapeReviewsFromPage() {
    const hostname = window.location.hostname;
    const reviewSelectors = hostname.includes("amazon")
        ? AMAZON_REVIEW_TEXT_SELECTORS
        : hostname.includes("flipkart")
            ? FLIPKART_REVIEW_TEXT_SELECTORS
            : [];

    const reviews = [];
    const seenTexts = new Set();

    for (const selector of reviewSelectors) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            let text = el.innerText?.trim();
            if (!text) return;

            // Clean up the text
            text = text.replace(/\s+/g, ' ').trim();

            // Skip if too short or already seen
            if (text.length < 20 || seenTexts.has(text)) return;

            // Skip if it's just metadata or not a review
            if (text.match(/^(Verified Purchase|Top Contributor|Vine Customer|Color:|Size:|Style:)/)) return;

            seenTexts.add(text);
            reviews.push(text);
        });
    }

    console.log(`Scraped ${reviews.length} unique reviews`);
    return reviews;
}

// --- Enhanced wait for reviews with auto-expansion ---
function waitForReviews(timeout = 20000) {
    return new Promise(async (resolve) => {
        console.log('Starting enhanced review collection...');

        // First, get initial reviews
        let allReviews = scrapeReviewsFromPage();
        console.log(`Initial scrape found ${allReviews.length} reviews`);

        // If we have some reviews, try to expand and get more
        if (allReviews.length > 0) {
            try {
                const expandedReviews = await expandAndLoadMoreReviews();
                if (expandedReviews.length > allReviews.length) {
                    console.log(`Expansion increased reviews from ${allReviews.length} to ${expandedReviews.length}`);
                    allReviews = expandedReviews;
                }
            } catch (error) {
                console.log('Expansion failed, using initial reviews:', error);
            }
            
            return resolve(allReviews);
        }

        // If no initial reviews found, wait and observe for dynamic loading
        console.log('No initial reviews found, waiting for dynamic content...');
        const observer = new MutationObserver(() => {
            const newReviews = scrapeReviewsFromPage();
            if (newReviews.length > allReviews.length) {
                allReviews = newReviews;
                console.log(`Found ${newReviews.length} reviews via observer`);
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });

        setTimeout(() => {
            observer.disconnect();
            console.log(`Final review count: ${allReviews.length}`);
            resolve(allReviews);
        }, timeout);
    });
}

// --- Message listener ---
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "scrapeReviews") {
        waitForReviews().then(reviews => {
            console.log("Content script scraped reviews:", reviews.length);
            sendResponse({ reviews });
        }).catch(err => {
            console.error("Scraping failed:", err);
            sendResponse({ reviews: [], error: err.message });
        });
        return true; // keep async response alive
    }
});
