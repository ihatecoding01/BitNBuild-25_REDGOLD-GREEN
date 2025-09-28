from fastapi import FastAPI
from .api import endpoints
from .core.errors import JobNotFound, job_not_found_handler
from .core.middleware import add_middleware

# --- App Initialization ---
app = FastAPI(
    title="Review Radar API",
    description="API for scraping and analyzing e-commerce product reviews.",
    version="0.1.0"
)

# --- Add Middleware ---
# Important: This function call adds CORS and logging middleware.
add_middleware(app)

# --- Add Exception Handlers ---
# This maps our custom JobNotFound exception to a 404 response.
app.add_exception_handler(JobNotFound, job_not_found_handler)

# --- Include API Routers ---
# This includes all the endpoints defined in api/endpoints.py.
app.include_router(endpoints.router, prefix="/api/v1")

# --- Root Endpoint ---
@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Welcome to Review Radar API. See /docs for details."}
