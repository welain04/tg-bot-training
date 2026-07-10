import logging
from datetime import date

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.data.mock import ANY_DOCTOR_ID, ANY_DOCTOR_NAME
from bot.keyboards.booking import (
    ai_pick_service_keyboard,
    ai_service_confirm_keyboard,
    confirm_keyboard,
    dates_keyboard,
    doctors_keyboard,
    name_input_keyboard,
    no_dates_keyboard,
    no_times_keyboard,
    phone_input_keyboard,
    services_keyboard,
    success_keyboard,
    times_keyboard,
)
from bot.keyboards.main_menu import main_menu_keyboard
from bot.messages.templates import (
    AI_ERROR_TEXT,
    AI_PICK_NOT_CONFIGURED_TEXT,
    AI_PICK_SERVICE_TEXT,
    BOOKING_IN_PROGRESS_TEXT,
    BOOKING_SAVE_ERROR_TEXT,
    CANCEL_TEXT,
    INPUT_NAME_TEXT,
    INPUT_PHONE_TEXT,
    NO_DATES_TEXT,
    NO_SERVICES_TEXT,
    NO_TIMES_TEXT,
    SELECT_DATE_TEXT,
    SELECT_DOCTOR_TEXT,
    SELECT_SERVICE_TEXT,
    SELECT_TIME_TEXT,
    format_ai_service_recommendation,
    format_confirm_text,
    format_success_text,
)
from bot.states.booking import BookingStates
from bot.utils.typing_action import with_typing
from domain.models.service import Service
from services.deps import (
    get_booking_service,
    get_clinic_data_service,
    get_llm_service,
    get_schedule_service,
    run_sync,
)
from services.llm_service import ChatMessage
from services.notification_service import NotificationService
from services.validation_service import ValidationService

router = Router()
logger = logging.getLogger(__name__)

AI_PICK_HISTORY_KEY = "ai_pick_history"


async def _get_services_keyboard():
    clinic_data = get_clinic_data_service()
    services = await run_sync(clinic_data.get_services)
    ai_available = get_llm_service().is_configured
    return services, services_keyboard(services, ai_pick_available=ai_available)


async def _go_to_doctor_selection(
    callback: CallbackQuery,
    state: FSMContext,
    service: Service,
) -> None:
    clinic_data = get_clinic_data_service()
    doctors = await run_sync(clinic_data.get_doctors_for_service, service.id)
    if not doctors:
        await callback.answer("Нет доступных врачей для этой услуги", show_alert=True)
        return

    await state.update_data(
        service_id=service.id,
        service_name=service.name,
        service_duration_min=service.duration_min,
    )
    await state.set_state(BookingStates.select_doctor)
    await callback.answer()
    await _edit_or_answer(
        callback,
        SELECT_DOCTOR_TEXT,
        doctors_keyboard(doctors),
    )


async def _edit_or_answer(callback: CallbackQuery, text: str, reply_markup) -> None:
    if not callback.message:
        return
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error):
            raise


async def _resolve_doctor_ids(data: dict) -> list[str]:
    doctor_id = data.get("doctor_id")
    if doctor_id:
        return [doctor_id]

    clinic_data = get_clinic_data_service()
    doctors = await run_sync(clinic_data.get_doctors_for_service, data["service_id"])
    return [doctor.id for doctor in doctors]


async def _get_available_dates(data: dict) -> list[date]:
    schedule = get_schedule_service()
    doctor_ids = await _resolve_doctor_ids(data)
    return await run_sync(
        schedule.get_available_dates,
        doctor_ids,
        data["service_duration_min"],
    )


async def _get_available_times(data: dict, appointment_date: date) -> list[str]:
    schedule = get_schedule_service()
    doctor_ids = await _resolve_doctor_ids(data)
    return await run_sync(
        schedule.get_available_times,
        doctor_ids,
        appointment_date,
        data["service_duration_min"],
    )


