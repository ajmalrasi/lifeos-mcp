"""Explicit process configuration; no implicit file or credential discovery."""

import os
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    api_base_url: str = "http://192.168.3.30:8000"
    api_token: SecretStr = SecretStr("")
    request_timeout: float = Field(default=20, ge=1, le=120)
    max_response_bytes: int = Field(default=2_097_152, ge=1024, le=8_388_608)

    @field_validator("api_base_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        url = urlsplit(value)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
        ):
            raise ValueError("Use an HTTP(S) origin without credentials, path, query or fragment")
        try:
            _ = url.port
        except ValueError as exc:
            raise ValueError("Invalid API port") from exc
        return value.rstrip("/")

    @classmethod
    def from_env(cls) -> "Settings":
        # Only documented settings are read; secrets are never discovered implicitly.
        return cls(
            api_base_url=os.environ.get(
                "LIFEOS_API_BASE_URL", cls.model_fields["api_base_url"].default
            ),
            api_token=os.environ.get("LIFEOS_API_TOKEN", ""),
            request_timeout=os.environ.get("LIFEOS_REQUEST_TIMEOUT", "20"),
        )
