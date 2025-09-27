"""
review_analyzer.py

Requirements:
  pip install transformers torch scikit-learn pandas
  Optional (KeyBERT semantic keywords): pip install keybert sentence-transformers

Usage:
  - Run with sample reviews:
      python review_analyzer.py
  - Or run on CSV (a column with review text):
      python review_analyzer.py --csv reviews.csv --col review_text
  - Or run on JSON Lines file (like Amazon reviews):
      python review_analyzer.py --json reviews.json --max_reviews 1000
      python review_analyzer.py --json reviews.json --json_text_field reviewText --max_reviews 500

Outputs a printed summary and returns a structured dict from analyze_reviews().
"""

import re
import argparse
import json
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

# Transformers / HF pipeline
from transformers import pipeline
import torch

# TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer

# Try KeyBERT (optional)
try:
    from keybert import KeyBERT
    KEYBERT_AVAILABLE = True
except Exception:
    KEYBERT_AVAILABLE = False

# ------------------------
# Utilities
# ------------------------
def clean_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = re.sub(r"http\S+", "", s)
    s = re.sub(r"@\w+", "", s)
    s = re.sub(r"[^0-9A-Za-z \'\.\,\!\?%:-]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r'(?<=[\.\!\?])\s+', text.strip())
    parts = [p.strip() for p in parts if p.strip()]
    return parts if parts else [text.strip()]

def top_tfidf_terms(docs: List[str], n: int = 10) -> List[str]:
    docs = [d for d in docs if d and len(d.split()) > 0]
    if not docs:
        return []
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=3000)
    X = vec.fit_transform(docs)
    mean_scores = np.asarray(X.mean(axis=0)).ravel()
    top_idx = mean_scores.argsort()[::-1][:n]
    features = np.array(vec.get_feature_names_out())
    return list(features[top_idx])

def grade_percent(percent: float) -> str:
    if percent >= 95:
        return "Overwhelmingly Positive"
    if percent >= 85:
        return "Very Positive"
    if percent >= 70:
        return "Mostly Positive"
    if percent >= 60:
        return "Positive"
    if percent >= 40:
        return "Mixed"
    if percent >= 25:
        return "Mostly Negative"
    if percent >= 10:
        return "Very Negative"
    return "Overwhelmingly Negative"

# Default aspect keyword lists (extend as needed)
DEFAULT_ASPECT_KEYWORDS = {
    "battery": ["battery", "batt", "charge", "charging", "battery life"],
    "screen": ["screen", "display", "resolution", "touchscreen"],
    "camera": ["camera", "photo", "picture", "selfie"],
    "sound": ["sound", "speaker", "audio", "volume", "earphone"],
    "connectivity": ["bluetooth", "wifi", "connection", "connectivity", "usb"],
    "performance": ["speed", "slow", "fast", "lag", "performance", "fps"],
    "design": ["design", "look", "feel", "build", "appearance"],
    "quality": ["quality", "durable", "durability", "material"],
    "price": ["price", "cost", "expensive", "cheap", "value"],
    "customer_service": ["customer service", "support", "warranty", "help"],
    "durability": ["durability", "durable", "break", "crack"]
}