@router.callback_query(F.data == "book")
async def start_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        services, keyboard = await _get_services_keyboard()
    except Exception:
        logger.exception("Failed to load services for booking")
        await callback.answer("Не удалось загрузить услуги. Попробуйте позже.", show_alert=True)
        return

    if not services:
        await callback.answer()
        await _edit_or_answer(callback, NO_SERVICES_TEXT, main_menu_keyboard())
        return

    await state.set_state(BookingStates.select_service)
    await callback.answer()
    _, keyboard = await _get_services_keyboard()
    await _edit_or_answer(
        callback,
        SELECT_SERVICE_TEXT,
        keyboard,
    )


@router.callback_query(F.data == "cancel", BookingStates.select_service)
@router.callback_query(F.data == "cancel", BookingStates.ai_pick_service)
@router.callback_query(F.data == "cancel", BookingStates.select_doctor)
@router.callback_query(F.data == "cancel", BookingStates.select_date)
@router.callback_query(F.data == "cancel", BookingStates.select_time)
@router.callback_query(F.data == "cancel", BookingStates.input_name)
@router.callback_query(F.data == "cancel", BookingStates.input_phone)
@router.callback_query(F.data == "cancel", BookingStates.confirm)
async def cancel_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await _edit_or_answer(callback, CANCEL_TEXT, main_menu_keyboard())


@router.callback_query(F.data.startswith("svc:"), BookingStates.select_service)
async def select_service(callback: CallbackQuery, state: FSMContext) -> None:
    service_id = callback.data.split(":", maxsplit=1)[1]
    clinic_data = get_clinic_data_service()
    service = await run_sync(clinic_data.get_service_by_id, service_id)
    if service is None:
        await callback.answer("Услуга не найдена", show_alert=True)
        return

    await _go_to_doctor_selection(callback, state, service)


@router.callback_query(F.data == "pick_service_ai", BookingStates.select_service)
@router.callback_query(F.data == "pick_service_ai", BookingStates.ai_pick_service)
async def start_ai_service_pick(callback: CallbackQuery, state: FSMContext) -> None:
    llm = get_llm_service()
    if not llm.is_configured:
        await callback.answer(
            "Помощник недоступен. Выберите услугу из списка.",
            show_alert=True,
        )
        return

    await state.set_state(BookingStates.ai_pick_service)
    await state.update_data(**{AI_PICK_HISTORY_KEY: []})
    await callback.answer()
    await _edit_or_answer(callback, AI_PICK_SERVICE_TEXT, ai_pick_service_keyboard())


@router.callback_query(F.data.startswith("confirm_ai_svc:"), BookingStates.ai_pick_service)
async def confirm_ai_service(callback: CallbackQuery, state: FSMContext) -> None:
    service_id = callback.data.split(":", maxsplit=1)[1]
    clinic_data = get_clinic_data_service()
    service = await run_sync(clinic_data.get_service_by_id, service_id)
    if service is None:
        await callback.answer("Услуга не найдена", show_alert=True)
        return

    await _go_to_doctor_selection(callback, state, service)


@router.message(BookingStates.ai_pick_service, F.text)
async def handle_ai_service_pick(message: Message, state: FSMContext) -> None:
    llm = get_llm_service()
    if not llm.is_configured:
        await state.set_state(BookingStates.select_service)
        _, keyboard = await _get_services_keyboard()
        await message.answer(AI_PICK_NOT_CONFIGURED_TEXT, reply_markup=keyboard)
        return

    clinic_data = get_clinic_data_service()
    try:
        services = await run_sync(clinic_data.get_services)
    except Exception:
        logger.exception("Failed to load services for AI pick")
        await message.answer(AI_ERROR_TEXT, reply_markup=ai_pick_service_keyboard())
        return

    if not services:
        await message.answer(NO_SERVICES_TEXT, reply_markup=main_menu_keyboard())
        await state.clear()
        return

    data = await state.get_data()
    history_raw: list[dict[str, str]] = list(data.get(AI_PICK_HISTORY_KEY, []))
    history = [ChatMessage(role=item["role"], content=item["content"]) for item in history_raw]

    try:
        recommendation = await with_typing(
            message.bot,
            message.chat.id,
            llm.recommend_service(message.text, services, history),
        )
    except Exception:
        logger.exception("Failed to get AI service recommendation")
        await message.answer(AI_ERROR_TEXT, reply_markup=ai_pick_service_keyboard())
        return

    history_raw.append({"role": "user", "content": message.text})
    history_raw.append({"role": "assistant", "content": recommendation.reply})
    await state.update_data(**{AI_PICK_HISTORY_KEY: history_raw})

    if recommendation.service_id and not recommendation.needs_clarification:
        service = next(item for item in services if item.id == recommendation.service_id)
        await message.answer(
            format_ai_service_recommendation(service.name, recommendation.reply),
            reply_markup=ai_service_confirm_keyboard(service.id, service.name),
        )
        return

    await message.answer(recommendation.reply, reply_markup=ai_pick_service_keyboard())


@router.callback_query(F.data.startswith("doc:"), BookingStates.select_doctor)
async def select_doctor(callback: CallbackQuery, state: FSMContext) -> None:
    doctor_id = callback.data.split(":", maxsplit=1)[1]

    if doctor_id == ANY_DOCTOR_ID:
        doctor_name = ANY_DOCTOR_NAME
    else:
        clinic_data = get_clinic_data_service()
        doctor = await run_sync(clinic_data.get_doctor_by_id, doctor_id)
        if doctor is None:
            await callback.answer("Врач не найден", show_alert=True)
            return
        doctor_name = doctor.full_name

    await state.update_data(
        doctor_id=None if doctor_id == ANY_DOCTOR_ID else doctor_id,
        doctor_name=doctor_name,
    )
    await state.set_state(BookingStates.select_date)
    await callback.answer()

    data = await state.get_data()
    dates = await _get_available_dates(data)
    if not dates:
        await _edit_or_answer(callback, NO_DATES_TEXT, no_dates_keyboard())
        return

    await _edit_or_answer(callback, SELECT_DATE_TEXT, dates_keyboard(dates))


@router.callback_query(F.data.startswith("date:"), BookingStates.select_date)
async def select_date(callback: CallbackQuery, state: FSMContext) -> None:
    date_raw = callback.data.split(":", maxsplit=1)[1]
    appointment_date = date.fromisoformat(date_raw)
    data = await state.get_data()

    await state.update_data(appointment_date=appointment_date.isoformat())
    await state.set_state(BookingStates.select_time)
    await callback.answer()

    times = await _get_available_times(data, appointment_date)
    if not times:
        await _edit_or_answer(callback, NO_TIMES_TEXT, no_times_keyboard())
        return

    await _edit_or_answer(callback, SELECT_TIME_TEXT, times_keyboard(times))


@router.callback_query(F.data.startswith("time:"), BookingStates.select_time)
async def select_time(callback: CallbackQuery, state: FSMContext) -> None:
    appointment_time = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(appointment_time=appointment_time)
    await state.set_state(BookingStates.input_name)
    await callback.answer()
    await _edit_or_answer(callback, INPUT_NAME_TEXT, name_input_keyboard())


@router.message(BookingStates.input_name, F.text)
async def input_name(message: Message, state: FSMContext) -> None:
    is_valid, result = ValidationService.validate_full_name(message.text)
    if not is_valid:
        await message.answer(result, reply_markup=name_input_keyboard())
        return

    await state.update_data(full_name=result)
    await state.set_state(BookingStates.input_phone)
    await message.answer(INPUT_PHONE_TEXT, reply_markup=phone_input_keyboard())


@router.message(BookingStates.input_phone, F.text)
async def input_phone(message: Message, state: FSMContext) -> None:
    is_valid, result = ValidationService.validate_phone(message.text)
    if not is_valid:
        await message.answer(result, reply_markup=phone_input_keyboard())
        return

    await state.update_data(phone=result)
    data = await state.get_data()
    await state.set_state(BookingStates.confirm)

    appointment_date = date.fromisoformat(data["appointment_date"]).strftime("%d.%m.%Y")
    await message.answer(
        format_confirm_text(
            service_name=data["service_name"],
            doctor_name=data["doctor_name"],
            appointment_date=appointment_date,
            appointment_time=data["appointment_time"],
            full_name=data["full_name"],
            phone=result,
        ),
        reply_markup=confirm_keyboard(),
    )


