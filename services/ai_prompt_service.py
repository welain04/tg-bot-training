from config.ai_prompt_templates import ai_prompt_templates
from config.clinic_texts import clinic_texts
from domain.models.service import Service


class AiPromptService:
    def build_system_prompt(self, services: list[Service]) -> str:
        if not services:
            return self._build_empty_services_prompt()

        services_list = "\n".join(
            f"{index}. {service.name}" for index, service in enumerate(services, start=1)
        )
        return ai_prompt_templates.system_prompt.format(
            clinic_name=clinic_texts.name,
            clinic_phone=clinic_texts.phone,
            services_list=services_list,
            services_count=len(services),
        )

    def build_booking_picker_prompt(self, services: list[Service]) -> str:
        base_prompt = self.build_system_prompt(services)
        if not services:
            return base_prompt

        services_with_ids = "\n".join(
            f'- id: "{service.id}", название: {service.name}' for service in services
        )
        booking_part = ai_prompt_templates.booking_picker_append.format(
            services_with_ids=services_with_ids,
        )
        return base_prompt + booking_part

    @staticmethod
    def _build_empty_services_prompt() -> str:
        return ai_prompt_templates.empty_services_prompt.format(
            clinic_name=clinic_texts.name,
            clinic_phone=clinic_texts.phone,
        )
