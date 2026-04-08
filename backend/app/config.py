from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sponsorship Platform API"
    app_env: str = "dev"
    database_url: str = (
        "postgresql+psycopg://sponsorship:sponsorship@localhost:5432/sponsorship"
    )
    # Comma-separated origins; browser app may run on 3000 (local) or 3001 (Docker).
    frontend_origins: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:5000"
    )
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v


settings = Settings()
