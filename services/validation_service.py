import re


class ValidationService:
    _NAME_PATTERN = re.compile(r"^[А-Яа-яЁё\-]+(?: [А-Яа-яЁё\-]+)+$")
    _PHONE_DIGITS_PATTERN = re.compile(r"\D")

    @classmethod
    def validate_full_name(cls, text: str) -> tuple[bool, str | None]:
        normalized = " ".join(text.strip().split())
        if len(normalized) < 5:
            return False, "Введите полное ФИО (минимум имя и фамилия)."
        if not cls._NAME_PATTERN.match(normalized):
            return False, "ФИО должно быть на русском языке, например: Иванов Иван Иванович."
        return True, normalized

    @classmethod
    def validate_phone(cls, text: str) -> tuple[bool, str | None]:
        digits = cls._PHONE_DIGITS_PATTERN.sub("", text.strip())
        if digits.startswith("8") and len(digits) == 11:
            digits = "7" + digits[1:]
        if digits.startswith("7") and len(digits) == 11:
            return True, f"+{digits}"
        if len(digits) == 10:
            return True, f"+7{digits}"
        return False, "Введите номер в формате +79001234567 или 89001234567."