@router.callback_query(F.data == "confirm", BookingStates.confirm)
async def confirm_booking(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("is_submitting"):
        await callback.answer(BOOKING_IN_PROGRESS_TEXT, show_alert=True)
        return

    user = callback.from_user
    if user is None:
        await callback.answer("Не удалось определить пользователя", show_alert=True)
        return

    await state.update_data(is_submitting=True)
    booking_service = get_booking_service()
    try:
        booking = await run_sync(
            booking_service.create_booking,
            telegram_id=user.id,
            telegram_username=user.username,
            full_name=data["full_name"],
            phone=data["phone"],
            service_id=data["service_id"],
            service_name=data["service_name"],
            doctor_id=data.get("doctor_id"),
            doctor_name=data["doctor_name"],
            appointment_date=data["appointment_date"],
            appointment_time=data["appointment_time"],
        )
        await NotificationService.notify_admin_new_booking(callback.bot, booking)
    except Exception:
        logger.exception("Failed to create booking")
        await state.update_data(is_submitting=False)
        await callback.answer(BOOKING_SAVE_ERROR_TEXT, show_alert=True)
        return

    await state.clear()
    await callback.answer()
    await _edit_or_answer(
        callback,
        format_success_text(booking.booking_id),
        success_keyboard(),
    )


@router.callback_query(F.data == "back:service", BookingStates.select_doctor)
@router.callback_query(F.data == "back:service", BookingStates.ai_pick_service)
async def back_to_service(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookingStates.select_service)
    await callback.answer()
    _, keyboard = await _get_services_keyboard()
    await _edit_or_answer(
        callback,
        SELECT_SERVICE_TEXT,
        keyboard,
    )


@router.callback_query(F.data == "back:doctor", BookingStates.select_date)
async def back_to_doctor(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    service_id = data.get("service_id")
    if not service_id:
        await start_booking(callback, state)
        return

    clinic_data = get_clinic_data_service()
    doctors = await run_sync(clinic_data.get_doctors_for_service, service_id)
    await state.set_state(BookingStates.select_doctor)
    await callback.answer()
    await _edit_or_answer(
        callback,
        SELECT_DOCTOR_TEXT,
        doctors_keyboard(doctors),
    )


@router.callback_query(F.data == "back:date", BookingStates.select_time)
async def back_to_date(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(BookingStates.select_date)
    await callback.answer()

    dates = await _get_available_dates(data)
    if not dates:
        await _edit_or_answer(callback, NO_DATES_TEXT, no_dates_keyboard())
        return

    await _edit_or_answer(callback, SELECT_DATE_TEXT, dates_keyboard(dates))


@router.callback_query(F.data == "back:phone", BookingStates.confirm)
async def back_to_phone(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookingStates.input_phone)
    await callback.answer()
    await _edit_or_answer(callback, INPUT_PHONE_TEXT, phone_input_keyboard())


@router.callback_query(F.data == "back:time", BookingStates.input_name)
async def back_to_time(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    appointment_date = date.fromisoformat(data["appointment_date"])

    await state.set_state(BookingStates.select_time)
    await callback.answer()

    times = await _get_available_times(data, appointment_date)
    if not times:
        await _edit_or_answer(callback, NO_TIMES_TEXT, no_times_keyboard())
        return

    await _edit_or_answer(callback, SELECT_TIME_TEXT, times_keyboard(times))


@router.callback_query(F.data == "back:name", BookingStates.input_phone)
async def back_to_name(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookingStates.input_name)
    await callback.answer()
    await _edit_or_answer(callback, INPUT_NAME_TEXT, name_input_keyboard())


@router.message(BookingStates.select_service)
@router.message(BookingStates.select_doctor)
@router.message(BookingStates.select_date)
@router.message(BookingStates.select_time)
@router.message(BookingStates.confirm)
async def booking_use_buttons(message: Message) -> None:
    from bot.messages.templates import USE_BUTTONS_TEXT

    await message.answer(USE_BUTTONS_TEXT)
