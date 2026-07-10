from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.data.mock import ANY_DOCTOR_ID, ANY_DOCTOR_NAME
from domain.models.doctor import Doctor
from domain.models.service import Service

_WEEKDAY_NAMES = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def _navigation_row(back_callback: str | None) -> list[InlineKeyboardButton]:
    row: list[InlineKeyboardButton] = []
    if back_callback:
        row.append(InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback))
    row.append(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return row


def services_keyboard(services: list[Service], *, ai_pick_available: bool = True) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=service.name, callback_data=f"svc:{service.id}")]
        for service in services
    ]
    if ai_pick_available:
        rows.append(
            [InlineKeyboardButton(text="🤖 Подобрать услугу", callback_data="pick_service_ai")]
        )
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ai_pick_service_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К списку услуг", callback_data="back:service")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def ai_service_confirm_keyboard(service_id: str, service_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Записаться: {service_name}",
                    callback_data=f"confirm_ai_svc:{service_id}",
                )
            ],
            [InlineKeyboardButton(text="🔄 Уточнить запрос", callback_data="pick_service_ai")],
            [InlineKeyboardButton(text="◀️ К списку услуг", callback_data="back:service")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def doctors_keyboard(doctors: list[Doctor]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=doctor.full_name, callback_data=f"doc:{doctor.id}")]
        for doctor in doctors
    ]
    rows.append(
        [InlineKeyboardButton(text=f"👤 {ANY_DOCTOR_NAME}", callback_data=f"doc:{ANY_DOCTOR_ID}")]
    )
    rows.append(_navigation_row("back:service"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dates_keyboard(dates: list[date]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{appointment_date.strftime('%d.%m.%Y')} ({_WEEKDAY_NAMES[appointment_date.weekday()]})",
                callback_data=f"date:{appointment_date.isoformat()}",
            )
        ]
        for appointment_date in dates
    ]
    rows.append(_navigation_row("back:doctor"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def times_keyboard(times: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for index, time_value in enumerate(times):
        row.append(InlineKeyboardButton(text=time_value, callback_data=f"time:{time_value}"))
        if len(row) == 3:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append(_navigation_row("back:date"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить запись", callback_data="confirm")],
            _navigation_row("back:phone"),
        ]
    )


def name_input_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            _navigation_row("back:time"),
        ]
    )


def phone_input_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            _navigation_row("back:name"),
        ]
    )


def success_keyboard() -> InlineKeyboardMarkup:
    from bot.keyboards.main_menu import back_to_menu_keyboard

    return back_to_menu_keyboard()


def no_dates_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Выбрать другого врача", callback_data="back:doctor")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def no_times_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Выбрать другую дату", callback_data="back:date")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )
