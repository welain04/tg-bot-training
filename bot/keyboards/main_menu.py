from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
            [InlineKeyboardButton(text="💬 Спросить об услугах", callback_data="ask_ai")],
            [InlineKeyboardButton(text="ℹ️ О клинике", callback_data="about")],
            [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В главное меню", callback_data="menu")],
        ]
    )
