from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str
    admin_chat_id: int
    google_sheets_id: str
    google_credentials_path: str = "credentials/google_service_account.json"
    google_credentials_json: str | None = None
    timezone: str = "Europe/Moscow"

    clinic_name: str = "Стоматологическая клиника"
    clinic_about: str = (
        "Мы оказываем полный спектр стоматологических услуг: "
        "консультации, лечение, профессиональную гигиену и хирургию."
    )
    clinic_address: str = "уточняйте у администратора"
    clinic_phone: str = "уточняйте у администратора"
    clinic_hours: str = "Пн–Сб, по предварительной записи"

    fsm_timeout_minutes: int = 30
    callback_throttle_seconds: float = 0.4
    log_level: str = "INFO"
    redis_url: str | None = None


settings = Settings()
