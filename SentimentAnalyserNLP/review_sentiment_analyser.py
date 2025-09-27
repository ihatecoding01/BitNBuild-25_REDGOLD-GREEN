#!/usr/bin/env python3
"""
Review Radar - Sentiment & Aspect Analyzer
Reads reviews from a CSV (column 'review_text' required), runs:
 - Zero-shot classification to detect which aspects/categories a sentence mentions
 - Sentiment analysis on sentences
Aggregates:
 - Per-review sentiment
 - Per-category sentiment (aggregated across sentences/reviews)
 - Overall numeric rating (1-5)
Produces:
 - CSV outputs with per-review and per-category summaries
 - PNG graphs (sentiment distribution, category ratings, top keywords)

Usage:
    python review_sentiment_analyzer.py --input sample_reviews.csv --outdir results

If sample CSV not provided / not found it will generate a small sample file.
"""

import os
import re
import argparse
import json
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import seaborn as sns

# HuggingFace
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# --------------------
# Utility functions
# --------------------

def simple_sentence_split(text):
    """Split text into sentences with a regex (avoids NLTK dependency)."""
    if not isinstance(text, str):
        return []
    # keep newlines as sentence boundary too
    text = text.replace('\n', ' ')
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    # remove tiny parts
    return [p.strip() for p in parts if len(p.strip()) > 0]


def normalize_sentiment_label(raw_label: str) -> str:
    """Map raw model output label to one of positive|neutral|negative."""
    lab = raw_label.lower()
    if 'pos' in lab or 'positive' in lab or 'label_2' in lab:
        return 'positive'
    if 'neg' in lab or 'negative' in lab or 'label_0' in lab:
        return 'negative'
    if 'neu' in lab or 'neutral' in lab or 'label_1' in lab:
        return 'neutral'
    # fallback heuristic: treat unknown as neutral
    return 'neutral'

def map_sentiment_label_to_score(label: str, score: float):
    """Convert a normalized label (or raw label) to numeric -1..1 score."""
    norm = normalize_sentiment_label(label)
    if norm == 'positive':
        return float(score)
    if norm == 'negative':
        return -float(score)
    return 0.0


def numeric_score_to_stars(avg_score):
    """
    avg_score expected in [-1, 1].
    Map to 1..5 stars:
    rating = ((avg_score + 1) / 2) * 4 + 1
    """
    clipped = max(-1.0, min(1.0, avg_score))
    return round(((clipped + 1.0) / 2.0) * 4.0 + 1.0, 2)


# --------------------
# Main analysis code
# --------------------

