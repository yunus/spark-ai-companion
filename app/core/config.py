import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import (
    PostgresDsn,
)
from functools import lru_cache
from dotenv import load_dotenv

env_path = os.getenv("ENV_PATH")
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):

    debug: bool = False
    log_level: str = "INFO"

    app_title: str = "Spark Companion"
    app_description: str = "Spark Companion"
    app_api_version: str = "v0"
    app_project_name: str = "Spark Companion"

    postgres_dsn: PostgresDsn = "postgresql+psycopg://user:password@localhost:5432/spark-companion"

    firebase_credentials_path: str = "path/to/firebase-service-account.json"

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return str(self.postgres_dsn)

    model_config = SettingsConfigDict(
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
