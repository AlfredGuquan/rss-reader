from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./rss_reader.db"
    default_user_id: str = "00000000-0000-0000-0000-000000000001"
    default_username: str = "default"
    cors_origins: list[str] = ["http://localhost:5173"]
    google_oauth_credentials_path: str = "config/google_oauth_credentials.json"
    google_oauth_redirect_uri: str = "http://localhost:5173/oauth/callback"
    reddit_user_agent: str = "RSS-Reader:v1.0 (by /u/rss-reader-app)"

    class Config:
        env_prefix = "RSS_"


settings = Settings()
