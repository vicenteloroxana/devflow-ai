# shared/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str
    anthropic_api_key: str = ""
    postgres_url: str = ""
    github_token: str = ""
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()