from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Enterprise Workflow API"
    environment: Literal["local", "test", "staging", "production"] = "local"
    public_base_url: str = ""  # e.g. https://api.example.com — optional, for webhooks / links
    api_prefix: str = "/api"
    secret_key: str = Field(
        default="dev-secret-change-in-production",
        min_length=16,
        description="JWT signing; must be a long random value in production.",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    frontend_url: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg2://workflow:workflow@localhost:5432/workflow"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    upload_dir: str = "./data/uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    allowed_upload_extensions: str = ".pdf,.png,.jpg,.jpeg,.gif,.txt,.md,.csv"
    # S3: leave bucket empty to use local disk only. Use IAM role on EC2; or set keys.
    s3_bucket: str = ""
    s3_prefix: str = "attachments"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_endpoint_url: str = ""  # set for MinIO, DigitalOcean Spaces, etc.

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = "noreply@example.com"

    rate_limit_per_minute: int = 120

    @computed_field
    @property
    def allowed_extensions_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_upload_extensions.split(",") if e.strip()}

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_test_db(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("sqlite"):
            return v
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
