#!/usr/bin/env python3
"""Thin CLI wrapper delegating to heavy analysis module.

Original large implementation moved to `analysis.heavy.review_analyzer`.
This script now:
 - Loads reviews from CSV
 - Runs heavy transformer-based analysis (optionally keyword mode)
 - Writes per-review & category CSV plus meta JSON (no plots to keep lean)
"""
import argparse, json
from pathlib import Path
import pandas as pd
from analysis.heavy.review_analyzer import run_heavy_analysis

def generate_sample_csv(path: Path):
    sample_reviews = [
        {"review_text": "Battery life is amazing — lasted two days. The screen is bright and crisp. Camera is okay but not great."},
        {"review_text": "Terrible customer service. The phone froze a lot. Shipping was delayed by a week."},
        {"review_text": "Excellent performance, snappy UI and great design. Price is a bit high but worth it."},
        {"review_text": "Battery drains fast when gaming. Overheats sometimes."},
        {"review_text": "Good value for money. Camera is excellent, photos are sharp."},
        {"review_text": "I love the design but screen cracked easily. Customer service helped replace it quickly."},
    ]
    pd.DataFrame(sample_reviews).to_csv(path, index=False)

def main():
    p = argparse.ArgumentParser("Heavy review analyzer (transformer-based)")
    p.add_argument('--input', '-i', default='sample_reviews.csv')
    p.add_argument('--outdir', '-o', default='results')
    p.add_argument('--aspects', default='battery,screen,camera,performance,price,design,customer service,shipping')
    p.add_argument('--aspect_method', choices=['zsc','keywords'], default='zsc')
    p.add_argument('--zsc_model', default='facebook/bart-large-mnli')
    p.add_argument('--sent_model', default='cardiffnlp/twitter-roberta-base-sentiment')
    p.add_argument('--zsc_threshold', type=float, default=0.35)
    p.add_argument('--zsc_batch_size', type=int, default=4)
    p.add_argument('--sent_batch_size', type=int, default=16)
    p.add_argument('--no_cache', action='store_true')
    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        generate_sample_csv(in_path)
    df = pd.read_csv(in_path)
    if 'review_text' not in df.columns:
        raise SystemExit('CSV must contain review_text column')
    reviews = df['review_text'].astype(str).tolist()
    aspects = [a.strip() for a in args.aspects.split(',') if a.strip()]

    result = run_heavy_analysis(
        reviews,
        aspects=aspects,
        aspect_method=args.aspect_method,
        zsc_model_name=args.zsc_model,
        sentiment_model_name=args.sent_model,
        zsc_threshold=args.zsc_threshold,
        zsc_batch_size=args.zsc_batch_size,
        sent_batch_size=args.sent_batch_size,
        cache_sentiment=not args.no_cache,
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # Persist minimal artifacts
    with open(outdir/'analysis_result.json','w',encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
    print(f'Saved JSON to {outdir/"analysis_result.json"}')

if __name__ == '__main__':
    main()
