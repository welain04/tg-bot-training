import json
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)


def build_credentials(
    *,
    credentials_path: str,
    credentials_json: str | None = None,
) -> Credentials:
    if credentials_json:
        # Fly secrets / PowerShell may inject a UTF-8 BOM prefix.
        credentials_json = credentials_json.lstrip("\ufeff").strip()
        info: dict[str, Any] = json.loads(credentials_json)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    return Credentials.from_service_account_file(credentials_path, scopes=SCOPES)


class GoogleSheetsClient:
    def __init__(self, credentials: Credentials, spreadsheet_id: str) -> None:
        client = gspread.authorize(credentials)
        self._spreadsheet = client.open_by_key(spreadsheet_id)

    def get_rows(self, sheet_name: str) -> list[list[str]]:
        worksheet = self._spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_values()

    def append_row(self, sheet_name: str, row: list[str]) -> None:
        worksheet = self._spreadsheet.worksheet(sheet_name)
        worksheet.append_row(row, value_input_option="USER_ENTERED")
