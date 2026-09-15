from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: SecretStr = SecretStr("mongodb://localhost:27017/?replicaSet=rs0")
    mongodb_database: str = Field(default="fuuud", pattern=r"^[A-Za-z0-9_-]+$")
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"
    public_app_url: str = "http://localhost:3000"
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_security: Literal["starttls", "ssl"] = "starttls"
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    mail_from: EmailStr = "noreply@example.com"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    def validate_security(self) -> None:
        if self.environment.lower() != "development" and len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be at least 32 characters outside development.")

    def validate_mail(self) -> None:
        self.validate_security()
        if not self.smtp_host:
            raise RuntimeError("SMTP_HOST is required to run the email worker.")
        if bool(self.smtp_username) != bool(self.smtp_password.get_secret_value()):
            raise RuntimeError("Set both SMTP_USERNAME and SMTP_PASSWORD.")
        url = urlsplit(self.public_app_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
        ):
            raise RuntimeError("PUBLIC_APP_URL must be the application's public origin.")
        if self.environment.lower() != "development" and url.scheme != "https":
            raise RuntimeError("PUBLIC_APP_URL must use HTTPS outside development.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
