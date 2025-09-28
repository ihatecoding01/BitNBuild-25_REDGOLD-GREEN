// Simplified Revuze Extension - Working Version
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔧 DEBUG: Revuze popup loaded');

    // Get DOM elements
    const analyzeButton = document.getElementById('analyze-button');
    const retryButton = document.getElementById('retry-button');
    const mainContent = document.getElementById('main-content');
    const errorMessageEl = document.getElementById('error-message');

    console.log('🔧 DEBUG: Elements found:', {
        analyzeButton: !!analyzeButton,
        mainContent: !!mainContent
    });

    const API_BASE_URL = 'http://localhost:8000/api/v1';
    let currentAnalysisData = null;
    let currentJobId = null;

    // UI Management
    function updateUI(state, data = null) {
        console.log('🔧 DEBUG: updateUI called with state:', state);

        if (!mainContent) return;

        // Hide all views
        mainContent.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });

        // Show the requested view
        const activeView = document.getElementById(`${state}-view`);
        if (activeView) {
            activeView.classList.add('active');
        }

        // Handle specific states
        if (state === 'error' && data) {
            if (errorMessageEl) {
                errorMessageEl.textContent = data.message || 'An error occurred.';
            }
        } else if (state === 'results' && data) {
            currentAnalysisData = data;
            renderResults(data);
            showDetailedAnalysisButton();
        }
    }

    // Simple results rendering
    function renderResults(data) {
        console.log('🔧 DEBUG: Rendering results:', data);

        // Update review count
        const nReviewsEl = document.getElementById('n-reviews');
        if (nReviewsEl) {
            nReviewsEl.textContent = data.n_reviews || 0;
        }

        // Simple sentiment display
        if (data.sentiment) {
            const positive = Math.round((data.sentiment.positive || 0) * 100);
            const negative = Math.round((data.sentiment.negative || 0) * 100);
            const neutral = Math.round((data.sentiment.neutral || 0) * 100);

            console.log('🔧 DEBUG: Sentiment:', { positive, negative, neutral });
        }
    }

    // Show detailed analysis button
    function showDetailedAnalysisButton() {
        const resultsView = document.getElementById('results-view');
        if (!resultsView) return;

        // Remove existing detailed button
        const existingBtn = document.getElementById('detailed-analysis-btn');
        if (existingBtn) existingBtn.remove();

        // Create new detailed analysis button
        const detailedBtn = document.createElement('button');
        detailedBtn.id = 'detailed-analysis-btn';
        detailedBtn.className = 'button detailed-btn';
        detailedBtn.textContent = '📊 View Detailed Analysis';

        detailedBtn.addEventListener('click', openDetailedAnalysis);
        resultsView.appendChild(detailedBtn);
    }

    // Open detailed analysis
    function openDetailedAnalysis() {
        if (!currentAnalysisData) return;

        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const currentTab = tabs[0];
            const pageInfo = {
                url: currentTab.url,
                title: currentTab.title,
                timestamp: new Date().toISOString()
            };

            const frontendData = {
                ...currentAnalysisData,
                source: 'extension',
                page_info: pageInfo,
                job_id: currentJobId
            };

            // Store data for viewer
            const analysisId = `analysis_${Date.now()}`;
            localStorage.setItem(`revuze_${analysisId}`, JSON.stringify(frontendData));

            // Open analysis viewer
            const viewerURL = chrome.runtime.getURL(`analysis-viewer.html?analysis=${analysisId}`);
            chrome.tabs.create({ url: viewerURL });
        });
    }

    // Poll for results
    async function pollForResults(jobId, maxAttempts = 30) {
        console.log('🔧 DEBUG: Polling for results, jobId:', jobId);

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                const response = await fetch(`${API_BASE_URL}/results/${jobId}`);

                if (response.ok) {
                    const data = await response.json();
                    console.log('🔧 DEBUG: Results received:', data);
                    return data;
                } else if (response.status === 202) {
                    console.log(`🔧 DEBUG: Still processing... attempt ${attempt}`);
                    await new Promise(resolve => setTimeout(resolve, 2000));
                } else {
                    throw new Error(`Results polling failed: ${response.status}`);
                }
            } catch (error) {
                console.error(`🔧 DEBUG: Polling attempt ${attempt} failed:`, error);
                if (attempt === maxAttempts) throw error;
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        throw new Error('Analysis timed out');
    }

    // Main analysis function
    async function analyzeReviews(reviews) {
        console.log('🔧 DEBUG: analyzeReviews called with', reviews.length, 'reviews');

        try {
            // Submit to backend
            console.log('🔧 DEBUG: Submitting to backend:', API_BASE_URL);
            const submitResponse = await fetch(`${API_BASE_URL}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reviews })
            });

            console.log('🔧 DEBUG: Submit response status:', submitResponse.status);

            if (!submitResponse.ok) {
                throw new Error(`Analysis submission failed: ${submitResponse.status}`);
            }

            const submitData = await submitResponse.json();
            currentJobId = submitData.job_id;
            console.log('🔧 DEBUG: Job ID:', currentJobId);

            // Poll for results
            const result = await pollForResults(currentJobId);
            updateUI('results', result);

        } catch (error) {
            console.error('🚨 DEBUG: Analysis failed:', error);
            updateUI('error', { message: error.message });
        }
    }

    // Start analysis - main function
    function startAnalysis() {
        console.log('🚀 DEBUG: startAnalysis called');
        updateUI('loading');

        chrome.runtime.sendMessage({ from: 'popup', action: 'scrapeReviews' }, (response) => {
            console.log('🔧 DEBUG: Scraping response:', response);

            if (chrome.runtime.lastError) {
                console.error('🚨 DEBUG: Chrome runtime error:', chrome.runtime.lastError.message);
                updateUI('error', { message: 'Could not scrape reviews. Reload page and try again.' });
                return;
            }

            const reviews = response?.reviews || [];
            console.log('🔧 DEBUG: Reviews found:', reviews.length);

            if (reviews.length === 0) {
                updateUI('error', { message: 'No reviews found on this page. Make sure you are on a product page with reviews.' });
                return;
            }

            // Start analysis
            analyzeReviews(reviews);
        });
    }

    // Event listeners
    if (analyzeButton) {
        console.log('🔧 DEBUG: Adding click listener to analyze button');
        analyzeButton.addEventListener('click', startAnalysis);
    } else {
        console.error('🚨 DEBUG: Analyze button not found!');
    }

    if (retryButton) {
        retryButton.addEventListener('click', () => updateUI('idle'));
    }

    // Initialize
    updateUI('idle');
    console.log('🔧 DEBUG: Extension initialized');
});