from dataclasses import dataclass, field
from datetime import date, time, timedelta

from domain.models.schedule import TimeInterval
from integrations.google_sheets import GoogleSheetsClient
from services.clinic_data_service import ClinicDataService
from utils.datetime_utils import (
    format_time,
    intervals_overlap,
    minutes_to_time,
    parse_time,
    time_to_minutes,
)
from utils.sheets_constants import (
    SHEET_BOOKINGS,
    SHEET_BREAKS,
    SHEET_BUSY_SLOTS,
    SHEET_EXCEPTIONS,
    SHEET_SCHEDULE,
    SLOT_STEP_MIN,
    WEEKDAY_NAMES,
)


@dataclass(frozen=True)
class ScheduleException:
    doctor_id: str
    exception_date: date
    type: str
    start: str
    end: str


@dataclass(frozen=True)
class BusyBlock:
    doctor_id: str
    block_date: date
    start: time
    end: time


@dataclass
class ScheduleCache:
    schedule_rows: list[list[str]]
    break_rows: list[list[str]]
    exception_rows: list[list[str]]
    busy_rows: list[list[str]]
    booking_rows: list[list[str]]
    service_durations: dict[str, int] = field(default_factory=dict)


class ScheduleService:
    def __init__(
        self,
        sheets_client: GoogleSheetsClient,
        clinic_data_service: ClinicDataService,
    ) -> None:
        self._sheets = sheets_client
        self._clinic_data = clinic_data_service

    def get_available_dates(
        self,
        doctor_ids: list[str],
        duration_min: int,
        *,
        days_ahead: int = 30,
        max_dates: int = 14,
    ) -> list[date]:
        if not doctor_ids:
            return []

        cache = self._load_cache()
        today = date.today()
        result: list[date] = []
        current = today + timedelta(days=1)

        while current <= today + timedelta(days=days_ahead) and len(result) < max_dates:
            if self._get_available_times_cached(cache, doctor_ids, current, duration_min):
                result.append(current)
            current += timedelta(days=1)

        return result

    def get_available_times(
        self,
        doctor_ids: list[str],
        appointment_date: date,
        duration_min: int,
    ) -> list[str]:
        if not doctor_ids:
            return []

        cache = self._load_cache()
        return self._get_available_times_cached(cache, doctor_ids, appointment_date, duration_min)

    def _load_cache(self) -> ScheduleCache:
        services = self._clinic_data.get_services()
        return ScheduleCache(
            schedule_rows=self._sheets.get_rows(SHEET_SCHEDULE),
            break_rows=self._sheets.get_rows(SHEET_BREAKS),
            exception_rows=self._sheets.get_rows(SHEET_EXCEPTIONS),
            busy_rows=self._sheets.get_rows(SHEET_BUSY_SLOTS),
            booking_rows=self._sheets.get_rows(SHEET_BOOKINGS),
            service_durations={service.id: service.duration_min for service in services},
        )

    def _get_available_times_cached(
        self,
        cache: ScheduleCache,
        doctor_ids: list[str],
        appointment_date: date,
        duration_min: int,
    ) -> list[str]:
        slot_starts: set[str] = set()
        for doctor_id in doctor_ids:
            for slot in self._get_doctor_slots(cache, doctor_id, appointment_date, duration_min):
                slot_starts.add(slot)
        return sorted(slot_starts)

    def _get_doctor_slots(
        self,
        cache: ScheduleCache,
        doctor_id: str,
        appointment_date: date,
        duration_min: int,
    ) -> list[str]:
        windows = self._get_work_windows(cache, doctor_id, appointment_date)
        if not windows:
            return []

        windows = self._subtract_breaks(cache, windows, doctor_id, appointment_date)
        busy_blocks = self._get_busy_blocks(cache, doctor_id, appointment_date)
        return self._generate_slots(windows, busy_blocks, duration_min)

    def _get_work_windows(
        self,
        cache: ScheduleCache,
        doctor_id: str,
        appointment_date: date,
    ) -> list[TimeInterval]:
        exception = self._get_exception(cache, doctor_id, appointment_date)
        if exception is not None:
            if exception.type == "day_off":
                return []
            if exception.type == "override":
                start = parse_time(exception.start)
                end = parse_time(exception.end)
                if start and end and start < end:
                    return [TimeInterval(start=start, end=end)]
                return []

        weekday = WEEKDAY_NAMES[appointment_date.weekday()]
        windows: list[TimeInterval] = []

        for row in cache.schedule_rows[1:]:
            if len(row) < 5:
                continue
            if row[0].strip() != doctor_id or row[1].strip().lower() != weekday:
                continue
            if not self._is_active(row[4]):
                continue

            start = parse_time(row[2])
            end = parse_time(row[3])
            if start and end and start < end:
                windows.append(TimeInterval(start=start, end=end))

        return windows

    def _subtract_breaks(
        self,
        cache: ScheduleCache,
        windows: list[TimeInterval],
        doctor_id: str,
        appointment_date: date,
    ) -> list[TimeInterval]:
        weekday = WEEKDAY_NAMES[appointment_date.weekday()]
        breaks: list[TimeInterval] = []

        for row in cache.break_rows[1:]:
            if len(row) < 4:
                continue
            if row[0].strip() != doctor_id or row[1].strip().lower() != weekday:
                continue

            start = parse_time(row[2])
            end = parse_time(row[3])
            if start and end and start < end:
                breaks.append(TimeInterval(start=start, end=end))

        return self._subtract_intervals(windows, breaks)

    def _get_busy_blocks(
        self,
        cache: ScheduleCache,
        doctor_id: str,
        appointment_date: date,
    ) -> list[BusyBlock]:
        blocks: list[BusyBlock] = []
        date_iso = appointment_date.isoformat()

        for row in cache.busy_rows[1:]:
            if len(row) < 6:
                continue
            if row[0].strip() != doctor_id or row[1].strip() != date_iso:
                continue
            if row[5].strip().lower() == "cancelled":
                continue

            start = parse_time(row[2])
            end = parse_time(row[3])
            if start and end and start < end:
                blocks.append(
                    BusyBlock(
                        doctor_id=doctor_id,
                        block_date=appointment_date,
                        start=start,
                        end=end,
                    )
                )

        for row in cache.booking_rows[1:]:
            if len(row) < 13:
                continue
            if row[8].strip() != doctor_id:
                continue
            if row[10].strip() != date_iso:
                continue
            if row[12].strip().lower() not in {"pending", "confirmed"}:
                continue

            start = parse_time(row[11])
            if start is None:
                continue

            service_id = row[6].strip()
            duration = cache.service_durations.get(service_id, 30)
            end_minutes = time_to_minutes(start) + duration
            blocks.append(
                BusyBlock(
                    doctor_id=doctor_id,
                    block_date=appointment_date,
                    start=start,
                    end=minutes_to_time(end_minutes),
                )
            )

        return blocks

    def _generate_slots(
        self,
        windows: list[TimeInterval],
        busy_blocks: list[BusyBlock],
        duration_min: int,
    ) -> list[str]:
        slots: list[str] = []

        for window in windows:
            slot_start = window.start_minutes
            latest_start = window.end_minutes - duration_min

            while slot_start <= latest_start:
                slot_end = slot_start + duration_min
                if not self._is_blocked(slot_start, slot_end, busy_blocks):
                    slots.append(format_time(minutes_to_time(slot_start)))
                slot_start += SLOT_STEP_MIN

        return slots

    @staticmethod
    def _is_blocked(slot_start: int, slot_end: int, busy_blocks: list[BusyBlock]) -> bool:
        for block in busy_blocks:
            block_start = time_to_minutes(block.start)
            block_end = time_to_minutes(block.end)
            if intervals_overlap(slot_start, slot_end, block_start, block_end):
                return True
        return False

    def _get_exception(
        self,
        cache: ScheduleCache,
        doctor_id: str,
        appointment_date: date,
    ) -> ScheduleException | None:
        date_iso = appointment_date.isoformat()

        for row in cache.exception_rows[1:]:
            if len(row) < 3:
                continue
            if row[0].strip() != doctor_id or row[1].strip() != date_iso:
                continue

            return ScheduleException(
                doctor_id=doctor_id,
                exception_date=appointment_date,
                type=row[2].strip().lower(),
                start=row[3].strip() if len(row) > 3 else "",
                end=row[4].strip() if len(row) > 4 else "",
            )

        return None

    @staticmethod
    def _subtract_intervals(
        windows: list[TimeInterval],
        removals: list[TimeInterval],
    ) -> list[TimeInterval]:
        result: list[TimeInterval] = []

        for window in windows:
            parts = [(window.start_minutes, window.end_minutes)]

            for removal in removals:
                updated_parts: list[tuple[int, int]] = []
                remove_start = removal.start_minutes
                remove_end = removal.end_minutes

                for part_start, part_end in parts:
                    if not intervals_overlap(part_start, part_end, remove_start, remove_end):
                        updated_parts.append((part_start, part_end))
                        continue

                    if part_start < remove_start:
                        updated_parts.append((part_start, remove_start))
                    if remove_end < part_end:
                        updated_parts.append((remove_end, part_end))

                parts = updated_parts

            for part_start, part_end in parts:
                if part_end - part_start > 0:
                    result.append(
                        TimeInterval(
                            start=minutes_to_time(part_start),
                            end=minutes_to_time(part_end),
                        )
                    )

        return result

    @staticmethod
    def _is_active(value: str) -> bool:
        return value.strip().upper() in {"TRUE", "1", "YES", "ДА"}
