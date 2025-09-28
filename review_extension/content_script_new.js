// content_script.js
console.log("Revuze content script injected.");

// --- Review selectors ---
const AMAZON_REVIEW_TEXT_SELECTORS = [
    'span[data-hook="review-body"] span:not([class])',
    'div[data-hook="review-body"] span:not([class])',
    '.cr-original-review-text',
    '[data-hook="review-body"] > span'
];

const FLIPKART_REVIEW_TEXT_SELECTORS = [
    'div.t-ZTKy div div',
    'div.t-ZTKy',
    'div._6K-7Co'
];

// --- Enhanced review scraping ---
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

            // Skip metadata/non-review content
            if (text.match(/^(Verified Purchase|Top Contributor|Vine Customer|Color:|Size:|Style:|Read more|Helpful|Report|By |On |Reviewed)/i)) return;

            seenTexts.add(text);
            reviews.push(text);
        });
    }

    console.log(`Found ${reviews.length} unique reviews on current page`);
    return reviews;
}

// --- Safe expansion without navigation ---
function safeExpandReviews() {
    return new Promise(async (resolve) => {
        console.log('Expanding truncated reviews...');
        let expandedAny = false;

        // Only expand "Read more" links within existing reviews
        const readMoreButtons = document.querySelectorAll('[data-hook="expand-collapse-content"]');
        readMoreButtons.forEach(button => {
            if (button.innerText.includes('Read more') && !button.classList.contains('revuze-expanded')) {
                button.classList.add('revuze-expanded');
                button.click();
                expandedAny = true;
            }
        });

        if (expandedAny) {
            console.log('Expanded some reviews, waiting for content...');
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        resolve(scrapeReviewsFromPage());
    });
}

// --- Main review collection function ---
function collectReviews(timeout = 10000) {
    return new Promise(async (resolve) => {
        console.log('Starting review collection...');

        try {
            // Step 1: Get initial reviews
            let reviews = scrapeReviewsFromPage();
            console.log(`Initial collection: ${reviews.length} reviews`);

            // Step 2: Try to expand truncated reviews (safe, no navigation)
            if (reviews.length > 0) {
                const expandedReviews = await safeExpandReviews();
                if (expandedReviews.length > reviews.length) {
                    reviews = expandedReviews;
                    console.log(`After expansion: ${reviews.length} reviews`);
                }
            }

            // Step 3: If still no reviews, wait a bit and try again (for dynamic content)
            if (reviews.length === 0) {
                console.log('No reviews found initially, waiting for dynamic content...');
                await new Promise(resolve => setTimeout(resolve, 2000));
                reviews = scrapeReviewsFromPage();
            }

            console.log(`Final collection: ${reviews.length} reviews`);
            resolve(reviews);

        } catch (error) {
            console.error('Error collecting reviews:', error);
            resolve([]); // Return empty array on error
        }
    });
}

// --- Message listener ---
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "scrapeReviews") {
        collectReviews().then(reviews => {
            console.log("Content script scraped reviews:", reviews.length);
            sendResponse({ reviews });
        }).catch(err => {
            console.error("Scraping failed:", err);
            sendResponse({ reviews: [], error: err.message });
        });
        return true; // keep async response alive
    }
});