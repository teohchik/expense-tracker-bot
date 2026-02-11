"""Bot configuration from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    bot_token: str
    api_base_url: str
    api_key: str
    admin_id: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
