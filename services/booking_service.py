from datetime import datetime

from domain.models.booking import Booking
from integrations.google_sheets import GoogleSheetsClient
from utils.id_generator import format_created_at, generate_booking_id
from utils.sheets_constants import SHEET_BOOKINGS


class BookingService:
    def __init__(self, sheets_client: GoogleSheetsClient) -> None:
        self._sheets = sheets_client

    def create_booking(
        self,
        *,
        telegram_id: int,
        telegram_username: str | None,
        full_name: str,
        phone: str,
        service_id: str,
        service_name: str,
        doctor_id: str | None,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
    ) -> Booking:
        rows = self._sheets.get_rows(SHEET_BOOKINGS)
        existing_ids = [row[0] for row in rows[1:] if row]
        now = datetime.now()
        booking_id = generate_booking_id(existing_ids, now)
        created_at = format_created_at(now)
        stored_doctor_id = doctor_id or "any"
        username = f"@{telegram_username}" if telegram_username else ""

        self._sheets.append_row(
            SHEET_BOOKINGS,
            [
                booking_id,
                created_at,
                str(telegram_id),
                username,
                full_name,
                phone,
                service_id,
                service_name,
                stored_doctor_id,
                doctor_name,
                appointment_date,
                appointment_time,
                "pending",
                "",
                "",
            ],
        )

        return Booking(
            booking_id=booking_id,
            created_at=created_at,
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            full_name=full_name,
            phone=phone,
            service_id=service_id,
            service_name=service_name,
            doctor_id=stored_doctor_id,
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        )
