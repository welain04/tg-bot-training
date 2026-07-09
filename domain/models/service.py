from dataclasses import dataclass


@dataclass(frozen=True)
class Service:
    id: str
    name: str
    duration_min: int
    doctor_ids: tuple[str, ...] | None = None
