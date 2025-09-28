from typing import List, Dict, Any
from core.errors import AnalysisError

# Import the advanced sentiment analyzer
try:
    from .sentiment_integration import analyze_reviews_advanced
    USE_ADVANCED_ANALYZER = True
    print("✅ Advanced sentiment analyzer loaded successfully")
except ImportError as e:
    print(f"⚠️ Advanced analyzer not available ({e}), falling back to mock")
    USE_ADVANCED_ANALYZER = False
    import time
    import random
    from collections import Counter

def analyze_reviews(reviews: List[str]) -> Dict[str, Any]:
    """
    Main NLP analysis function that uses advanced sentiment analysis when available,
    otherwise falls back to mock analysis for testing.
    """
    if USE_ADVANCED_ANALYZER:
        return analyze_reviews_advanced(reviews)
    else:
        return analyze_reviews_mock(reviews)

def analyze_reviews_mock(reviews: List[str]) -> Dict[str, Any]:
    """
    Mock NLP analysis function (fallback when advanced analyzer unavailable).
    - Simulates processing time.
    - Returns a deterministic, structured analysis based on input.
    - Can be made to fail to test error handling.
    """
    print(f"MOCK NLP: Starting analysis of {len(reviews)} reviews...")
    time.sleep(random.uniform(1, 3)) # Simulate CPU-bound work

    if not reviews:
        raise AnalysisError("Cannot analyze an empty list of reviews.")
    
    if any("trigger_nlp_fail" in review for review in reviews):
        raise AnalysisError("Mock error: Unhandled token in NLP model.")

    # --- Generate mock analysis data ---
    n_reviews = len(reviews)
    counts = {
        "positive": 0,
        "negative": 0,
        "neutral": 0,
    }
    
    # Simple keyword-based sentiment counting
    for review in reviews:
        if "disappointed" in review or "poor" in review or "buggy" in review or "terrible" in review:
            counts["negative"] += 1
        elif "love" in review or "best" in review or "outstanding" in review or "perfectly" in review:
            counts["positive"] += 1
        else:
            counts["neutral"] += 1
    
    # Ensure no division by zero and handle cases where one sentiment is 100%
    if counts["positive"] == 0 and counts["negative"] == 0:
        counts["neutral"] = n_reviews
    
    total = sum(counts.values())
    if total == 0: total = 1 # Avoid division by zero

    sentiment_breakdown = {k: round(v / total, 2) for k, v in counts.items()}

    # Ensure sentiment fractions sum to 1.0
    sentiment_sum = sum(sentiment_breakdown.values())
    if sentiment_sum != 1.0 and total > 0:
        diff = 1.0 - sentiment_sum
        sentiment_breakdown[max(sentiment_breakdown, key=sentiment_breakdown.get)] += diff

    analysis = {
        "sentiment": sentiment_breakdown,
        "counts": counts,
        "top_positive": [
            {"term": "battery life", "score": 0.31},
            {"term": "screen", "score": 0.25},
            {"term": "build quality", "score": 0.19},
            {"term": "performance", "score": 0.15},
            {"term": "setup", "score": 0.10},
        ],
        "top_negative": [
            {"term": "customer service", "score": 0.28},
            {"term": "battery", "score": 0.22},
            {"term": "software bugs", "score": 0.18},
            {"term": "dead pixel", "score": 0.14},
            {"term": "return process", "score": 0.11},
        ],
        "n_reviews": n_reviews
    }
    
    print("MOCK NLP: Analysis complete.")
    return analysis