# ------------------------
# Label normalization helpers (robust handling of many HF model label formats)
# ------------------------
def build_label_mapping_from_pipeline_output(example_output: List[Dict[str, float]]) -> Dict[str, str]:
    """
    Given one example of pipeline output (list of dicts with 'label' keys),
    produce mapping label_string -> normalized sentiment ('positive','neutral','negative').
    Strategy:
      - If any label strings contain 'neg'/'pos'/'neu' -> map by substring match.
      - Else if label names are like 'LABEL_0' assume order LABEL_0=negative, LABEL_1=neutral, LABEL_2=positive.
    """
    label_map = {}
    labels = [d['label'] for d in example_output]
    labels_lower = [l.lower() for l in labels]

    # If any labels include readable substrings, map directly
    if any(('neg' in l) or ('pos' in l) or ('neu' in l) for l in labels_lower):
        for l in labels:
            ll = l.lower()
            if 'neg' in ll:
                label_map[l] = 'negative'
            elif 'pos' in ll:
                label_map[l] = 'positive'
            elif 'neu' in ll:
                label_map[l] = 'neutral'
            else:
                # fallback: keep original
                label_map[l] = l
        return label_map

    # fallback: assume LABEL_0=negative, LABEL_1=neutral, LABEL_2=positive (common for 3-class roberta sentiment)
    # If the model has a different number of labels, give them generic names in order
    if all(l.startswith('LABEL_') for l in labels):
        ordinal_to_norm = {}
        # If exactly 3 labels use negative/neutral/positive mapping
        if len(labels) == 3:
            order = ['negative', 'neutral', 'positive']
        else:
            # For other sizes, map center-ish to neutral if size odd
            if len(labels) == 2:
                order = ['negative', 'positive']
            else:
                # generic ordering: assign index-based names
                order = [f'label_{i}' for i in range(len(labels))]
        for idx, l in enumerate(labels):
            if idx < len(order):
                label_map[l] = order[idx]
            else:
                label_map[l] = l
        return label_map

    # Final fallback: return identity mapping
    for l in labels:
        label_map[l] = l
    return label_map

def normalize_pipeline_scores(per_input_scores: List[Dict[str, float]], label_map: Dict[str, str]) -> Dict[str, float]:
    """
    Convert pipeline output list-of-dicts for one input into normalized dict:
      { 'positive': prob, 'neutral': prob, 'negative': prob, ... }
    Uses provided label_map mapping label_string -> normalized token
    """
    out = {}
    for d in per_input_scores:
        lab = d['label']
        score = float(d.get('score', 0.0))
        norm_lab = label_map.get(lab, lab)
        # aggregate if multiple original labels map to same norm_lab
        out[norm_lab] = out.get(norm_lab, 0.0) + score
    # ensure keys for pos/neu/neg present
    for k in ('positive', 'neutral', 'negative'):
        out.setdefault(k, 0.0)
    return out

