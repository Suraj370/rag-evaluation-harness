from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    database_url: str
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333


settings = Settings()
