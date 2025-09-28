from fastapi import FastAPI
from api import endpoints
from core.errors import JobNotFound, job_not_found_handler
from core.middleware import add_middleware

app = FastAPI(
    title="Review Radar API",
    description="API for analyzing e-commerce product reviews. Scraping is now done in the browser extension.",
    version="0.2.0"  # bumped version
)

# --- Middleware ---
add_middleware(app)

# --- Custom Exception Handlers ---
app.add_exception_handler(JobNotFound, job_not_found_handler)

# --- API Routes ---
app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Welcome to Review Radar API. Send review texts to /api/v1/analyze"}
