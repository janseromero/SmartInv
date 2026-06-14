"""Runtime configuration for the SmartInv API.

Settings are read from environment variables prefixed with ``SMARTINV_``
or from a ``.env`` file in the working directory. Langfuse keys are the one
exception: they use the SDK's conventional unprefixed ``LANGFUSE_*`` names.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
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

    # --- Data platform (CV1.E4 / ADR-004, ADR-017) ---
    database_url: str = "postgresql://smartinv:smartinv@localhost:5432/smartinv"
    redis_url: str = "redis://localhost:6379/0"

    # Object store: SeaweedFS S3-compatible (ADR-017). Dev defaults only —
    # never real credentials.
    s3_endpoint_url: str = "http://localhost:8333"
    s3_access_key: str = "smartinv"
    s3_secret_key: str = "smartinvsecret"  # noqa: S105 — dev default, not a secret
    s3_region: str = "us-east-1"
    s3_bucket: str = "smartinv-local"

    # --- LLM observability: Langfuse Cloud (CV1.E4 / ADR-018) ---
    # Configuration only; the LLM gateway wires these into the SDK in CV5.E1.
    # Read from the unprefixed LANGFUSE_* names the Langfuse SDK expects.
    langfuse_public_key: str = Field(default="", validation_alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", validation_alias="LANGFUSE_SECRET_KEY")
    langfuse_base_url: str = Field(
        default="https://us.cloud.langfuse.com",
        validation_alias="LANGFUSE_BASE_URL",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance."""
    return Settings()
