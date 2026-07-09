from config.settings import settings

SELECT_SERVICE_TEXT = (
    "📅 <b>Запись на приём</b>\n\n"
    "Шаг 1 из 7. Выберите услугу:"
)

SELECT_DOCTOR_TEXT = (
    "📅 <b>Запись на приём</b>\n\n"
    "Шаг 2 из 7. Выберите врача:"
)

SELECT_DATE_TEXT = (
    "📅 <b>Запись на приём</b>\n\n"
    "Шаг 3 из 7. Выберите дату:"
)

SELECT_TIME_TEXT = (
    "📅 <b>Запись на приём</b>\n\n"
    "Шаг 4 из 7. Выберите время:"
)

NO_DATES_TEXT = (
    "📅 <b>Запись на приём</b>\n\n"
    "К сожалению, нет свободных дат для выбранного врача.\n"
    "Попробуйте выбрать другого врача."
)

NO_TIMES_TEXT = (
    "📅 <b>Запись на приём</b>\n\n"
    "На выбранную дату нет свободного времени.\n"
    "Попробуйте выбрать другую дату."
)

INPUT_NAME_TEXT = (
    "📅 <b>Запись на приём</b>\n\n"
    "Шаг 5 из 7. Введите ваше <b>ФИО</b>:\n"
    "<i>Например: Иванов Иван Иванович</i>"
)

INPUT_PHONE_TEXT = (
    "📅 <b>Запись на приём</b>\n\n"
    "Шаг 6 из 7. Введите <b>номер телефона</b>:\n"
    "<i>Например: +79001234567</i>"
)

CANCEL_TEXT = "Запись отменена. Вы можете начать заново через главное меню."

SESSION_EXPIRED_TEXT = (
    "⏱ Сессия записи истекла из-за неактивности.\n"
    "Нажмите /start, чтобы начать заново."
)

NO_SERVICES_TEXT = (
    "Сейчас нет доступных услуг для записи.\n"
    "Пожалуйста, свяжитесь с администратором."
)

BOOKING_SAVE_ERROR_TEXT = "Не удалось сохранить заявку. Попробуйте позже."

BOOKING_IN_PROGRESS_TEXT = "Заявка уже отправляется, подождите..."

USE_BUTTONS_TEXT = "Пожалуйста, используйте кнопки меню или введите данные на текущем шаге."


def get_main_menu_text() -> str:
    return (
        f"🦷 <b>{settings.clinic_name}</b>\n\n"
        "Добро пожаловать! Выберите действие:"
    )


def get_about_text() -> str:
    return (
        "ℹ️ <b>О клинике</b>\n\n"
        f"{settings.clinic_about}\n\n"
        "Запись на приём — через кнопку «Записаться» в главном меню."
    )


def get_contacts_text() -> str:
    return (
        "📞 <b>Контакты</b>\n\n"
        f"📍 Адрес: {settings.clinic_address}\n"
        f"☎️ Телефон: {settings.clinic_phone}\n"
        f"🕐 Режим работы: {settings.clinic_hours}"
    )


def format_confirm_text(
    *,
    service_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    full_name: str,
    phone: str,
) -> str:
    return (
        "📅 <b>Запись на приём</b>\n\n"
        "Шаг 7 из 7. Проверьте данные:\n\n"
        f"🩺 <b>Услуга:</b> {service_name}\n"
        f"👨‍⚕️ <b>Врач:</b> {doctor_name}\n"
        f"📆 <b>Дата:</b> {appointment_date}\n"
        f"🕐 <b>Время:</b> {appointment_time}\n"
        f"👤 <b>ФИО:</b> {full_name}\n"
        f"📞 <b>Телефон:</b> {phone}"
    )


def format_success_text(booking_id: str) -> str:
    return (
        "✅ <b>Спасибо! Заявка создана.</b>\n\n"
        f"Номер заявки: <code>{booking_id}</code>\n\n"
        "В ближайшее время администратор свяжется с вами "
        "для окончательного подтверждения записи."
    )