def analyze_reviews(df,
                    candidate_aspects,
                    zsc_model_name='facebook/bart-large-mnli',
                    sentiment_model_name='cardiffnlp/twitter-roberta-base-sentiment',
                    zsc_threshold=0.35,
                    device=-1,
                    example_limit: int = 3):
    """
    df: pandas dataframe with column 'review_text'
    candidate_aspects: list[str] : aspects to detect (e.g., battery, screen...)
    Returns:
        results_df: per-review dataframe
        category_summary_df: per-category aggregated metrics
        top_keywords: dict with 'positive' and 'negative' lists
    """

    # Initialize pipelines (takes time and downloads models on first run)
    print("Loading Zero-Shot Classification pipeline (...this may take a while on first run)...")
    zsc = pipeline("zero-shot-classification", model=zsc_model_name, device=device)

    print("Loading Sentiment pipeline (...this may take a while on first run)...")
    sentiment = pipeline("sentiment-analysis", model=sentiment_model_name, device=device)

    # Prepare outputs
    per_review_results = []
    # category -> list of numeric scores (range roughly -1..1)
    category_scores: Dict[str, List[float]] = {cat: [] for cat in candidate_aspects}
    # category -> list of (sentence, norm_label, sentiment_confidence)
    category_sentence_examples: Dict[str, List[Tuple[str, str, float]]] = {cat: [] for cat in candidate_aspects}
    # per-category sentiment counts
    category_sentiment_counts: Dict[str, Counter] = {cat: Counter() for cat in candidate_aspects}
    # accumulate all sentences classified as positive / negative for keyword extraction
    positive_texts = []
    negative_texts = []

    # iterate reviews
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Analyzing reviews"):
        text = str(row.get('review_text', '')).strip()
        review_id = row.get('review_id', idx)
        if not text:
            continue

        sentences = simple_sentence_split(text)
        if len(sentences) == 0:
            sentences = [text]

        # Zero-shot classify each sentence (multi_label True so a sentence can mention multiple aspects)
        zsc_results = zsc(sentences, candidate_labels=candidate_aspects, multi_label=True)

        # accumulate per-category sentence sentiments for this review
        per_category_sentences = defaultdict(list)

        for s_idx, s in enumerate(sentences):
            result = zsc_results[s_idx]
            # result: dict with 'labels' and 'scores', labels in order of candidate_aspects or top ones
            labels = result['labels']
            scores = result['scores']
            # map each label to score and accept if above threshold
            for lab, sc in zip(labels, scores):
                if sc >= zsc_threshold:
                    per_category_sentences[lab].append((s, sc))

        # For each category that appears in this review, run sentiment on the sentences assigned to it
        review_category_scores = {}
        for cat, sents in per_category_sentences.items():
            # run sentiment on the sentences (batch)
            texts_for_sentiment = [s for s, _ in sents]
            sent_out = sentiment(texts_for_sentiment)
            # map labels to numeric and compute mean
            numeric_vals = []
            for o, original_text in zip(sent_out, texts_for_sentiment):
                raw_label = o['label']
                conf = o.get('score', 1.0)
                norm_label = normalize_sentiment_label(raw_label)
                numeric_vals.append(map_sentiment_label_to_score(norm_label, conf))
                # store example only if sentence actually contains the aspect token (loose check)
                if cat.lower() in original_text.lower():
                    category_sentence_examples[cat].append((original_text, norm_label, conf))
                category_sentiment_counts[cat][norm_label] += 1
            # weight by the zero-shot score optionally? For simplicity, average numeric_vals
            if len(numeric_vals) > 0:
                mean_cat_score = float(np.mean(numeric_vals))
                review_category_scores[cat] = mean_cat_score
                # store in global category_scores
                category_scores[cat].append(mean_cat_score)

                # accumulate for keyword extraction
                if mean_cat_score > 0.05:
                    positive_texts.extend(texts_for_sentiment)
                elif mean_cat_score < -0.05:
                    negative_texts.extend(texts_for_sentiment)

        # If no category sentences found, fall back to computing overall sentiment on whole review
        overall_sent = sentiment(text)
        # overall_sent is a list with one dict
        overall_label_raw = overall_sent[0]['label']
        overall_label = normalize_sentiment_label(overall_label_raw)
        overall_score_raw = overall_sent[0].get('score', 1.0)
        overall_numeric = map_sentiment_label_to_score(overall_label, overall_score_raw)

        # Save per-review result
        per_review_results.append({
            'review_id': review_id,
            'review_text': text,
            'overall_label': overall_label,
            'overall_score_raw': overall_score_raw,
            'overall_numeric': overall_numeric,
            'per_category_scores': json.dumps(review_category_scores)
        })
        # also tag text for keywords
        if overall_numeric > 0.05:
            positive_texts.append(text)
        elif overall_numeric < -0.05:
            negative_texts.append(text)

    results_df = pd.DataFrame(per_review_results)

    # compute overall numeric average across reviews
    avg_score = results_df['overall_numeric'].mean() if len(results_df) > 0 else 0.0
    overall_rating_stars = numeric_score_to_stars(avg_score)

    # per-category summary with examples
    category_summary = []
    for cat in candidate_aspects:
        scores = category_scores.get(cat, [])
        examples = category_sentence_examples.get(cat, [])
        sent_counts = category_sentiment_counts.get(cat, Counter())
        if len(scores) == 0:
            mean_score = np.nan
            count = 0
            pos_examples = []
            neg_examples = []
            pos_c = neg_c = neu_c = 0
        else:
            mean_score = float(np.mean(scores))
            count = len(scores)
            # pick positive examples (label == positive) sorted by confidence
            pos_examples_all = [(s, c) for (s, lab, c) in examples if lab == 'positive']
            neg_examples_all = [(s, c) for (s, lab, c) in examples if lab == 'negative']
            pos_examples_all.sort(key=lambda x: x[1], reverse=True)
            neg_examples_all.sort(key=lambda x: x[1], reverse=True)
            pos_examples = [s for s, _ in pos_examples_all[:example_limit]]
            neg_examples = [s for s, _ in neg_examples_all[:example_limit]]
            pos_c = sent_counts.get('positive', 0)
            neg_c = sent_counts.get('negative', 0)
            neu_c = sent_counts.get('neutral', 0)
        rating_stars = numeric_score_to_stars(mean_score) if not np.isnan(mean_score) else np.nan
        category_summary.append({
            'category': cat,
            'mean_score': mean_score,
            'count': count,
            'rating_stars': rating_stars,
            'sent_count_positive': pos_c,
            'sent_count_neutral': neu_c,
            'sent_count_negative': neg_c,
            'top_positive_examples': json.dumps(pos_examples, ensure_ascii=False),
            'top_negative_examples': json.dumps(neg_examples, ensure_ascii=False)
        })
    category_summary_df = pd.DataFrame(category_summary).sort_values('count', ascending=False)

    # extract top keywords with TF-IDF from positive / negative texts
    top_keywords = {'positive': [], 'negative': []}
    def get_top_tfidf(corpus, top_n=15):
        if not corpus:
            return []
        vect = TfidfVectorizer(stop_words='english', max_features=500)
        X = vect.fit_transform(corpus)
        sums = np.asarray(X.sum(axis=0)).ravel()
        terms = np.array(vect.get_feature_names_out())
        top_idx = sums.argsort()[::-1][:top_n]
        return list(zip(terms[top_idx], sums[top_idx]))

    top_keywords['positive'] = get_top_tfidf(positive_texts, top_n=20)
    top_keywords['negative'] = get_top_tfidf(negative_texts, top_n=20)

    meta = {
        'overall_avg_score': float(avg_score),
        'overall_rating_stars': overall_rating_stars,
        'num_reviews_analyzed': len(results_df)
    }

    return results_df, category_summary_df, top_keywords, meta


