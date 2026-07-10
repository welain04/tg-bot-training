from pydantic import field_validator
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

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.3
    groq_max_tokens: int = 300
    groq_base_url: str = "https://api.groq.com/openai/v1"

    @field_validator("groq_api_key", mode="before")
    @classmethod
    def strip_groq_api_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None


settings = Settings()
