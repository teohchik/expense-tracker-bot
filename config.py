"""Bot configuration from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    bot_token: str
    api_base_url: str
    api_key: str
    admin_id: int

    redis_host: str
    redis_port: int

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"



class BotSettings:
    """Bot application constants."""
    CATEGORIES_PER_PAGE: int = 10
    EXPENSES_PER_PAGE: int = 10


settings = Settings()
bot_settings = BotSettings()
