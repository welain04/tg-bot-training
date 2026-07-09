from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main_menu import back_to_menu_keyboard, main_menu_keyboard
from bot.messages.templates import get_about_text, get_contacts_text, get_main_menu_text

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        get_main_menu_text(),
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            get_main_menu_text(),
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data == "about")
async def show_about(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            get_about_text(),
            reply_markup=back_to_menu_keyboard(),
        )


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            get_contacts_text(),
            reply_markup=back_to_menu_keyboard(),
        )
