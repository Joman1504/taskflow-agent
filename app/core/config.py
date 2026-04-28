# app/core/config.py
# Reads .env via pydantic-settings
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-5-mini"
    app_env: str = "development"
    chroma_persist_dir: str = "./chroma_store"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
