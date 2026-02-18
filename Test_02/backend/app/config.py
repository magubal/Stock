from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Stock Research ONE"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/stock_research"
    DATABASE_POOL_SIZE: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DART_API_KEY: Optional[str] = None
    FRED_API_KEY: Optional[str] = None
    
    # Scraping
    USER_AGENT: str = "Stock-Research-ONE/1.0"
    REQUEST_DELAY: float = 1.0
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Ignore unrelated keys in .env (e.g., ORACLE_* for research scripts).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
