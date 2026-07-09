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
        return ClinicTexts(
            name="Стоматологическая клиника",
            about=(
                "Мы оказываем полный спектр стоматологических услуг: "
                "консультации, лечение, профессиональную гигиену и хирургию."
            ),
            address="уточняйте у администратора",
            phone="уточняйте у администратора",
            hours="Пн–Сб, по предварительной записи",
        )

    with _CLINIC_FILE.open("rb") as clinic_file:
        data = tomllib.load(clinic_file)

    return ClinicTexts(
        name=str(data.get("clinic_name", "")).strip() or "Стоматологическая клиника",
        about=str(data.get("clinic_about", "")).strip(),
        address=str(data.get("clinic_address", "")).strip() or "уточняйте у администратора",
        phone=str(data.get("clinic_phone", "")).strip() or "уточняйте у администратора",
        hours=str(data.get("clinic_hours", "")).strip() or "Пн–Сб, по предварительной записи",
    )


clinic_texts = load_clinic_texts()