# --------------------
# Plotting / saving outputs
# --------------------

def save_outputs(outdir: Path, results_df: pd.DataFrame, category_summary_df: pd.DataFrame, top_keywords: dict, meta: dict):
    outdir.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(outdir / "per_review_results.csv", index=False)
    category_summary_df.to_csv(outdir / "category_summary.csv", index=False)

    # 1) Sentiment distribution pie chart
    # Replace raw labels with normalized labels already stored; ensure ordering
    counts = results_df['overall_label'].value_counts()
    plt.figure(figsize=(6,6))
    counts.plot.pie(autopct='%1.1f%%', ylabel='', title='Sentiment distribution')
    plt.savefig(outdir / "sentiment_distribution_pie.png", bbox_inches='tight')
    plt.close()

    # 2) Category ratings bar chart
    if not category_summary_df.empty:
        plt.figure(figsize=(10,6))
        sns.barplot(data=category_summary_df, x='rating_stars', y='category', orient='h')
        plt.title('Category ratings (1-5 stars)')
        plt.xlabel('Rating (stars)')
        plt.ylabel('Category')
        plt.xlim(1,5)
        plt.tight_layout()
        plt.savefig(outdir / "category_ratings_bar.png", bbox_inches='tight')
        plt.close()

    # 3) Top positive keywords
    def plot_top_keywords(klist, title, fname):
        if not klist:
            return
        words, scores = zip(*klist[:20])
        plt.figure(figsize=(8,6))
        sns.barplot(x=list(scores)[::-1], y=list(words)[::-1])  # reverse to have most at top
        plt.title(title)
        plt.xlabel('TF-IDF score (relative)')
        plt.tight_layout()
        plt.savefig(outdir / fname, bbox_inches='tight')
        plt.close()

    plot_top_keywords(top_keywords.get('positive', []), 'Top keywords in positive sentences', "top_positive_keywords.png")
    plot_top_keywords(top_keywords.get('negative', []), 'Top keywords in negative sentences', "top_negative_keywords.png")

    # Save meta
    with open(outdir / "analysis_meta.json", 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"Saved outputs to {outdir.resolve()}")

# --------------------
# Sample CSV generator
# --------------------

def generate_sample_csv(path):
    sample_reviews = [
        {"review_id": 1, "review_text": "Battery life is amazing — lasted two days. The screen is bright and crisp. Camera is okay but not great."},
        {"review_id": 2, "review_text": "Terrible customer service. The phone froze a lot. Shipping was delayed by a week."},
        {"review_id": 3, "review_text": "Excellent performance, snappy UI and great design. Price is a bit high but worth it."},
        {"review_id": 4, "review_text": "Battery drains fast when gaming. Overheats sometimes."},
        {"review_id": 5, "review_text": "Good value for money. Camera is excellent, photos are sharp."},
        {"review_id": 6, "review_text": "I love the design but screen cracked easily. Customer service helped replace it quickly."},
    ]
    pd.DataFrame(sample_reviews).to_csv(path, index=False)
    print(f"Generated sample CSV at {path}")


