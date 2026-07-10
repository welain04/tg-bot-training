import json
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from config.settings import settings
from domain.models.service import Service
from services.ai_prompt_service import AiPromptService
from services.clinic_data_service import ClinicDataService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ServiceRecommendation:
    reply: str
    service_id: str | None
    needs_clarification: bool


class LlmService:
    def __init__(
        self,
        clinic_data: ClinicDataService,
        prompt_service: AiPromptService,
    ) -> None:
        self._clinic_data = clinic_data
        self._prompt_service = prompt_service
        self._client: AsyncOpenAI | None = None

    @property
    def is_configured(self) -> bool:
        return bool(settings.groq_api_key)

    def build_system_prompt(self, services: list[Service] | None = None) -> str:
        active_services = services if services is not None else self._clinic_data.get_services()
        return self._prompt_service.build_system_prompt(active_services)

    async def reply(self, user_message: str, history: list[ChatMessage] | None = None) -> str:
        if not self.is_configured:
            raise RuntimeError("Groq API key is not configured")

        services = self._clinic_data.get_services()
        system_prompt = self.build_system_prompt(services)
        messages = self._build_messages(system_prompt, user_message, history)

        content = await self._create_completion(messages)
        if not content:
            logger.warning("LLM returned empty response")
            return "Извините, не удалось сформировать ответ. Попробуйте переформулировать вопрос."
        return content.strip()

    async def recommend_service(
        self,
        user_message: str,
        services: list[Service],
        history: list[ChatMessage] | None = None,
    ) -> ServiceRecommendation:
        if not self.is_configured:
            raise RuntimeError("Groq API key is not configured")

        system_prompt = self._prompt_service.build_booking_picker_prompt(services)
        messages = self._build_messages(system_prompt, user_message, history)

        content = await self._create_completion(messages, json_mode=True)
        if not content:
            logger.warning("LLM returned empty service recommendation")
            return ServiceRecommendation(
                reply="Извините, не удалось подобрать услугу. Попробуйте описать запрос иначе.",
                service_id=None,
                needs_clarification=True,
            )

        return self._parse_service_recommendation(content, services)

    async def _create_completion(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
    ) -> str | None:
        kwargs: dict = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": settings.groq_temperature,
            "max_tokens": settings.groq_max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        client = self._get_client()
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    @staticmethod
    def _build_messages(
        system_prompt: str,
        user_message: str,
        history: list[ChatMessage] | None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend({"role": item.role, "content": item.content} for item in history)
        messages.append({"role": "user", "content": user_message})
        return messages

    @staticmethod
    def _parse_service_recommendation(raw: str, services: list[Service]) -> ServiceRecommendation:
        fallback = ServiceRecommendation(
            reply="Извините, не удалось разобрать ответ. Попробуйте описать запрос иначе.",
            service_id=None,
            needs_clarification=True,
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON: %s", raw)
            return fallback

        reply = str(data.get("reply", "")).strip()
        if not reply:
            return fallback

        needs_clarification = bool(data.get("needs_clarification", True))
        service_id_raw = data.get("service_id")
        service_id = str(service_id_raw).strip() if service_id_raw else None

        if service_id:
            valid_ids = {service.id for service in services}
            if service_id not in valid_ids:
                logger.warning("LLM returned unknown service_id: %s", service_id)
                return ServiceRecommendation(
                    reply=reply,
                    service_id=None,
                    needs_clarification=True,
                )
            needs_clarification = False

        return ServiceRecommendation(
            reply=reply,
            service_id=service_id,
            needs_clarification=needs_clarification,
        )

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url=settings.groq_base_url,
            )
        return self._client