# ------------------------
# Main analysis function
# ------------------------
def analyze_reviews(
    reviews: List[str],
    model_name: str = "cardiffnlp/twitter-roberta-base-sentiment",
    batch_size: int = 32,
    aspects_keywords: Dict[str, List[str]] = None,
    tfidf_top_n: int = 12,
    use_keybert: bool = False
) -> Dict[str, Any]:
    """
    Single function to analyze reviews:
      - Runs HF pipeline batch sentiment labelling (positive / neutral / negative)
      - Aggregates counts and confidences
      - Splits reviews by sentiment
      - Computes TF-IDF top terms per sentiment
      - Optionally runs KeyBERT on concatenated positive/negative corpora
      - Performs simple keyword-based aspect extraction and per-aspect sentiment aggregation
    Returns a dict with 'overall', 'by_sentiment', 'tfidf_terms', 'keybert_terms' (optional), 'aspects'
    """
    if aspects_keywords is None:
        aspects_keywords = DEFAULT_ASPECT_KEYWORDS

    # prepare reviews
    cleaned = [clean_text(r) for r in reviews]
    if len(cleaned) == 0:
        return {}

    # create HF pipeline (batch inference)
    device = 0 if torch.cuda.is_available() else -1
    print(f"[info] Using model: {model_name}, device: {'cuda' if device==0 else 'cpu'}")
    sentiment_pipe = pipeline("sentiment-analysis", model=model_name, tokenizer=model_name, device=device)

    # 1) Run batch sentiment inference with top_k=None to get per-class probs
    # The returned shape: list per review, each element is list of dicts [{'label':..., 'score':...}, ...]
    hf_outputs = sentiment_pipe(cleaned, batch_size=batch_size, truncation=True, max_length=512, top_k=None)

    # Build label mapping using the first output to handle different label naming conventions
    label_map = build_label_mapping_from_pipeline_output(hf_outputs[0])
    # normalize all outputs into dicts {positive: prob, neutral: prob, negative: prob}
    normalized_probs = [normalize_pipeline_scores(o, label_map) for o in hf_outputs]

    # Decide predicted label per review (argmax of normalized probs), compute top_score
    results_per_review = []
    for text, probs in zip(cleaned, normalized_probs):
        # Ensure probs keys exist
        pos = probs.get('positive', 0.0)
        neu = probs.get('neutral', 0.0)
        neg = probs.get('negative', 0.0)
        # choose label by max
        probs_tuple = {'positive': pos, 'neutral': neu, 'negative': neg}
        pred_label = max(probs_tuple.items(), key=lambda x: x[1])[0]
        top_score = float(probs_tuple[pred_label])
        results_per_review.append({
            'text': text,
            'predicted_label': pred_label,
            'top_score': top_score,
            'all_probs': probs_tuple
        })

    # 2) Aggregate counts and confidences
    counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    sum_conf = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
    for r in results_per_review:
        lab = r['predicted_label']
        counts[lab] += 1
        sum_conf[lab] += r['top_score']

    avg_conf = {}
    total = len(results_per_review)
    for lab in counts:
        avg_conf[lab] = (sum_conf[lab] / counts[lab]) if counts[lab] > 0 else None

    # Lists split by sentiment
    sentiment_buckets = {
        'positive': [r['text'] for r in results_per_review if r['predicted_label'] == 'positive'],
        'neutral':  [r['text'] for r in results_per_review if r['predicted_label'] == 'neutral'],
        'negative': [r['text'] for r in results_per_review if r['predicted_label'] == 'negative']
    }

    # 3) TF-IDF top terms per sentiment (baseline)
    tfidf_terms = {}
    for lab in ('positive', 'neutral', 'negative'):
        tfidf_terms[lab] = top_tfidf_terms(sentiment_buckets[lab], n=tfidf_top_n)

    # 4) Optional: KeyBERT semantic keywords on concatenated corpora
    keybert_terms = {}
    if use_keybert:
        if not KEYBERT_AVAILABLE:
            print("[warn] KeyBERT not installed. Install with: pip install keybert sentence-transformers")
        else:
            try:
                kw_model = KeyBERT(model='all-MiniLM-L6-v2')  # compact & fast embedding model
                for lab in ('positive', 'negative'):
                    docs = sentiment_buckets[lab]
                    if not docs:
                        keybert_terms[lab] = []
                        continue
                    concatenated = " ".join(docs)
                    kws = kw_model.extract_keywords(concatenated,
                                                    top_n=tfidf_top_n,
                                                    keyphrase_ngram_range=(1, 2),
                                                    use_mmr=True,
                                                    stop_words='english')
                    keybert_terms[lab] = [kw for kw, score in kws]
            except Exception as e:
                print("[warn] KeyBERT extraction failed:", e)
                keybert_terms = {}

    # 5) Aspect-level: find sentences that mention each aspect -> classify those sentences -> aggregate
    # Collect sentences mentioning aspects
    aspect_sentences: Dict[str, List[str]] = {a: [] for a in aspects_keywords.keys()}
    aspect_sentence_records: List[Tuple[str, str]] = []  # (aspect, sentence)
    for text in cleaned:
        sents = split_sentences(text)
        sents_lower = [s.lower() for s in sents]
        for aspect, kws in aspects_keywords.items():
            for sent, sent_low in zip(sents, sents_lower):
                for kw in kws:
                    # word boundary check
                    if re.search(r'\b' + re.escape(kw.lower()) + r'\b', sent_low):
                        aspect_sentences[aspect].append(sent)
                        aspect_sentence_records.append((aspect, sent))
                        break

    # Run sentiment classification on aspect sentences in batches (if any)
    aspect_summary = {}
    if aspect_sentence_records:
        sentences_to_classify = [s for (_, s) in aspect_sentence_records]
        # classify sentences; reuse same sentiment_pipe
        sent_outputs = sentiment_pipe(sentences_to_classify, batch_size=batch_size, truncation=True, max_length=512, top_k=None)
        sent_label_map = build_label_mapping_from_pipeline_output(sent_outputs[0])
        sent_normalized = [normalize_pipeline_scores(o, sent_label_map) for o in sent_outputs]
        
        # Better: explicitly map sentences->outputs using list indices
        aspect_to_probs: Dict[str, List[Dict[str, float]]] = {a: [] for a in aspects_keywords.keys()}
        aspect_to_sentences: Dict[str, List[str]] = {a: [] for a in aspects_keywords.keys()}
        for (a, s), prob in zip(aspect_sentence_records, sent_normalized):
            aspect_to_probs[a].append(prob)
            aspect_to_sentences[a].append(s)

        # Now compute stats per aspect
        for a in aspects_keywords.keys():
            probs = aspect_to_probs.get(a, [])
            sents = aspect_to_sentences.get(a, [])
            if not probs:
                aspect_summary[a] = {"count": 0, "positive_pct": None, "category": "No mentions", "top_pos": [], "top_neg": [], "keywords_tfidf": []}
                continue
            # compute discrete labels
            discrete_positive = 0
            pos_scores = []
            for p in probs:
                pos = p.get('positive', 0.0)
                neu = p.get('neutral', 0.0)
                neg = p.get('negative', 0.0)
                maxi_label = max(('positive', pos), ('neutral', neu), ('negative', neg), key=lambda x: x[1])[0]
                # If top probability too low (<0.55) treat as neutral-ish
                top_prob = max(pos, neu, neg)
                if top_prob < 0.55 and maxi_label != 'neutral':
                    maxi_label = 'neutral'
                if maxi_label == 'positive':
                    discrete_positive += 1
                pos_scores.append(pos)
            positive_pct = (discrete_positive / len(probs)) * 100.0
            category = grade_percent(positive_pct)
            # example sentences sorted by positive probability
            sorted_idx = sorted(range(len(pos_scores)), key=lambda i: pos_scores[i], reverse=True)
            top_pos = [sents[i] for i in sorted_idx[:3]]
            top_neg = [sents[i] for i in sorted_idx[-3:]][::-1]
            keywords = top_tfidf_terms(sents, n=8)
            aspect_summary[a] = {
                "count": len(probs),
                "positive_pct": positive_pct,
                "category": category,
                "top_pos": top_pos,
                "top_neg": top_neg,
                "keywords_tfidf": keywords
            }
    else:
        # no aspect sentences
        for a in aspects_keywords.keys():
            aspect_summary[a] = {"count": 0, "positive_pct": None, "category": "No mentions", "top_pos": [], "top_neg": [], "keywords_tfidf": []}

    # Prepare overall summary
    overall_positive_percent = (counts['positive'] / total) * 100.0
    overall_category = grade_percent(overall_positive_percent)

    overall_summary = {
        "total_reviews": total,
        "counts": counts,
        "average_confidence": avg_conf,
        "positive_percent": overall_positive_percent,
        "category": overall_category,
    }

    return {
        "overall": overall_summary,
        "per_review": results_per_review,
        "by_sentiment_buckets": sentiment_buckets,
        "tfidf_terms": tfidf_terms,
        "keybert_terms": keybert_terms,
        "aspects": aspect_summary
    }

