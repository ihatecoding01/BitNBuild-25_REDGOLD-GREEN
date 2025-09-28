import os
from pydantic_settings import BaseSettings 
from typing import List


from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.
    """
    PORT: int = int(os.getenv("PORT", 8000))
    
    
    CORS_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(',') if origin
    ] + [
        "chrome-extension://*", 
    ]

    
    MAX_REVIEWS_DEFAULT: int = int(os.getenv("MAX_REVIEWS_DEFAULT", 500))
    MAX_REVIEWS_LIMIT: int = int(os.getenv("MAX_REVIEWS_LIMIT", 2000))
    SCRAPE_TIMEOUT_SECONDS: int = int(os.getenv("SCRAPE_TIMEOUT_SECONDS", 60))

    
    ENABLE_API_KEY: bool = os.getenv("ENABLE_API_KEY", "false").lower() == "true"
    API_KEY: str = os.getenv("API_KEY", "default-secret-key")

    class Config:
        case_sensitive = True


settings = Settings()
