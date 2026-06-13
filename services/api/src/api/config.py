"""Runtime configuration for the SmartInv API.

Settings are read from environment variables prefixed with ``SMARTINV_``
or from a ``.env`` file in the working directory.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SMARTINV_",
        extra="ignore",
    )

    environment: Literal["dev", "test", "staging", "prod"] = "dev"
    service_name: str = "smartinv-api"
    version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance."""
    return Settings()
