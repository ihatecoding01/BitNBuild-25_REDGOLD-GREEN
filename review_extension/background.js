// Acts as a message broker between popup.js and content_script.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("Background received:", request);
    if (request.from === 'popup' && request.action === 'scrapeReviews') {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const activeTab = tabs[0];
            if (activeTab?.id) {
                chrome.tabs.sendMessage(
                    activeTab.id,
                    { action: "scrapeReviews" },
                    (response) => {
                        if (chrome.runtime.lastError) {
                            console.error("Error sending message to content script:", chrome.runtime.lastError.message);
                            sendResponse({
                                reviews: [],
                                error: "Could not communicate with the page. Try reloading the tab."
                            });
                        } else {
                            // Ensure content_script always returns a consistent object
                            sendResponse(response || { reviews: [], error: "No response from content script." });
                        }
                    }
                );
            } else {
                sendResponse({ reviews: [], error: "No active tab found." });
            }
        });

        // Required to keep sendResponse valid asynchronously
        return true;
    }
});
