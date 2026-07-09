from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    admin_chat_id: int
    google_sheets_id: str
    google_credentials_path: str = "credentials/google_service_account.json"
    google_credentials_json: str | None = None
    timezone: str = "Europe/Moscow"

    fsm_timeout_minutes: int = 30
    callback_throttle_seconds: float = 0.4
    log_level: str = "INFO"
    redis_url: str | None = None


settings = Settings()
