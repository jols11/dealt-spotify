from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8765/api/auth/callback"
    frontend_origin: str = "http://127.0.0.1:4177"
    session_secret: str = "dev-only-change-me"
    database_url: str = "sqlite:///./data/local/listening_graph.db"
    session_gap_minutes: int = Field(default=30, ge=5, le=180)
    cors_origins: str = "http://127.0.0.1:4177,http://localhost:4177"
    spotify_auth_url: str = "https://accounts.spotify.com/authorize"
    spotify_token_url: str = "https://accounts.spotify.com/api/token"
    spotify_api_base: str = "https://api.spotify.com/v1"
    oauth_scopes: str = "user-read-recently-played user-top-read user-read-private"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        url = self.database_url
        if url.startswith("sqlite:///./"):
            relative = url.removeprefix("sqlite:///./")
            return f"sqlite:///{(ROOT_DIR / relative).resolve()}"
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
