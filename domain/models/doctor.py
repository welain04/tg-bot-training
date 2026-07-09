from dataclasses import dataclass


@dataclass(frozen=True)
class Doctor:
    id: str
    full_name: str
    service_ids: tuple[str, ...]
