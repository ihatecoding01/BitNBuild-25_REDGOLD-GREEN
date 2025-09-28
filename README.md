# Review Radar – Unified Heavy Sentiment & Aspect Analysis with Scraping

## What It Does
Scrapes product review pages (Amazon / Flipkart) and performs transformer-based aspect & sentiment analysis. Provides:
1. Playwright async scraper (`scraper.py`).
2. Heavy analyzer (`analysis/review_analysis.py`) using zero-shot classification + sentiment (HuggingFace pipelines).
3. FastAPI backend exposing async scrape+analyze jobs and direct analysis endpoints.
4. CLI for CSV batch analysis.

## Tech Stack
FastAPI, Transformers, Playwright, Pydantic v2, Uvicorn, Python 3.13.

## Directory Overview
```
analysis/review_analysis.py          # Heavy analyzer
backend/main.py                      # FastAPI entrypoint
backend/api/endpoints.py             # REST endpoints
backend/adapters/nlp.py              # Analyzer adapter
backend/adapters/scraper.py          # Re-exports root scraper
backend/jobs/manager.py              # Background job orchestration
scraper.py                           # Playwright scraper
SentimentAnalyser/review_sentiment_analyser.py  # CLI
requirements.txt                     # Single global dependencies
```

## Install & Setup
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu   # choose CUDA variant if needed
playwright install chromium
```
First model run downloads: `facebook/bart-large-mnli` (zero-shot) and `cardiffnlp/twitter-roberta-base-sentiment`.

## Run the API
```powershell
uvicorn backend.main:app --port 8001 --reload
```
Swagger UI: http://127.0.0.1:8001/docs

### Async Job Flow
1. POST `/api/v1/analyze` body:
```json
{ "url": "https://www.amazon.in/dp/ASIN_CODE", "max_reviews": 40 }
```
2. Poll `/api/v1/status/{job_id}` until `status` = `done`.
3. GET `/api/v1/results/{job_id}` for final analysis.

### Direct Analysis Endpoints
POST `/api/v1/analyze/reviews`:
```json
{ "reviews": ["Great battery life", "Terrible camera"], "aspect_method": "keywords" }
```
POST `/api/v1/analyze/text`:
```json
{ "text": "Battery is great. Camera is bad.", "splitter": "sentence" }
```

### Output Example
```json
{
  "sentiment": {"positive": 0.55, "neutral": 0.30, "negative": 0.15},
  "counts": {"positive": 11, "neutral": 6, "negative": 3},
  "n_reviews": 20,
  "categories": [
    {"category": "battery", "n_reviews": 12, "mean_score": 0.34, "rating_stars": 4.36}
  ],
  "mode": "heavy"
}
```

## Analyzer Details
- `aspect_method="zsc"` uses zero-shot model (BART MNLI) with threshold (default 0.35).
- `aspect_method="keywords"` simple substring match of aspect labels.
- Sentiment model: `cardiffnlp/twitter-roberta-base-sentiment`.
- Category mean converted to stars (1–5) via linear mapping of [-1,1].

## CLI Usage
```powershell
python SentimentAnalyser/review_sentiment_analyser.py --input sample_reviews.csv --aspect_method zsc --outdir results
```
Generates `analysis_result.json` in the output directory.

## Scraper Standalone Test
```powershell
python -c "import asyncio, scraper; print(asyncio.run(scraper.scrape_reviews('https://www.amazon.in/dp/ASIN_CODE', 5)))"
```
First run opens non-headless browser for login; session stored under `playwright_user_data/`.

## Troubleshooting
| Problem | Cause | Fix |
|---------|-------|-----|
| ImportError: transformers | Dependencies missing | `pip install -r requirements.txt` |
| Torch not installed | Torch intentionally unpinned | Install CPU/CUDA torch manually |
| Slow first call | Model downloads | Allow initial warm download; then cached |
| Empty output categories | Threshold too strict / no keyword matches | Lower `zsc_threshold` or use `keywords` |
| Scraper fails container detection | Selector drift | Update selectors in `scraper.py` |

## Roadmap
- Persist job store (Redis/DB)
- Caching layer for zero-shot & sentiment
- Configurable aspect sets per request
- Add unit/integration tests
- Dockerfile & CI workflow

## License
Internal / TBD
