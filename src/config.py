"""Application configuration management."""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Always prefer this repository's .env values over inherited shell/user variables.
load_dotenv(dotenv_path=ENV_FILE, override=True)


class Config:
    """Base configuration."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "24"))
    )

    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "sqlite:///pos_system.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Pagination
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Paystack
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    PAYSTACK_CURRENCY: str = os.getenv("PAYSTACK_CURRENCY", "NGN")
    PAYSTACK_BASE_URL: str = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
    PAYSTACK_CALLBACK_URL: str = os.getenv("PAYSTACK_CALLBACK_URL", "")
    PAYSTACK_CHECKOUT_TOKEN_MAX_AGE: int = int(os.getenv("PAYSTACK_CHECKOUT_TOKEN_MAX_AGE", "900"))


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=5)


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG: bool = False


# Map environment names to config objects
config_map: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> Config:
    """Return the appropriate config object based on the ENV environment variable."""
    env = os.getenv("ENV", "default")
    return config_map.get(env, DevelopmentConfig)()
