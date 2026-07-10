from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def ai_chat_keyboard(service_id: str | None = None, service_name: str | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if service_id and service_name:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📅 Продолжить запись: {service_name}",
                    callback_data=f"continue_booking:{service_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
