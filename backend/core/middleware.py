import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

def add_middleware(app):
    """Adds all required middleware to the FastAPI app instance."""
    
    class LoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            # Log request details
            print(
                f'INFO:     "{request.method} {request.url.path}" {response.status_code} '
                f'- Processed in {process_time:.2f}ms'
            )
            return response
            
    app.add_middleware(LoggingMiddleware)

    from .config import settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
