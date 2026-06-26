from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    APP_TITLE: str = "ai-agent-platform"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"

    AUDIO_STORAGE_DIR: str = "audio_files"
    MAX_AUDIO_FILE_SIZE: int = 10 * 1024 * 1024


settings = Settings()  # ty: ignore[missing-argument]