# ------------------------
# CLI / Demo runner
# ------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=None, help="CSV file with a column of reviews")
    parser.add_argument("--col", type=str, default="review", help="Column name for reviews in CSV")
    parser.add_argument("--json", type=str, default=None, help="JSON file with review data (JSON Lines format)")
    parser.add_argument("--json_text_field", type=str, default="reviewText", help="Field name for review text in JSON")
    parser.add_argument("--json_rating_field", type=str, default="overall", help="Field name for rating in JSON (optional)")
    parser.add_argument("--max_reviews", type=int, default=None, help="Maximum number of reviews to process from JSON file")
    parser.add_argument("--model", type=str, default="cardiffnlp/twitter-roberta-base-sentiment", help="Hugging Face model for sentiment (3-class recommended)")
    parser.add_argument("--batch", type=int, default=32, help="batch size for HF pipeline")
    parser.add_argument("--use_keybert", action="store_true", help="Run KeyBERT for semantic keywords (optional)")
    args = parser.parse_args()

    if args.csv:
        df = pd.read_csv(args.csv)
        if args.col not in df.columns:
            raise ValueError(f"Column '{args.col}' not found in CSV.")
        reviews = df[args.col].astype(str).tolist()
    elif args.json:
        print(f"[info] Loading reviews from JSON file: {args.json}")
        reviews = []
        try:
            with open(args.json, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    if args.max_reviews and len(reviews) >= args.max_reviews:
                        break
                    try:
                        data = json.loads(line.strip())
                        if args.json_text_field in data:
                            review_text = data[args.json_text_field]
                            if review_text and review_text.strip():
                                reviews.append(review_text)
                        else:
                            print(f"[warn] Line {line_num + 1}: Missing field '{args.json_text_field}'")
                    except json.JSONDecodeError as e:
                        print(f"[warn] Line {line_num + 1}: JSON decode error - {e}")
                    except Exception as e:
                        print(f"[warn] Line {line_num + 1}: Error processing line - {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {args.json}")
        except Exception as e:
            raise Exception(f"Error reading JSON file: {e}")
        
        print(f"[info] Loaded {len(reviews)} valid reviews from JSON file")
        if len(reviews) == 0:
            raise ValueError("No valid reviews found in JSON file")
    else:
        # sample reviews to demo functionality
        reviews = [
            "Battery lasts all day under heavy usage — I'm impressed.",
            "Screen is gorgeous and bright, colors pop.",
            "Camera is terrible in low light; pictures are noisy.",
            "Audio volume is low and speaker cracks at high volume.",
            "Terrible customer service; they never replied to my ticket.",
            "Great value for the price. Very solid build quality.",
            "Bluetooth disconnects randomly, connectivity is a mess.",
            "Device overheats while gaming and becomes slow.",
            "I love the design — sleek and premium feel.",
            "Stopped working after two months. Very disappointed."
        ]

    print(f"[info] Loaded {len(reviews)} reviews. Running analyze_reviews() ...")
    results = analyze_reviews(reviews, model_name=args.model, batch_size=args.batch, use_keybert=args.use_keybert)

    # Print a compact summary
    o = results["overall"]
    print("\n=== OVERALL SUMMARY ===")
    print(f"Total reviews: {o['total_reviews']}")
    print("Counts:", o['counts'])
    print("Avg confidences:", o['average_confidence'])
    print(f"Positive %: {o['positive_percent']:.1f}%  => {o['category']}")

    print("\n=== TOP TF-IDF TERMS (per sentiment) ===")
    for lab, terms in results["tfidf_terms"].items():
        print(f"  {lab.upper():8}: {', '.join(terms[:10]) if terms else '(none)'}")

    if results.get("keybert_terms"):
        print("\n=== KEYBERT TERMS (semantic; may be empty if not installed) ===")
        for lab, kws in results["keybert_terms"].items():
            print(f"  {lab.upper():8}: {', '.join(kws[:10]) if kws else '(none)'}")

    print("\n=== ASPECT SUMMARIES ===")
    for aspect, info in results["aspects"].items():
        print(f"\nAspect: {aspect}")
        if info["count"] == 0:
            print("  No mentions found.")
            continue
        print(f"  Mentions: {info['count']}; Positive%: {info['positive_pct']:.1f} => {info['category']}")
        if info.get("keywords_tfidf"):
            print("  Keywords:", ", ".join(info["keywords_tfidf"]))
        if info.get("top_pos"):
            print("  Example positive sentences:")
            for s in info["top_pos"]:
                print("   -", s)
        if info.get("top_neg"):
            print("  Example negative sentences:")
            for s in info["top_neg"]:
                print("   -", s)

if __name__ == "__main__":
    main()
