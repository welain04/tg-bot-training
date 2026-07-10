import asyncio
from functools import lru_cache

from config.settings import settings
from integrations.google_sheets import GoogleSheetsClient, build_credentials
from services.ai_prompt_service import AiPromptService
from services.booking_service import BookingService
from services.clinic_data_service import ClinicDataService
from services.llm_service import LlmService


@lru_cache
def get_sheets_client() -> GoogleSheetsClient:
    credentials = build_credentials(
        credentials_path=settings.google_credentials_path,
        credentials_json=settings.google_credentials_json,
    )
    return GoogleSheetsClient(credentials, settings.google_sheets_id)


@lru_cache
def get_clinic_data_service() -> ClinicDataService:
    return ClinicDataService(get_sheets_client())


@lru_cache
def get_schedule_service() -> "ScheduleService":
    from services.schedule_service import ScheduleService

    return ScheduleService(get_sheets_client(), get_clinic_data_service())


@lru_cache
def get_booking_service() -> BookingService:
    return BookingService(get_sheets_client())


@lru_cache
def get_ai_prompt_service() -> AiPromptService:
    return AiPromptService()


@lru_cache
def get_llm_service() -> LlmService:
    return LlmService(get_clinic_data_service(), get_ai_prompt_service())


def build_ai_system_prompt() -> str:
    clinic_data = get_clinic_data_service()
    prompt_service = get_ai_prompt_service()
    return prompt_service.build_system_prompt(clinic_data.get_services())


async def run_sync(func, /, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)
