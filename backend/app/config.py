from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Orquestador Multi-Agente"
    app_env: str = "dev"

    contact_email: Optional[str] = Field(default=None, validation_alias="CONTACT_EMAIL")
    use_mock_apis: bool = Field(default=True, validation_alias="USE_MOCK_APIS")

    postgres_user: str = Field(default="arquitecto", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="super_password_secreta_123", validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="orquestador_db", validation_alias="POSTGRES_DB")
    postgres_host: str = Field(default="db", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")

    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")

    base_projects_dir: Path = Field(
        default=Path("/home/vitoto/email@victorfigueroa.cl"),
        validation_alias="BASE_PROJECTS_DIR",
    )

    backend_cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="BACKEND_CORS_ORIGINS",
    )

    default_usuario_config_id: int = Field(default=1, validation_alias="DEFAULT_USUARIO_CONFIG_ID")
    max_agent_steps: int = Field(default=8, validation_alias="MAX_AGENT_STEPS")
    max_tool_calls: int = Field(default=5, validation_alias="MAX_TOOL_CALLS")
    stream_char_delay_seconds: float = Field(default=0.005, validation_alias="STREAM_CHAR_DELAY_SECONDS")
    db_inline_max_bytes: int = Field(default=262_144, validation_alias="DB_INLINE_MAX_BYTES")

    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    github_personal_access_token: Optional[str] = Field(default=None, validation_alias="GITHUB_PERSONAL_ACCESS_TOKEN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins(self) -> List[str]:
        return [x.strip() for x in self.backend_cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.base_projects_dir.mkdir(parents=True, exist_ok=True)
    return settings
