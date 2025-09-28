"""Heavy transformer-based review analysis extracted from original script.

Public entrypoint:
  run_heavy_analysis(reviews: list[str], *, aspects: list[str], aspect_method='zsc', ... ) -> dict
Returns simplified structure similar to lightweight analyzer but preserves
category details and overall distribution. Internals borrowed from original
SentimentAnalyser/review_sentiment_analyser.py analyze_reviews function.

Note: plotting, CSV writing, CLI, and keyword extraction outputs omitted here.
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple
import json, math, time
from collections import defaultdict, Counter

try:
    import pandas as pd
    import numpy as np
    from transformers import pipeline
except Exception as e:  # pragma: no cover
    raise ImportError("Heavy analyzer dependencies missing. Install transformers and pandas.") from e

# ---- Utility helpers (trimmed from original) ----

def simple_sentence_split(text: str) -> List[str]:
    import re
    if not isinstance(text, str):
        return []
    text = text.replace('\n', ' ')
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]

def normalize_sentiment_label(raw_label: str) -> str:
    lab = raw_label.lower()
    if 'pos' in lab or 'positive' in lab or 'label_2' in lab:
        return 'positive'
    if 'neg' in lab or 'negative' in lab or 'label_0' in lab:
        return 'negative'
    if 'neu' in lab or 'neutral' in lab or 'label_1' in lab:
        return 'neutral'
    return 'neutral'

def map_sentiment_label_to_score(label: str, score: float) -> float:
    norm = normalize_sentiment_label(label)
    if norm == 'positive':
        return float(score)
    if norm == 'negative':
        return -float(score)
    return 0.0

# star rating helper

def numeric_score_to_stars(avg_score: float) -> float:
    clipped = max(-1.0, min(1.0, avg_score))
    return round(((clipped + 1.0) / 2.0) * 4.0 + 1.0, 2)

# ---- Core heavy analysis (condensed) ----

def run_heavy_analysis(
    reviews: List[str],
    *,
    aspects: List[str],
    aspect_method: str = 'zsc',
    zsc_model_name: str = 'facebook/bart-large-mnli',
    sentiment_model_name: str = 'cardiffnlp/twitter-roberta-base-sentiment',
    zsc_threshold: float = 0.35,
    zsc_batch_size: int = 4,
    sent_batch_size: int = 16,
    cache_sentiment: bool = True,
) -> Dict[str, Any]:
    if not reviews:
        return {"sentiment": {"positive":0,"neutral":0,"negative":0}, "counts": {"positive":0,"neutral":0,"negative":0}, "n_reviews":0, "categories": []}

    df = pd.DataFrame({"review_id": range(1, len(reviews)+1), "review_text": reviews})

    if aspect_method == 'zsc':
        zsc = pipeline('zero-shot-classification', model=zsc_model_name, device=-1)
    else:
        zsc = None
    sentiment = pipeline('sentiment-analysis', model=sentiment_model_name, device=-1)

    category_scores: Dict[str, List[float]] = {a: [] for a in aspects}
    category_sentiment_counts: Dict[str, Counter] = {a: Counter() for a in aspects}

    sentiment_cache: Dict[str, Tuple[str,float,float]] = {}
    per_review_labels: List[str] = []

    for _, row in df.iterrows():
        text = str(row.review_text).strip()
        if not text:
            continue
        sentences = simple_sentence_split(text) or [text]
        per_category_sentences = defaultdict(list)
        if aspect_method == 'zsc':
            zsc_results = zsc(sentences, candidate_labels=aspects, multi_label=True, batch_size=zsc_batch_size)
            for s_idx, s in enumerate(sentences):
                result = zsc_results[s_idx]
                labels = result['labels']
                scores = result['scores']
                for lab, sc in zip(labels, scores):
                    if sc >= zsc_threshold:
                        per_category_sentences[lab].append((s, sc))
        else:
            # keyword heuristic
            lower_sentences = [s.lower() for s in sentences]
            for s, low in zip(sentences, lower_sentences):
                for a in aspects:
                    if a.lower() in low:
                        per_category_sentences[a].append((s,1.0))

        review_overall_numeric = 0.0
        review_overall_label = 'neutral'
        # aggregate per category
        for cat, sents in per_category_sentences.items():
            texts_for_sentiment = [s for s,_ in sents]
            to_infer = [s for s in texts_for_sentiment if (not cache_sentiment) or (s not in sentiment_cache)]
            if to_infer:
                new_out = sentiment(to_infer, batch_size=sent_batch_size)
                for s_text, o in zip(to_infer, new_out):
                    norm = normalize_sentiment_label(o['label'])
                    conf = o.get('score',1.0)
                    numeric = map_sentiment_label_to_score(norm, conf)
                    if cache_sentiment:
                        sentiment_cache[s_text] = (norm, conf, numeric)
            # gather
            numeric_vals = []
            for s_text in texts_for_sentiment:
                if cache_sentiment and s_text in sentiment_cache:
                    norm, conf, numeric = sentiment_cache[s_text]
                else:
                    o = sentiment(s_text)[0]
                    norm = normalize_sentiment_label(o['label'])
                    conf = o.get('score',1.0)
                    numeric = map_sentiment_label_to_score(norm, conf)
                category_sentiment_counts[cat][norm] += 1
                numeric_vals.append(numeric)
            if numeric_vals:
                mean_cat_score = float(sum(numeric_vals)/len(numeric_vals))
                category_scores[cat].append(mean_cat_score)

        # overall review sentiment (whole text)
        if cache_sentiment and text in sentiment_cache:
            review_overall_label = sentiment_cache[text][0]
            review_overall_numeric = sentiment_cache[text][2]
        else:
            o = sentiment(text)[0]
            review_overall_label = normalize_sentiment_label(o['label'])
            review_overall_numeric = map_sentiment_label_to_score(review_overall_label, o.get('score',1.0))
            if cache_sentiment:
                sentiment_cache[text] = (review_overall_label, o.get('score',1.0), review_overall_numeric)
        per_review_labels.append(review_overall_label)

    # aggregate categories to output structure
    cat_rows = []
    for cat, scores in category_scores.items():
        if not scores:
            continue
        mean_score = sum(scores)/len(scores)
        cat_rows.append({
            'category': cat,
            'n_reviews': len(scores),
            'mean_score': round(mean_score,4),
            'rating_stars': numeric_score_to_stars(mean_score)
        })
    cat_rows.sort(key=lambda r: abs(r['mean_score']), reverse=True)

    total = len(per_review_labels) or 1
    dist_counts = {k: per_review_labels.count(k) for k in ('positive','neutral','negative')}
    dist = {k: round(v/total,4) for k,v in dist_counts.items()}
    return {
        'sentiment': dist,
        'counts': dist_counts,
        'n_reviews': len(per_review_labels),
        'categories': cat_rows,
        'mode': 'heavy'
    }
