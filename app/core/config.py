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
    GW2_API_KEY: str
    FRONTEND_URL: str
    WORLDS_CRAWLER_INTERVAL_MINUTES: int = 2880  # 48 hours
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8")


settings = Settings()
