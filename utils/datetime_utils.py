from datetime import time


def parse_time(value: str) -> time | None:
    cleaned = value.strip()
    if not cleaned or cleaned in {"00:00", "0:00"}:
        return None

    parts = cleaned.split(":")
    if len(parts) != 2:
        return None

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
    except ValueError:
        return None

    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None

    return time(hours, minutes)


def time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def minutes_to_time(total_minutes: int) -> time:
    return time(total_minutes // 60, total_minutes % 60)


def format_time(value: time) -> str:
    return value.strftime("%H:%M")


def intervals_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a
