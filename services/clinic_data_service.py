from domain.models.doctor import Doctor
from domain.models.service import Service
from integrations.google_sheets import GoogleSheetsClient
from utils.sheets_constants import SHEET_DOCTORS, SHEET_SERVICES


class ClinicDataService:
    def __init__(self, sheets_client: GoogleSheetsClient) -> None:
        self._sheets = sheets_client

    def get_services(self) -> list[Service]:
        rows = self._sheets.get_rows(SHEET_SERVICES)
        services: list[Service] = []

        for row in rows[1:]:
            if len(row) < 6:
                continue
            if not self._is_active(row[4]):
                continue

            doctor_ids_raw = row[5].strip()
            doctor_ids = None if doctor_ids_raw.lower() == "all" else self._split_ids(doctor_ids_raw)
            services.append(
                Service(
                    id=row[0].strip(),
                    name=row[1].strip(),
                    duration_min=int(row[2]),
                    doctor_ids=doctor_ids,
                )
            )

        return services

    def get_service_by_id(self, service_id: str) -> Service | None:
        return next((service for service in self.get_services() if service.id == service_id), None)

    def get_doctors(self) -> list[Doctor]:
        rows = self._sheets.get_rows(SHEET_DOCTORS)
        doctors: list[Doctor] = []

        for row in rows[1:]:
            if len(row) < 5:
                continue
            if not self._is_active(row[3]):
                continue

            doctors.append(
                Doctor(
                    id=row[0].strip(),
                    full_name=row[1].strip(),
                    service_ids=self._split_ids(row[4]),
                )
            )

        return doctors

    def get_doctor_by_id(self, doctor_id: str) -> Doctor | None:
        return next((doctor for doctor in self.get_doctors() if doctor.id == doctor_id), None)

    def get_doctors_for_service(self, service_id: str) -> list[Doctor]:
        service = self.get_service_by_id(service_id)
        if service is None:
            return []

        doctors = self.get_doctors()
        if service.doctor_ids is None:
            return [doctor for doctor in doctors if service_id in doctor.service_ids]

        allowed = set(service.doctor_ids)
        return [doctor for doctor in doctors if doctor.id in allowed]

    @staticmethod
    def _split_ids(raw: str) -> tuple[str, ...]:
        return tuple(part.strip() for part in raw.split(",") if part.strip())

    @staticmethod
    def _is_active(value: str) -> bool:
        return value.strip().upper() in {"TRUE", "1", "YES", "ДА"}
