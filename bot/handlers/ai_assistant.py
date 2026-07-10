import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.booking import _start_doctor_selection
from bot.keyboards.ai_assistant import ai_chat_keyboard
from bot.messages.templates import AI_ASSISTANT_TEXT, AI_ERROR_TEXT, AI_NOT_CONFIGURED_TEXT
from bot.states.ai_assistant import AiAssistantStates
from bot.utils.typing_action import with_typing
from services.deps import get_clinic_data_service, get_llm_service, run_sync
from services.llm_service import ChatMessage

router = Router()
logger = logging.getLogger(__name__)

AI_CHAT_HISTORY_KEY = "ai_chat_history"
RECOMMENDED_SERVICE_ID_KEY = "recommended_service_id"

_BOOKING_INTENT = re.compile(
    r"\b(запиш\w*|запис\w*|записаться|оформ\w*\s*запись|хочу\s+на\s+при[её]м)\b",
    re.IGNORECASE,
)


@router.callback_query(F.data == "ask_ai")
async def start_ai_chat(callback: CallbackQuery, state: FSMContext) -> None:
    llm = get_llm_service()
    if not llm.is_configured:
        await callback.answer()
        if callback.message:
            await callback.message.edit_text(
                AI_NOT_CONFIGURED_TEXT,
                reply_markup=ai_chat_keyboard(),
            )
        return

    await state.set_state(AiAssistantStates.chatting)
    await state.update_data(**{AI_CHAT_HISTORY_KEY: [], RECOMMENDED_SERVICE_ID_KEY: None})
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            AI_ASSISTANT_TEXT,
            reply_markup=ai_chat_keyboard(),
        )


@router.message(AiAssistantStates.chatting, F.text)
async def handle_ai_message(message: Message, state: FSMContext) -> None:
    llm = get_llm_service()
    if not llm.is_configured:
        await state.clear()
        await message.answer(AI_NOT_CONFIGURED_TEXT, reply_markup=ai_chat_keyboard())
        return

    clinic_data = get_clinic_data_service()
    try:
        services = await run_sync(clinic_data.get_services)
    except Exception:
        logger.exception("Failed to load services for AI chat")
        await message.answer(AI_ERROR_TEXT, reply_markup=ai_chat_keyboard())
        return

    data = await state.get_data()
    pending_service_id = data.get(RECOMMENDED_SERVICE_ID_KEY)

    if pending_service_id and _BOOKING_INTENT.search(message.text):
        service = await run_sync(clinic_data.get_service_by_id, pending_service_id)
        if service is not None:
            await _start_doctor_selection(message, state, service)
            return

    history_raw: list[dict[str, str]] = list(data.get(AI_CHAT_HISTORY_KEY, []))
    history = [ChatMessage(role=item["role"], content=item["content"]) for item in history_raw]

    try:
        recommendation = await with_typing(
            message.bot,
            message.chat.id,
            llm.recommend_service(message.text, services, history),
        )
    except Exception:
        logger.exception("Failed to get LLM reply")
        await message.answer(AI_ERROR_TEXT, reply_markup=ai_chat_keyboard())
        return

    history_raw.append({"role": "user", "content": message.text})
    history_raw.append({"role": "assistant", "content": recommendation.reply})

    service = llm.resolve_service(recommendation, services)
    recommended_service_id = service.id if service else None
    await state.update_data(
        **{
            AI_CHAT_HISTORY_KEY: history_raw,
            RECOMMENDED_SERVICE_ID_KEY: recommended_service_id,
        }
    )

    await message.answer(
        recommendation.reply,
        reply_markup=ai_chat_keyboard(
            service_id=recommended_service_id,
            service_name=service.name if service else None,
        ),
    )
