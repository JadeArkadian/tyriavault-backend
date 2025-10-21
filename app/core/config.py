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
    CACHE_TTL_SECONDS: int = 300  # 5 minutes
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8")


settings = Settings()
