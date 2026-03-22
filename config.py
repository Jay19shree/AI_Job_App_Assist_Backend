import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    # MongoDB
    mongodb_uri: str = ""
    mongodb_db_name: str = "ai_job_assistant"

    # CORS
    allowed_origins: str = "*"

    # Email
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"   # ✅ ignore any extra env vars like MAIL_STARTTLS


@lru_cache
def get_settings() -> Settings:
    return Settings()