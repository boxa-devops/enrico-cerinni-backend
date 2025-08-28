from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://username:password@localhost:5432/enrico_cerrini_dev",
    )

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "your-jwt-secret-key-here")
    jwt_refresh_secret: str = os.getenv(
        "JWT_REFRESH_SECRET", "your-refresh-secret-key-here"
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Server
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")  # development, staging, production

    # CORS
    cors_origin: str = os.getenv(
        "CORS_ORIGIN", "http://localhost:3001,http://localhost:3000,http://localhost:3002"
    )

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    bcrypt_rounds: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Marketing / Notifications
    telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    sms_provider: Optional[str] = os.getenv("SMS_PROVIDER", "")
    sms_api_key: Optional[str] = os.getenv("SMS_API_KEY")
    sms_from_number: Optional[str] = os.getenv("SMS_FROM_NUMBER")
    sms_base_url: Optional[str] = os.getenv("SMS_BASE_URL")

    @property
    def is_production(self) -> bool:
        """Check if we're running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if we're running in development environment."""
        return self.environment.lower() == "development"

    class Config:
        env_file = ".env"


settings = Settings()
