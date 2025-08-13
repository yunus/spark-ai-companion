import os
from typing import Literal

from google.adk.cli.utils.common import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import (
    PostgresDsn,
)
from functools import lru_cache
from dotenv import load_dotenv

env_path = os.getenv("ENV_PATH")
load_dotenv(dotenv_path=env_path)


class AgentTools(BaseModel):
    vertex_ai_data_store_id: str | None = None
    vertex_ai_data_store_enabled: bool = False


class AgentModels(BaseModel):
    root: str = "gemini-2.5-flash"
    ui_analyzer: str = "gemini-2.5-flash"
    code_analyzer: str = "gemini-2.5-flash"
    case_matcher: str = "gemini-2.5-flash"


class Settings(BaseSettings):

    debug: bool = False
    log_level: Literal["INFO", "ERROR"] = "INFO"
    log_format: Literal["console", "json"] = "console"
    log_use_colors: bool = True

    app_title: str = "Spark Companion"
    app_description: str = "Spark Companion"
    app_api_version: str = "v0"
    app_project_name: str = "Spark Companion"

    postgres_dsn: PostgresDsn = (
        "postgresql+psycopg://user:password@localhost:5432/spark-companion"
    )

    firebase_credentials_path: str = "path/to/firebase-service-account.json"

    agent_models: AgentModels = AgentModels()
    agent_tools: AgentTools = AgentTools()

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return str(self.postgres_dsn)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
