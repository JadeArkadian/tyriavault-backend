import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = ".env"
if os.getenv("ENV") == "test":
    env_file = ".env.test"

load_dotenv()


class Settings(BaseSettings):
    """
    Configuration settings for the TyriaVault Backend application.

    """

    ## TODO: get these from pyproject.toml
    PROJECT_NAME: str = "TyriaVault Backend ⚔️"
    PROJECT_VERSION: str = "0.1.0"
    DATABASE_URL: str
    FRONTEND_URL: str
    GW2_API_BASE_URL: str = "https://api.guildwars2.com/v2"
    CACHE_TTL_STATIC_SECONDS: int = 2592000  # 30 days
    CACHE_TTL_NORMAL_SECONDS: int = 300  # 5 minutes
    LOG_LEVEL: str = "INFO"
    ITEMS_CRAWLER_INTERVAL_SECONDS: int = 24 * 60 * 60
    ITEMS_CRAWLER_FETCH_EXPIRATION_SECONDS: int = 30 * 24 * 60 * 60  # 30 days

    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8")


settings = Settings()
