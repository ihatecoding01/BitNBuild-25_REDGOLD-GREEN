from typing import List, Dict, Any
import math
from ..core.errors import AnalysisError
from analysis.review_analysis import analyze_reviews_advanced

def analyze_reviews(reviews: List[str]) -> Dict[str, Any]:
    """Production analyzer wrapper around advanced analysis module.

    Raises AnalysisError if list is empty.
    """
    if not reviews:
        raise AnalysisError("Cannot analyze an empty list of reviews.")
    try:
        result = analyze_reviews_advanced(reviews, aspect_method="keywords", cache_sentiment=True)
        # adapt to existing expected keys: ensure top_positive / top_negative present
        # For now derive simple placeholder lists from category scores
        cats = result.get("categories", [])
        # pick top positive / negative categories by mean_score if present
        positives = sorted([c for c in cats if not math.isnan(c.get('mean_score', float('nan')))], key=lambda c: c.get('mean_score',0), reverse=True)[:5]
        negatives = sorted([c for c in cats if not math.isnan(c.get('mean_score', float('nan')))], key=lambda c: c.get('mean_score',0))[:5]
        top_positive = [{"term": c['category'], "score": c.get('mean_score',0)} for c in positives]
        top_negative = [{"term": c['category'], "score": c.get('mean_score',0)} for c in negatives]
        return {
            "sentiment": result['sentiment'],
            "counts": result['counts'],
            "top_positive": top_positive,
            "top_negative": top_negative,
            "n_reviews": result['n_reviews']
        }
    except Exception as e:
        # fallback small structure
        return {"sentiment": {"positive":0,"neutral":1.0,"negative":0}, "counts": {"positive":0,"neutral":len(reviews),"negative":0}, "top_positive": [], "top_negative": [], "n_reviews": len(reviews)}
