from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    resume_analyzer_base_url: str = "http://resume-analyzer-dev:8080"
    coding_analyzer_base_url: str = "http://coding-analyzer-dev:8080"
    marksheet_analyzer_base_url: str = "http://marksheet-analyzer-dev:8080"
    resume_http_timeout_s: float = 120.0
    coding_http_timeout_s: float = 180.0
    marksheet_http_timeout_s: float = 120.0

    @property
    def resume_base(self) -> str:
        return self.resume_analyzer_base_url.rstrip("/")

    @property
    def coding_base(self) -> str:
        return self.coding_analyzer_base_url.rstrip("/")

    @property
    def marksheet_base(self) -> str:
        return self.marksheet_analyzer_base_url.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
