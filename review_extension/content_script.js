// content_script.js
console.log("🔎 Revuze content script injected.");

// --- Review selectors ---
const AMAZON_REVIEW_TEXT_SELECTORS = [
    'span[data-hook="review-body"]',
    'div.review-text-content span',
    'div[data-hook="review-collapsed"]',
    '.review-text-content span'
];

const FLIPKART_REVIEW_TEXT_SELECTORS = [
    'div.t-ZTKy div div',
    'div.t-ZTKy',
    'div._6K-7Co'
];

// --- Scrape reviews from the DOM ---
function scrapeReviewsFromPage() {
    const hostname = window.location.hostname;
    const reviewSelectors = hostname.includes("amazon")
        ? AMAZON_REVIEW_TEXT_SELECTORS
        : hostname.includes("flipkart")
        ? FLIPKART_REVIEW_TEXT_SELECTORS
        : [];

    const reviews = [];
    for (const selector of reviewSelectors) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            const text = el.innerText?.trim();
            if (text && !reviews.includes(text)) reviews.push(text);
        });
    }
    return reviews;
}

// --- Wait for reviews to appear and load dynamically ---
function waitForReviews(timeout = 15000) {
    return new Promise(resolve => {
        let allReviews = scrapeReviewsFromPage();
        if (allReviews.length > 0) return resolve(allReviews);

        const observer = new MutationObserver(() => {
            const newReviews = scrapeReviewsFromPage();
            if (newReviews.length > allReviews.length) {
                allReviews = newReviews;
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });

        setTimeout(() => {
            observer.disconnect();
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
