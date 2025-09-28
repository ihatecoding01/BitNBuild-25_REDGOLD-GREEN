document.addEventListener('DOMContentLoaded', () => {
    console.log("🔧 DEBUG: Popup script loaded");
    const analyzeButton = document.getElementById('analyze-button');
    const retryButton = document.getElementById('retry-button');
    const mainContent = document.getElementById('main-content');
    const errorMessageEl = document.getElementById('error-message');
    const nReviewsEl = document.getElementById('n-reviews');

    console.log("🔧 DEBUG: Elements found:", {
        analyzeButton: !!analyzeButton,
        retryButton: !!retryButton,
        mainContent: !!mainContent
    });

    // New unique analytics elements
    const confidenceBarEl = document.getElementById('confidence-bar');
    const confidenceTextEl = document.getElementById('confidence-text');
    const confidenceReasonEl = document.getElementById('confidence-reason');
    const trustPercentageEl = document.getElementById('trust-percentage');
    const lovePointsEl = document.getElementById('love-points');
    const hatePointsEl = document.getElementById('hate-points');
    const categoryBreakdownEl = document.getElementById('category-breakdown');
    const chartCanvas = document.getElementById('sentiment-chart');

    let sentimentChart = null;
    const API_BASE_URL = 'http://localhost:8000/api/v1';

    // --- UI Helpers ---
    const updateUI = (state, data = null) => {
        if (!mainContent) return;

        mainContent.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
        const activeView = document.getElementById(`${state}-view`);
        if (activeView) activeView.classList.add('active');

        if (state === 'results' && data) {
            const nReviews = data.n_reviews || (data.reviews ? data.reviews.length : 0);
            if (nReviewsEl) nReviewsEl.textContent = nReviews;

            renderPurchaseConfidence(data);
            renderAuthenticityScore(data);
            renderLoveHateAnalysis(data);
            renderCategoryBreakdown(data);
            renderReviewVelocityAnalysis(data);
            renderPriceValueInsights(data);
            renderChart(data.sentiment);
        } else if (state === 'error' && data) {
            if (errorMessageEl) errorMessageEl.textContent = data.message || 'An unknown error occurred.';
        }
    };

    const renderOverallSummary = (data) => {
        // Calculate overall rating from sentiment
        const sentimentData = data.sentiment || {};
        const positiveRatio = sentimentData.positive || 0;
        const negativeRatio = sentimentData.negative || 0;
        const neutralRatio = sentimentData.neutral || 0;

        // Convert sentiment to 1-5 star rating
        const overallRating = data.overall_rating_stars || (1 + (positiveRatio * 4) - (negativeRatio * 2));
        const clampedRating = Math.max(1, Math.min(5, overallRating));

        // Render star rating
        if (starRatingEl) {
            const fullStars = Math.floor(clampedRating);
            const hasHalfStar = clampedRating % 1 >= 0.5;
            let starsText = '★'.repeat(fullStars);
            if (hasHalfStar) starsText += '☆';
            starsText += '☆'.repeat(5 - fullStars - (hasHalfStar ? 1 : 0));
            starRatingEl.textContent = starsText;
        }

        if (ratingTextEl) {
            ratingTextEl.textContent = `${clampedRating.toFixed(1)}/5`;
        }

        // Generate summary text
        if (summaryTextEl) {
            const nReviews = data.n_reviews || 0;
            const posPercent = Math.round(positiveRatio * 100);
            const negPercent = Math.round(negativeRatio * 100);

            let summaryText = `Based on ${nReviews} reviews: `;
            if (posPercent >= 60) {
                summaryText += `Mostly positive feedback (${posPercent}% positive)`;
            } else if (negPercent >= 40) {
                summaryText += `Mixed reviews with concerns (${negPercent}% negative)`;
            } else {
                summaryText += `Balanced feedback across sentiments`;
            }

            summaryTextEl.textContent = summaryText;
        }
    };

    // --- UNIQUE ANALYTICS FUNCTIONS ---

    const renderPurchaseConfidence = (data) => {
        const sentimentData = data.sentiment || {};
        const positiveRatio = sentimentData.positive || 0;
        const negativeRatio = sentimentData.negative || 0;
        const nReviews = data.n_reviews || 0;

        // Calculate confidence score (0-100) based on multiple factors
        let confidenceScore = 50; // base score

        // Factor 1: Overall sentiment (40% weight)
        confidenceScore += (positiveRatio - negativeRatio) * 40;

        // Factor 2: Review volume (20% weight)
        const volumeBonus = Math.min(nReviews / 50, 1) * 20;
        confidenceScore += volumeBonus;

        // Factor 3: Category analysis (20% weight)
        if (data.category_breakdown && data.category_breakdown.length > 0) {
            const avgCategoryRating = data.category_breakdown.reduce((sum, cat) => sum + cat.rating, 0) / data.category_breakdown.length;
            confidenceScore += (avgCategoryRating - 3) * 10;
        }

        // Factor 4: Sentiment balance (20% weight) - extreme polarization reduces confidence
        const balance = 1 - Math.abs(positiveRatio - negativeRatio);
        confidenceScore += balance * 10;

        confidenceScore = Math.max(0, Math.min(100, confidenceScore));

        // Update UI
        if (confidenceBarEl) {
            setTimeout(() => {
                confidenceBarEl.style.width = `${confidenceScore}%`;
            }, 300);
        }

        if (confidenceTextEl) {
            let confidenceLabel = '';
            if (confidenceScore >= 80) confidenceLabel = 'High Confidence';
            else if (confidenceScore >= 60) confidenceLabel = 'Good Confidence';
            else if (confidenceScore >= 40) confidenceLabel = 'Moderate Risk';
            else confidenceLabel = 'High Risk';

            confidenceTextEl.textContent = `${Math.round(confidenceScore)}% ${confidenceLabel}`;
        }

        if (confidenceReasonEl) {
            let reason = '';
            if (confidenceScore >= 70) {
                reason = `Strong positive sentiment (${Math.round(positiveRatio * 100)}% positive) with good review volume.`;
            } else if (negativeRatio > 0.4) {
                reason = `Concerns noted: ${Math.round(negativeRatio * 100)}% negative reviews highlight potential issues.`;
            } else {
                reason = `Mixed feedback suggests carefully review specific aspects before purchasing.`;
            }
            confidenceReasonEl.textContent = reason;
        }
    };

    const renderAuthenticityScore = (data) => {
        const nReviews = data.n_reviews || 0;
        const authMetrics = data.authenticity_metrics || {};
        let authenticityScore = 75; // base score

        // Factor 1: Review volume distribution
        if (nReviews < 5) authenticityScore -= 20;
        else if (nReviews > 100) authenticityScore += 10;

        // Factor 2: Sentiment distribution (fake reviews often skew extremely)
        const sentimentData = data.sentiment || {};
        const isExtreme = sentimentData.positive > 0.9 || sentimentData.negative > 0.9;
        if (isExtreme && nReviews > 20) authenticityScore -= 15;

        // Factor 3: Advanced metrics from backend
        if (authMetrics.avg_review_length) {
            // Authentic reviews tend to be reasonably detailed
            if (authMetrics.avg_review_length > 100) authenticityScore += 8;
            else if (authMetrics.avg_review_length < 30) authenticityScore -= 10;
        }

        if (authMetrics.keyword_diversity) {
            // More diverse vocabulary suggests authentic reviews
            if (authMetrics.keyword_diversity >= 20) authenticityScore += 12;
            else if (authMetrics.keyword_diversity < 8) authenticityScore -= 8;
        }

        if (authMetrics.category_coverage) {
            // Authentic reviews cover multiple product aspects
            if (authMetrics.category_coverage >= 4) authenticityScore += 10;
            else if (authMetrics.category_coverage <= 1) authenticityScore -= 12;
        }

        authenticityScore = Math.max(30, Math.min(95, authenticityScore));

        if (trustPercentageEl) {
            trustPercentageEl.textContent = `${Math.round(authenticityScore)}%`;
        }

        // Update trust indicators with real data
        const lengthIndicator = document.getElementById('indicator-length');
        const emotionIndicator = document.getElementById('indicator-emotion');
        const specificIndicator = document.getElementById('indicator-specific');

        if (lengthIndicator) {
            const lengthScore = authMetrics.avg_review_length || 50;
            lengthIndicator.className = 'indicator ' +
                (lengthScore > 80 ? 'high' : lengthScore > 40 ? 'medium' : 'low');
        }

        if (emotionIndicator) {
            const emotionBalance = 1 - (authMetrics.sentiment_variance || 0);
            emotionIndicator.className = 'indicator ' +
                (emotionBalance > 0.7 ? 'high' : emotionBalance > 0.4 ? 'medium' : 'low');
        }

        if (specificIndicator) {
            const specificityScore = authMetrics.category_coverage || 0;
            specificIndicator.className = 'indicator ' +
                (specificityScore >= 4 ? 'high' : specificityScore >= 2 ? 'medium' : 'low');
        }
    };

    const renderLoveHateAnalysis = (data) => {
        const positiveKeywords = data.top_positive || [];
        const negativeKeywords = data.top_negative || [];

        // Generate love points (what users praise most)
        const lovePoints = positiveKeywords.slice(0, 4).map(kw => {
            const benefits = {
                'battery': 'Long-lasting battery life',
                'screen': 'Excellent display quality',
                'camera': 'Great photo quality',
                'performance': 'Smooth and fast operation',
                'quality': 'Well-built and durable',
                'design': 'Attractive appearance',
                'price': 'Good value for money'
            };
            return benefits[kw.term.toLowerCase()] || `Excellent ${kw.term}`;
        });

        // Generate hate points (main complaints)
        const hatePoints = negativeKeywords.slice(0, 4).map(kw => {
            const complaints = {
                'battery': 'Battery drains quickly',
                'screen': 'Display issues reported',
                'camera': 'Poor photo quality',
                'service': 'Customer service problems',
                'quality': 'Build quality concerns',
                'price': 'Overpriced for features',
                'software': 'Software bugs and glitches'
            };
            return complaints[kw.term.toLowerCase()] || `Issues with ${kw.term}`;
        });

        // Update UI
        if (lovePointsEl) {
            lovePointsEl.innerHTML = '';
            (lovePoints.length > 0 ? lovePoints : ['Generally positive feedback']).forEach(point => {
                const li = document.createElement('li');
                li.textContent = point;
                lovePointsEl.appendChild(li);
            });
        }

        if (hatePointsEl) {
            hatePointsEl.innerHTML = '';
            (hatePoints.length > 0 ? hatePoints : ['Minor concerns noted']).forEach(point => {
                const li = document.createElement('li');
                li.textContent = point;
                hatePointsEl.appendChild(li);
            });
        }
    };

    const renderCategoryBreakdown = (data) => {
        if (!categoryBreakdownEl) return;

        // Use real category data from backend if available
        let categories = [];
        if (data.category_breakdown && data.category_breakdown.length > 0) {
            categories = data.category_breakdown.map(cat => ({
                name: cat.name,
                score: cat.rating,
                count: cat.count,
                sentiment: cat.sentiment_score >= 0.1 ? 'positive' : cat.sentiment_score <= -0.1 ? 'negative' : 'neutral'
            }));
        } else {
            // Fallback to mock data if no categories detected
            const sentimentData = data.sentiment || {};
            const mockCategories = [
                { name: 'Overall Quality', score: 3.5 },
                { name: 'Value for Money', score: 3.2 },
                { name: 'User Experience', score: 3.0 }
            ];

            categories = mockCategories.map(cat => {
                const adjustment = (sentimentData.positive || 0) * 1.5 - (sentimentData.negative || 0) * 1.5;
                const adjustedScore = Math.max(1, Math.min(5, cat.score + adjustment));

                return {
                    name: cat.name,
                    score: adjustedScore,
                    sentiment: adjustedScore >= 3.5 ? 'positive' : adjustedScore >= 2.5 ? 'neutral' : 'negative'
                };
            });
        }

        categoryBreakdownEl.innerHTML = '';
        categories.forEach(category => {
            const categoryItem = document.createElement('div');
            categoryItem.className = 'category-item';

            const nameSpan = document.createElement('span');
            nameSpan.className = 'category-name';
            nameSpan.textContent = category.name;
            if (category.count) {
                nameSpan.title = `Mentioned in ${category.count} reviews`;
            }

            const scoreSpan = document.createElement('span');
            scoreSpan.className = 'category-score';
            scoreSpan.textContent = category.score.toFixed(1);

            // Color code based on sentiment
            if (category.sentiment === 'positive') {
                scoreSpan.style.backgroundColor = '#E8F5E8';
                scoreSpan.style.color = '#2E7D32';
            } else if (category.sentiment === 'negative') {
                scoreSpan.style.backgroundColor = '#FFEBEE';
                scoreSpan.style.color = '#C62828';
            } else {
                scoreSpan.style.backgroundColor = '#F5F5F5';
                scoreSpan.style.color = '#757575';
            }

            categoryItem.appendChild(nameSpan);
            categoryItem.appendChild(scoreSpan);
            categoryBreakdownEl.appendChild(categoryItem);
        });
    };

    const renderChart = (sentimentData) => {
        if (!chartCanvas || !sentimentData) return;
        if (sentimentChart) sentimentChart.destroy();

        const data = {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [
                    sentimentData.positive * 100 || 0,
                    sentimentData.neutral * 100 || 0,
                    sentimentData.negative * 100 || 0
                ],
                backgroundColor: ['#2E7D32', '#B0BEC5', '#C62828'],
                borderColor: '#F7F9FC',
                borderWidth: 3,
                hoverOffset: 8
            }]
        };

        sentimentChart = new Chart(chartCanvas, {
            type: 'doughnut',
            data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: context => {
                                let label = context.label || '';
                                if (label) label += ': ';
                                if (context.parsed !== null) label += context.parsed.toFixed(1) + '%';
                                return label;
                            }
                        }
                    }
                }
            }
        });
    };

    // --- Analyze Reviews with Async Job Polling ---
    const analyzeReviews = async (reviews) => {
        try {
            // Step 1: Submit job to backend
            console.log("Submitting reviews for analysis:", reviews.length);
            const submitResponse = await fetch(`${API_BASE_URL}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reviews })
            });

            if (!submitResponse.ok) {
                throw new Error(`Failed to submit job: ${submitResponse.status}`);
            }

            const submitResult = await submitResponse.json();
            const jobId = submitResult.job_id;
            console.log("Job submitted with ID:", jobId);

            // Step 2: Poll for results
            const result = await pollForResults(jobId);
            console.log("Analysis complete:", result);
            updateUI('results', result);

        } catch (err) {
            console.error("Error analyzing reviews:", err);
            updateUI('error', { message: err.message || "Analysis failed." });
        }
    };

    // --- Poll for Job Results ---
    const pollForResults = async (jobId, maxAttempts = 30, delay = 1000) => {
        const loadingText = document.querySelector('#loading-view .loading-text');

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                if (loadingText) {
                    loadingText.textContent = `Analyzing reviews... (${attempt}/${maxAttempts})`;
                }

                const response = await fetch(`${API_BASE_URL}/results/${jobId}`);

                if (!response.ok) {
                    throw new Error(`Failed to get results: ${response.status}`);
                }

                const result = await response.json();
                console.log(`Poll attempt ${attempt}:`, result.status);

                if (result.status === 'done') {
                    return result;
                } else if (result.status === 'error') {
                    throw new Error(result.error?.message || 'Analysis job failed');
                }
                // If status is 'pending', continue polling

                // Wait before next poll
                await new Promise(resolve => setTimeout(resolve, delay));
            } catch (err) {
                if (attempt === maxAttempts) {
                    throw err;
                }
                console.warn(`Poll attempt ${attempt} failed, retrying:`, err.message);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        throw new Error('Analysis timed out - please try again');
    };

    // --- NEW UNIQUE ANALYTICS FUNCTIONS ---

    const renderReviewVelocityAnalysis = (data) => {
        const nReviews = data.n_reviews || 0;
        const velocityEl = document.getElementById('velocity-indicator');
        const velocityTextEl = document.getElementById('velocity-text');

        if (!velocityEl || !velocityTextEl) return;

        // Simulate review velocity analysis (in real app, this would come from backend)
        let velocityScore = 'moderate';
        let velocityText = 'Steady review flow';
        let velocityClass = 'moderate';

        if (nReviews > 100) {
            velocityScore = 'high';
            velocityText = 'High review activity - Popular product';
            velocityClass = 'high';
        } else if (nReviews < 20) {
            velocityScore = 'low';
            velocityText = 'Limited reviews - New or niche product';
            velocityClass = 'low';
        }

        velocityEl.className = `velocity-indicator ${velocityClass}`;
        velocityTextEl.textContent = velocityText;
    };

    const renderPriceValueInsights = (data) => {
        const valueEl = document.getElementById('value-score');
        const valueTextEl = document.getElementById('value-insight');
        const valueReasonEl = document.getElementById('value-reason');

        if (!valueEl || !valueTextEl || !valueReasonEl) return;

        const sentimentData = data.sentiment || {};
        const positiveRatio = sentimentData.positive || 0;
        const negativeRatio = sentimentData.negative || 0;

        // Calculate value score (advanced algorithm in real implementation)
        const valueScore = Math.round(60 + (positiveRatio * 30) - (negativeRatio * 20));
        const clampedValue = Math.max(10, Math.min(100, valueScore));

        let valueText = 'Fair Value';
        let valueReason = 'Price matches quality expectations';

        if (clampedValue >= 80) {
            valueText = 'Excellent Value';
            valueReason = 'High quality product for the price point';
        } else if (clampedValue >= 60) {
            valueText = 'Good Value';
            valueReason = 'Reasonable quality-to-price ratio';
        } else if (clampedValue < 40) {
            valueText = 'Poor Value';
            valueReason = 'Quality concerns relative to price';
        }

        // Animate the progress bar with proper timing
        valueEl.style.width = '0%';

        // Use requestAnimationFrame for smooth animation
        setTimeout(() => {
            valueEl.style.width = `${clampedValue}%`;
        }, 100);

        valueTextEl.textContent = `${clampedValue}% - ${valueText}`;
        valueReasonEl.textContent = valueReason;
    };

    // --- End New Analytics Functions ---

    // --- Start Analysis ---
    const startAnalysis = () => {
        console.log("🚀 DEBUG: startAnalysis called");
        updateUI('loading');

        chrome.runtime.sendMessage({ from: 'popup', action: 'scrapeReviews' }, (response) => {
            console.log("🔧 DEBUG: Response received:", response);
            if (chrome.runtime.lastError) {
                console.error("🚨 DEBUG: Chrome runtime error:", chrome.runtime.lastError.message);
                return updateUI('error', { message: "Could not scrape reviews. Reload page and try again." });
            }

            console.log("Response from background:", response);
            const reviews = response?.reviews || [];
            console.log("🔧 DEBUG: Reviews found:", reviews.length);
            if (!reviews.length) {
                return updateUI('error', { message: "No reviews found on this page." });
            }

            // Send reviews to backend and handle async job workflow
            console.log("🔧 DEBUG: Calling analyzeReviews with", reviews.length, "reviews");
            analyzeReviews(reviews);
        });
    };

    // --- Frontend Integration ---
    let currentAnalysisData = null;
    let currentJobId = null;

    // Store analysis data when results are received
    const originalUpdateUI = updateUI;
    updateUI = (state, data = null) => {
        originalUpdateUI(state, data);

        if (state === 'results' && data) {
            currentAnalysisData = data;
            // Show the detailed analysis button
            showDetailedAnalysisOption();
        }
    };

    // Add detailed analysis button to results view
    const showDetailedAnalysisOption = () => {
        const resultsView = document.getElementById('results-view');
        if (!resultsView || resultsView.querySelector('.detailed-analysis-btn')) return;

        const detailedBtn = document.createElement('button');
        detailedBtn.className = 'detailed-analysis-btn';
        detailedBtn.textContent = '📊 View Detailed Analysis';
        detailedBtn.style.cssText = `
            width: 100%;
            margin-top: 15px;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        `;

        detailedBtn.addEventListener('mouseover', () => {
            detailedBtn.style.transform = 'translateY(-2px)';
            detailedBtn.style.boxShadow = '0 8px 25px rgba(102, 126, 234, 0.4)';
        });

        detailedBtn.addEventListener('mouseout', () => {
            detailedBtn.style.transform = 'translateY(0)';
            detailedBtn.style.boxShadow = 'none';
        });

        detailedBtn.addEventListener('click', openDetailedAnalysis);

        // Add to the end of results view
        resultsView.appendChild(detailedBtn);
    };

    // Open detailed analysis in frontend
    const openDetailedAnalysis = () => {
        if (!currentAnalysisData) return;

        // Get current page info
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const currentTab = tabs[0];
            const pageInfo = {
                url: currentTab.url,
                title: currentTab.title,
                timestamp: new Date().toISOString()
            };

            // Prepare data for the HTML viewer
            const frontendData = {
                ...currentAnalysisData,
                source: 'extension',
                page_info: pageInfo,
                job_id: currentJobId
            };

            // Store data in localStorage for viewer to pickup
            const analysisId = `analysis_${Date.now()}`;
            localStorage.setItem(`revuze_${analysisId}`, JSON.stringify(frontendData));

            // Open the analysis viewer HTML page
            const viewerURL = chrome.runtime.getURL(`analysis-viewer.html?analysis=${analysisId}`);
            chrome.tabs.create({ url: viewerURL });
        });
    };

    // Enhanced analyzeReviews to store job ID
    const originalAnalyzeReviews = analyzeReviews;
    analyzeReviews = async (reviews) => {
        console.log("🔧 DEBUG: analyzeReviews called with", reviews.length, "reviews");
        console.log("🔧 DEBUG: API_BASE_URL:", API_BASE_URL);
        try {
            // Step 1: Submit reviews for analysis
            console.log("🔧 DEBUG: Submitting to backend...");
            const submitResponse = await fetch(`${API_BASE_URL}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ reviews })
            });

            console.log("🔧 DEBUG: Submit response status:", submitResponse.status);
            if (!submitResponse.ok) {
                throw new Error(`Analysis submission failed: ${submitResponse.status}`);
            }

            const submitData = await submitResponse.json();
            const jobId = submitData.job_id;
            currentJobId = jobId; // Store for frontend integration

            console.log(`🔧 DEBUG: Analysis job submitted with ID: ${jobId}`);

            // Step 2: Poll for results
            const result = await pollForResults(jobId);

            updateUI('results', result);
        } catch (error) {
            console.error("🚨 DEBUG: Analysis failed:", error);
            updateUI('error', { message: error.message });
        }
    };

    if (analyzeButton) {
        console.log("🔧 DEBUG: Adding click listener to analyze button");
        analyzeButton.addEventListener('click', startAnalysis);
    } else {
        console.error("🚨 DEBUG: Analyze button not found!");
    }
    if (retryButton) retryButton.addEventListener('click', () => updateUI('idle'));

    updateUI('idle');
});
