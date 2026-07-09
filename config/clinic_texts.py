import tomllib
from dataclasses import dataclass
from pathlib import Path

_CLINIC_FILE = Path(__file__).with_name("clinic.toml")


@dataclass(frozen=True, slots=True)
class ClinicTexts:
    name: str
    about: str
    address: str
    phone: str
    hours: str


def load_clinic_texts() -> ClinicTexts:
    if not _CLINIC_FILE.is_file():
        raise FileNotFoundError(
            f"Clinic config not found: {_CLINIC_FILE}. "
            "Ensure config/clinic.toml is included in the Docker image."
        )

    with _CLINIC_FILE.open("rb") as clinic_file:
        data = tomllib.load(clinic_file)

    def _require(key: str) -> str:
        value = str(data.get(key, "")).strip()
        if not value:
            raise ValueError(f"Missing or empty '{key}' in {_CLINIC_FILE}")
        return value

    return ClinicTexts(
        name=_require("clinic_name"),
        about=_require("clinic_about"),
        address=_require("clinic_address"),
        phone=_require("clinic_phone"),
        hours=_require("clinic_hours"),
    )


clinic_texts = load_clinic_texts()
