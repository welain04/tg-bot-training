import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main_menu import back_to_menu_keyboard
from bot.messages.templates import AI_ASSISTANT_TEXT, AI_ERROR_TEXT, AI_NOT_CONFIGURED_TEXT
from bot.states.ai_assistant import AiAssistantStates
from bot.utils.typing_action import with_typing
from services.deps import get_llm_service
from services.llm_service import ChatMessage

router = Router()
logger = logging.getLogger(__name__)

AI_CHAT_HISTORY_KEY = "ai_chat_history"


@router.callback_query(F.data == "ask_ai")
async def start_ai_chat(callback: CallbackQuery, state: FSMContext) -> None:
    llm = get_llm_service()
    if not llm.is_configured:
        await callback.answer()
        if callback.message:
            await callback.message.edit_text(
                AI_NOT_CONFIGURED_TEXT,
                reply_markup=back_to_menu_keyboard(),
            )
        return

    await state.set_state(AiAssistantStates.chatting)
    await state.update_data(**{AI_CHAT_HISTORY_KEY: []})
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            AI_ASSISTANT_TEXT,
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(AiAssistantStates.chatting, F.text)
async def handle_ai_message(message: Message, state: FSMContext) -> None:
    llm = get_llm_service()
    if not llm.is_configured:
        await state.clear()
        await message.answer(AI_NOT_CONFIGURED_TEXT, reply_markup=back_to_menu_keyboard())
        return

    data = await state.get_data()
    history_raw: list[dict[str, str]] = list(data.get(AI_CHAT_HISTORY_KEY, []))
    history = [ChatMessage(role=item["role"], content=item["content"]) for item in history_raw]

    try:
        reply = await with_typing(
            message.bot,
            message.chat.id,
            llm.reply(message.text, history),
        )
    except Exception:
        logger.exception("Failed to get LLM reply")
        await message.answer(AI_ERROR_TEXT, reply_markup=back_to_menu_keyboard())
        return

    history_raw.append({"role": "user", "content": message.text})
    history_raw.append({"role": "assistant", "content": reply})
    await state.update_data(**{AI_CHAT_HISTORY_KEY: history_raw})
    await message.answer(reply, reply_markup=back_to_menu_keyboard())
