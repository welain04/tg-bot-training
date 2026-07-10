import tomllib
from dataclasses import dataclass
from pathlib import Path

_AI_PROMPT_FILE = Path(__file__).with_name("ai_prompt.toml")


@dataclass(frozen=True, slots=True)
class AiPromptTemplates:
    system_prompt: str
    booking_picker_append: str
    empty_services_prompt: str


def load_ai_prompt_templates() -> AiPromptTemplates:
    if not _AI_PROMPT_FILE.is_file():
        raise FileNotFoundError(
            f"AI prompt config not found: {_AI_PROMPT_FILE}. "
            "Ensure config/ai_prompt.toml is included in the Docker image."
        )

    with _AI_PROMPT_FILE.open("rb") as prompt_file:
        data = tomllib.load(prompt_file)

    def _require(key: str) -> str:
        value = str(data.get(key, "")).strip()
        if not value:
            raise ValueError(f"Missing or empty '{key}' in {_AI_PROMPT_FILE}")
        return value

    return AiPromptTemplates(
        system_prompt=_require("system_prompt"),
        booking_picker_append=_require("booking_picker_append"),
        empty_services_prompt=_require("empty_services_prompt"),
    )


ai_prompt_templates = load_ai_prompt_templates()
