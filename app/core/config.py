"""
Application configuration settings
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Meta/Facebook Configuration
    META_ACCESS_TOKEN: str = ""
    
    # Cache Configuration
    CACHE_TTL: int = 3600  # 1 hour
    REDIS_URL: str = ""
    
    # HTTP Client Configuration
    HTTP_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
