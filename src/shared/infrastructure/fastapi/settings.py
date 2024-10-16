from typing import Optional
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: Optional[str] = None
    app_version: str
    description: Optional[str] = None
    admin_email: str
    DYNAMODB_URL: Optional[str] = None
    TABLE_NAME: str
    allowed_origins: str
    APP_ENVIRONMENT: str
    API_PATH_VERSION_PREFIX: str
    AWS_DEFAULT_REGION: Optional[str]
    AWS_USERPOOLID: Optional[str]
    AWS_USERPOOLWEBCLIENTID: Optional[str]
    AWS_ACCESS_KEY_ID: Optional[str]
    AWS_SECRET_ACCESS_KEY: Optional[str]

    model_config = SettingsConfigDict(
        env_file=".env.dev" if Path(".env.dev").exists() else ".env")