# --------------------
# CLI + main
# --------------------
def main():
    parser = argparse.ArgumentParser(description="Review Radar - sentiment & aspect-based analyzer")
    parser.add_argument('--input', '-i', type=str, default='sample_reviews.csv', help='Input CSV file path (must have column review_text). If missing a sample will be generated.')
    parser.add_argument('--outdir', '-o', type=str, default='results', help='Output directory for CSVs and images')
    parser.add_argument('--aspects', '-a', type=str,
                        default="battery,screen,camera,performance,price,design,customer service,shipping",
                        help='Comma-separated list of aspects/categories to detect')
    parser.add_argument('--zsc_model', type=str, default='facebook/bart-large-mnli', help='Zero-shot model (HF model id)')
    parser.add_argument('--sent_model', type=str, default='cardiffnlp/twitter-roberta-base-sentiment', help='Sentiment model (HF model id)')
    parser.add_argument('--zsc_threshold', type=float, default=0.35, help='threshold for zero-shot category assignment (0-1)')
    parser.add_argument('--use_gpu', action='store_true', help='Attempt to use GPU (if available)')
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    aspects = [a.strip() for a in args.aspects.split(',') if a.strip()]

    if not input_path.exists():
        print(f"Input CSV {input_path} not found — creating a small sample file.")
        generate_sample_csv(input_path)

    df = pd.read_csv(input_path)
    if 'review_text' not in df.columns:
        raise ValueError("Input CSV must contain a column named 'review_text'")

    # device selection for HF pipelines:
    device = 0 if (args.use_gpu and __import__('torch').cuda.is_available()) else -1

    results_df, category_summary_df, top_keywords, meta = analyze_reviews(
        df=df,
        candidate_aspects=aspects,
        zsc_model_name=args.zsc_model,
        sentiment_model_name=args.sent_model,
        zsc_threshold=args.zsc_threshold,
        device=device
    )

    # add star column for per-review numeric -> stars mapping
    results_df['rating_stars'] = results_df['overall_numeric'].apply(lambda x: numeric_score_to_stars(x))

    save_outputs(outdir, results_df, category_summary_df, top_keywords, meta)

    # Detailed terminal summary
    print("\n=== OVERALL SUMMARY ===")
    print(f"Reviews analyzed: {meta['num_reviews_analyzed']}")
    print(f"Overall avg sentiment score: {meta['overall_avg_score']:.3f}  => Stars: {meta['overall_rating_stars']}")

    # Sentiment distribution
    dist = results_df['overall_label'].value_counts(normalize=True) * 100.0
    print("\nSentiment distribution (% of reviews):")
    for lab in ['positive', 'neutral', 'negative']:
        if lab in dist:
            print(f"  {lab.capitalize():8}: {dist[lab]:5.1f}%")

    print("\n=== CATEGORY DETAILS ===")
    for _, row in category_summary_df.iterrows():
        if row['count'] == 0:
            continue
        cat = row['category']
        mean_score = row['mean_score']
        stars = row['rating_stars']
        sentiment_label = 'positive' if mean_score > 0.1 else ('negative' if mean_score < -0.1 else 'neutral')
        print(f"\n[{cat}] Mentions: {int(row['count'])}  MeanScore: {mean_score:.3f}  Stars: {stars}  => {sentiment_label.upper()}")
        if 'sent_count_positive' in row:
            print(f"   Sentence sentiment counts -> +:{int(row['sent_count_positive'])} 0:{int(row['sent_count_neutral'])} -:{int(row['sent_count_negative'])}")
        # show examples
        try:
            pos_examples = json.loads(row['top_positive_examples'])
            neg_examples = json.loads(row['top_negative_examples'])
        except Exception:
            pos_examples, neg_examples = [], []
        if pos_examples:
            print("  Positive examples:")
            for ex in pos_examples:
                print("   +", ex)
        if neg_examples:
            print("  Negative examples:")
            for ex in neg_examples:
                print("   -", ex)

    print("\n=== TOP KEYWORDS ===")
    def show_kw(label, kws):
        if not kws:
            print(f"  {label.capitalize()}: (none)")
            return
        top_formatted = ", ".join([w for w, _ in kws[:15]])
        print(f"  {label.capitalize()}: {top_formatted}")
    show_kw('positive', top_keywords.get('positive'))
    show_kw('negative', top_keywords.get('negative'))

if __name__ == "__main__":
    main()
