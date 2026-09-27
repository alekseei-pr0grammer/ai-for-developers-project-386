from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables (or backend/.env in dev)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://calendar:calendar@localhost:5432/calendar"
    # Origins allowed to call the API from a browser, comma-separated.
    # Only needed when the frontend is served from a different origin (e.g. a CDN).
    cors_origins: Annotated[list[str], NoDecode] = []
    # Send the Host's session cookie only over HTTPS. Turn off for plain-HTTP local setups.
    session_cookie_secure: bool = True
    session_lifetime_days: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
