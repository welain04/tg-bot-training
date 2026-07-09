from datetime import datetime

SHEET_BOOKINGS = "Заявки"


def generate_booking_id(existing_ids: list[str], now: datetime | None = None) -> str:
    current = now or datetime.now()
    date_part = current.strftime("%Y%m%d")
    prefix = f"BK-{date_part}-"
    sequences = []

    for booking_id in existing_ids:
        if booking_id.startswith(prefix):
            try:
                sequences.append(int(booking_id.rsplit("-", maxsplit=1)[1]))
            except ValueError:
                continue

    next_sequence = max(sequences, default=0) + 1
    return f"{prefix}{next_sequence:03d}"


def format_created_at(now: datetime | None = None) -> str:
    current = now or datetime.now()
    return current.strftime("%Y-%m-%d %H:%M")
