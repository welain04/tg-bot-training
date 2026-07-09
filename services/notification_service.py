from aiogram import Bot

from config.settings import settings
from domain.models.booking import Booking


class NotificationService:
    @staticmethod
    def format_booking_message(booking: Booking) -> str:
        username = f"@{booking.telegram_username}" if booking.telegram_username else "—"
        appointment_date = booking.appointment_date
        if len(appointment_date) == 10 and appointment_date[4] == "-":
            year, month, day = appointment_date.split("-")
            appointment_date = f"{day}.{month}.{year}"

        return (
            "🦷 <b>Новая заявка #{booking_id}</b>\n\n"
            f"👤 <b>ФИО:</b> {booking.full_name}\n"
            f"📞 <b>Телефон:</b> {booking.phone}\n"
            f"🩺 <b>Услуга:</b> {booking.service_name}\n"
            f"👨‍⚕️ <b>Врач:</b> {booking.doctor_name}\n"
            f"📅 <b>Дата:</b> {appointment_date}\n"
            f"🕐 <b>Время:</b> {booking.appointment_time}\n"
            f"📱 <b>Telegram:</b> {username} (id: {booking.telegram_id})\n"
            f"⏳ <b>Статус:</b> {booking.status}"
        )

    @staticmethod
    async def notify_admin_new_booking(bot: Bot, booking: Booking) -> None:
        await bot.send_message(
            chat_id=settings.admin_chat_id,
            text=NotificationService.format_booking_message(booking),
        )
