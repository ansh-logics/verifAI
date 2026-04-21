from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    resume_analyzer_base_url: str = "http://resume-analyzer-dev:8080"
    coding_analyzer_base_url: str = "http://coding-analyzer-dev:8080"
    marksheet_analyzer_base_url: str = "http://marksheet-analyzer-dev:8080"
    jd_analyzer_base_url: str = "http://jd-analyzer-dev:8080"
    resume_http_timeout_s: float = 120.0
    coding_http_timeout_s: float = 180.0
    marksheet_http_timeout_s: float = 120.0
    jd_http_timeout_s: float = 120.0
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/verifai"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo_sql: bool = False
    log_level: str = "INFO"
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    cloudinary_resume_folder: str = "verifAI/resumes"
    auth_jwt_secret: str = "change-me-master-service-jwt-secret"
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 120
    tpo_username: str = "tpo"
    tpo_password: str = "tpo12345"
    tpo_access_token_expire_minutes: int = 240
    tpo_allow_api_key_fallback: bool = True
    tpo_api_key: str = "default-insecure-tpo-key"
    cors_allowed_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:18084,http://127.0.0.1:18084,"
        "http://localhost:28084,http://127.0.0.1:28084"
    )
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "VerifAI TPO"

    @property
    def resume_base(self) -> str:
        return self.resume_analyzer_base_url.rstrip("/")

    @property
    def coding_base(self) -> str:
        return self.coding_analyzer_base_url.rstrip("/")

    @property
    def marksheet_base(self) -> str:
        return self.marksheet_analyzer_base_url.rstrip("/")

    @property
    def jd_base(self) -> str:
        return self.jd_analyzer_base_url.rstrip("/")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
