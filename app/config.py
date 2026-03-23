from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class DatabaseConfig(BaseModel):
    database_url: str = "postgresql://username:password@localhost:5432/enrico_cerrini_dev"

    @property
    def sync_database_url(self) -> str:
        """Normalize DATABASE_URL for SQLAlchemy psycopg2 driver."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


class JwtConfig(BaseModel):
    jwt_secret: str = "your-jwt-secret-key-here"
    jwt_refresh_secret: str = "your-refresh-secret-key-here"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class ServerConfig(BaseModel):
    port: int = 8000
    host: str = "0.0.0.0"
    debug: bool = True
    environment: str = "development"  # development, staging, production

    @property
    def is_production(self) -> bool:
        """Check if we're running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if we're running in development environment."""
        return self.environment.lower() == "development"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() == "true"
        return v


class SecurityConfig(BaseModel):
    secret_key: str = "your-secret-key-here"
    bcrypt_rounds: int = 12


class RateLimitConfig(BaseModel):
    rate_limit_per_minute: int = 60


class NotificationConfig(BaseModel):
    telegram_bot_token: Optional[str] = None
    sms_provider: Optional[str] = ""
    sms_api_key: Optional[str] = None
    sms_from_number: Optional[str] = None
    sms_base_url: Optional[str] = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        extra="ignore",
    )

    database: DatabaseConfig = DatabaseConfig()
    jwt: JwtConfig = JwtConfig()
    server: ServerConfig = ServerConfig()
    security: SecurityConfig = SecurityConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()
    notification: NotificationConfig = NotificationConfig()


settings = Settings()