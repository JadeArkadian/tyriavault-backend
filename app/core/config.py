from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    """
    Configuration settings for the TyriaVault Backend application.

    """

    ## TODO: get these from pyproject.toml
    PROJECT_NAME:str = "TyriaVault Backend ⚔️"
    PROJECT_VERSION: str = "0.1.0"
    DATABASE_URL: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()