from dataclasses import dataclass


@dataclass(frozen=True)
class Booking:
    booking_id: str
    created_at: str
    telegram_id: int
    telegram_username: str | None
    full_name: str
    phone: str
    service_id: str
    service_name: str
    doctor_id: str
    doctor_name: str
    appointment_date: str
    appointment_time: str
    status: str = "pending"
