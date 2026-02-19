"""
Core configuration settings for the application
Uses Pydantic Settings for environment variable management
"""
from pydantic_settings import BaseSettings
from typing import Optional
import sys


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "Club Management SaaS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/club_management"
    
    # Security - CHANGE THESE IN PRODUCTION!
    SECRET_KEY: str = "CHANGE-THIS-IN-PRODUCTION-USE-openssl-rand-base64-32"  # MUST be changed!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password hashing
    BCRYPT_ROUNDS: int = 12
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Redis (for caching and rate limiting)
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # File uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Email (for future implementation)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True
    FEE_GENERATION_HOUR: int = 0  # Hour of day to generate fees (0-23)
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate security settings in production
        if not self.DEBUG:
            if "CHANGE-THIS" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                print("\n" + "="*70)
                print("🚨 CRITICAL SECURITY ERROR 🚨")
                print("="*70)
                print("SECRET_KEY is using the default insecure value!")
                print("This is NOT allowed in production (DEBUG=False).")
                print("\nTo fix this:")
                print("1. Generate a secure key: openssl rand -base64 32")
                print("2. Set environment variable: SECRET_KEY=<generated-key>")
                print("="*70 + "\n")
                sys.exit(1)
            
            if "password" in self.DATABASE_URL.lower() or "user" in self.DATABASE_URL:
                print("\n" + "="*70)
                print("🚨 DATABASE CONFIGURATION ERROR 🚨")
                print("="*70)
                print("DATABASE_URL appears to use default placeholder values!")
                print("Please set a proper DATABASE_URL environment variable.")
                print("="*70 + "\n")
                sys.exit(1)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
