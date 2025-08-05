"""
Configuration settings for GA4 Admin Automation System
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application settings
    APP_NAME: str = "GA4 Admin Automation System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/ga4_admin_dev",
        description="Database connection URL"
    )
    DATABASE_ECHO: bool = False
    
    # Authentication settings
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    
    # Password settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google API settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = None
    
    # Email settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    
    # Email configuration
    EMAIL_FROM: str = "noreply@ga4admin.com"
    EMAIL_FROM_NAME: str = "GA4 Admin System"
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # Feature flags
    ENABLE_REGISTRATION: bool = True
    ENABLE_PASSWORD_RESET: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    
    # AI and ML settings
    MODELS_DIR: str = "models"
    AI_CACHE_TTL: int = 3600  # 1 hour
    ML_MODEL_REFRESH_INTERVAL: int = 86400  # 24 hours
    
    # AI Model settings
    ANOMALY_DETECTION_THRESHOLD: float = 2.5
    TREND_PREDICTION_MIN_DAYS: int = 7
    AI_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Redis settings for AI caching
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_AI_CACHE_TTL: int = 1800  # 30 minutes
    
    # Natural Language Processing
    NLP_MODEL_NAME: str = "en_core_web_sm"  # spaCy model
    MAX_QUERY_LENGTH: int = 500
    
    # Performance settings
    AI_WORKER_THREADS: int = 4
    ML_BATCH_SIZE: int = 100
    
    # Feature flags for AI
    ENABLE_AI_INSIGHTS: bool = True
    ENABLE_NATURAL_LANGUAGE_QUERY: bool = True
    ENABLE_ANOMALY_DETECTION: bool = True
    ENABLE_TREND_PREDICTION: bool = True
    ENABLE_ML_MODEL_TRAINING: bool = False  # Disabled by default for security
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic"""
        return self.DATABASE_URL.replace("+asyncpg", "")


# Global settings instance
settings = Settings()