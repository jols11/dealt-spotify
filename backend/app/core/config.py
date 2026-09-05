from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


def _clean(value: object) -> str:
    text = "" if value is None else str(value)
    return text.strip().strip('"').strip("'")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(Path.cwd() / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8765/api/auth/callback"
    frontend_origin: str = "http://127.0.0.1:4177"
    public_base_url: str = ""
    session_secret: str = "dev-only-change-me"
    database_url: str = "sqlite:///./data/local/listening_graph.db"
    session_gap_minutes: int = Field(default=30, ge=5, le=180)
    cors_origins: str = "http://127.0.0.1:4177,http://localhost:4177,http://127.0.0.1:8765,http://localhost:8765"
    spotify_auth_url: str = "https://accounts.spotify.com/authorize"
    spotify_token_url: str = "https://accounts.spotify.com/api/token"
    spotify_api_base: str = "https://api.spotify.com/v1"
    oauth_scopes: str = "user-read-recently-played user-top-read user-read-private"

    @field_validator(
        "spotify_client_id",
        "spotify_client_secret",
        "spotify_redirect_uri",
        "frontend_origin",
        "public_base_url",
        "session_secret",
        "cors_origins",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, value: object) -> str:
        return _clean(value)

    @property
    def frontend_origin_effective(self) -> str:
        if self.public_base_url:
            return self.public_base_url.rstrip("/")
        return self.frontend_origin.rstrip("/")

    @property
    def redirect_uri_effective(self) -> str:
        if self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/api/auth/callback"
        return self.spotify_redirect_uri

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        extra = self.frontend_origin_effective
        if extra and extra not in origins:
            origins.append(extra)
        return origins

    @property
    def cookie_https_only(self) -> bool:
        return self.frontend_origin_effective.startswith("https://")

    @property
    def catalog_ready(self) -> bool:
        return bool(self.spotify_client_id and self.spotify_client_secret)

    @property
    def spotify_configured(self) -> bool:
        return bool(self.spotify_client_id)

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
