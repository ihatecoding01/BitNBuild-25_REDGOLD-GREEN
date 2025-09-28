"""
Integration wrapper for the advanced sentiment analyzer
"""
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from .review_sentiment_analyser import analyze_reviews as advanced_analyze
from core.errors import AnalysisError


def analyze_reviews_advanced(reviews: List[str]) -> Dict[str, Any]:
    """
    Wrapper function that uses the advanced sentiment analyzer
    and formats output to match the API expectations.
    """
    if not reviews:
        raise AnalysisError("Cannot analyze an empty list of reviews.")
    
    print(f"ADVANCED NLP: Starting analysis of {len(reviews)} reviews...")
    
    try:
        # Create DataFrame from reviews list
        df = pd.DataFrame([
            {"review_id": idx, "review_text": text} 
            for idx, text in enumerate(reviews)
        ])
        
        # Define aspects for analysis
        candidate_aspects = [
            "battery", "screen", "camera", "performance", "price", 
            "design", "customer service", "shipping", "quality", "features"
        ]
        
        # Run the advanced analysis with optimized settings for speed
        results_df, category_summary_df, top_keywords, meta = advanced_analyze(
            df=df,
            candidate_aspects=candidate_aspects,
            aspect_method='keywords',  # Use faster keyword method
            cache_sentiment=True,      # Cache for speed
            collect_timings=False,
            device=-1  # Use CPU (more reliable than GPU detection)
        )
        
        # Extract overall sentiment distribution
        sentiment_counts = results_df['overall_label'].value_counts()
        total_reviews = len(results_df)
        
        sentiment_breakdown = {
            "positive": float(sentiment_counts.get('positive', 0) / total_reviews),
            "neutral": float(sentiment_counts.get('neutral', 0) / total_reviews),
            "negative": float(sentiment_counts.get('negative', 0) / total_reviews)
        }
        
        counts = {
            "positive": int(sentiment_counts.get('positive', 0)),
            "neutral": int(sentiment_counts.get('neutral', 0)),
            "negative": int(sentiment_counts.get('negative', 0))
        }
        
        # Extract top positive and negative keywords
        def format_keywords(kw_list, limit=10):
            return [
                {"term": term, "score": float(score)} 
                for term, score in kw_list[:limit]
            ]
        
        top_positive = format_keywords(top_keywords.get('positive', []))
        top_negative = format_keywords(top_keywords.get('negative', []))
        
        # Extract category-wise analysis
        category_data = []
        for _, row in category_summary_df.iterrows():
            if row['count'] > 0:  # Only include categories with mentions
                category_data.append({
                    "name": row['category'].title(),
                    "rating": float(row['rating_stars']) if not pd.isna(row['rating_stars']) else 3.0,
                    "count": int(row['count']),
                    "sentiment_score": float(row['mean_score']) if not pd.isna(row['mean_score']) else 0.0
                })
        
        # Sort by count (most mentioned first)
        category_data.sort(key=lambda x: x['count'], reverse=True)
        
        # Calculate authenticity indicators
        avg_review_length = results_df['review_text'].str.len().mean() if len(results_df) > 0 else 50
        sentiment_variance = np.var([sentiment_breakdown['positive'], sentiment_breakdown['neutral'], sentiment_breakdown['negative']])
        
        result = {
            "sentiment": sentiment_breakdown,
            "counts": counts,
            "top_positive": top_positive,
            "top_negative": top_negative,
            "n_reviews": total_reviews,
            "overall_rating_stars": meta.get('overall_rating_stars', 3.0),
            "categories_analyzed": len(category_data),
            "category_breakdown": category_data[:6],  # Top 6 categories
            
            # Authenticity indicators for unique analysis
            "authenticity_metrics": {
                "avg_review_length": float(avg_review_length),
                "sentiment_variance": float(sentiment_variance),
                "keyword_diversity": len(set([kw['term'] for kw in top_positive + top_negative])),
                "category_coverage": len([c for c in category_data if c['count'] >= 2])
            }
        }
        
        print(f"ADVANCED NLP: Analysis complete. Processed {total_reviews} reviews with {len(top_keywords)} key insights.")
        
        analysis = {
            "sentiment": sentiment_breakdown,
            "counts": counts,
            "top_positive": top_positive,
            "top_negative": top_negative,
            "n_reviews": total_reviews,
            "overall_rating_stars": meta.get('overall_rating_stars', 3.0),
            "categories_analyzed": len(category_data),
            "category_breakdown": category_data[:6],  # Top 6 categories
            
            # Authenticity indicators for unique analysis
            "authenticity_metrics": {
                "avg_review_length": float(avg_review_length),
                "sentiment_variance": float(sentiment_variance),
                "keyword_diversity": len(set([kw['term'] for kw in top_positive + top_negative])),
                "category_coverage": len([c for c in category_data if c['count'] >= 2])
            }
        }
        return result
        
    except Exception as e:
        print(f"ADVANCED NLP: Error during analysis: {str(e)}")
        raise AnalysisError(f"Advanced sentiment analysis failed: {str(e)}")