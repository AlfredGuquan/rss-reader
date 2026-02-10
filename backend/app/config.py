from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./rss_reader.db"
    default_user_id: str = "00000000-0000-0000-0000-000000000001"
    default_username: str = "default"
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_prefix = "RSS_"


settings = Settings()
