# Деплой на Fly.io

Пошаговая инструкция для Windows.

## 1. Установить Fly CLI

PowerShell:

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

Перезапустите терминал, затем:

```powershell
fly version
fly auth login
```

Откроется браузер — войдите через GitHub или email.

---

## 2. Остановить локального бота

Если бот запущен на вашем ПК — остановите его (`Ctrl+C`).

Иначе будет ошибка: `Conflict: terminated by other getUpdates request`.

---

## 3. Создать приложение

```powershell
cd c:\Users\Sasha\tg-bot-training
fly apps create dental-booking-bot
```

Если имя **занято**, придумайте другое (латиница, дефисы), например `dental-booking-bot-sasha`, и:

1. Измените `app = "..."` в `fly.toml`
2. Выполните `fly apps create dental-booking-bot-sasha`

---

## 4. Задать секреты (переменные окружения)

### Обязательные

Подставьте значения из вашего `.env`:

```powershell
fly secrets set `
  BOT_TOKEN="ВАШ_BOT_TOKEN" `
  ADMIN_CHAT_ID="ВАШ_ADMIN_CHAT_ID" `
  GOOGLE_SHEETS_ID="ВАШ_GOOGLE_SHEETS_ID" `
  GOOGLE_CREDENTIALS_JSON="$(Get-Content -Raw credentials\google_service_account.json)"
```

### Тексты клиники (опционально)

```powershell
fly secrets set `
  CLINIC_NAME="Стоматологическая клиника" `
  CLINIC_ABOUT="Мы оказываем полный спектр стоматологических услуг." `
  CLINIC_ADDRESS="г. Москва, ул. Примерная, 1" `
  CLINIC_PHONE="+7 (495) 123-45-67" `
  CLINIC_HOURS="Пн–Сб, по предварительной записи"
```

Проверить список секретов (значения не показываются):

```powershell
fly secrets list
```

---

## 5. Деплой

```powershell
fly deploy
```

Первый деплой займёт 2–5 минут (сборка Docker-образа).

---

## 6. Проверка

Логи в реальном времени:

```powershell
fly logs
```

Ожидаемое:

```
Bot started (polling)
Run polling for bot @...
```

В Telegram: `/start` → **Записаться**.

Статус машины:

```powershell
fly status
```

---

## 7. Обновление после изменений кода

```powershell
fly deploy
```

---

## Полезные команды

| Действие | Команда |
|----------|---------|
| Логи | `fly logs` |
| Перезапуск | `fly machine restart --app dental-booking-bot` |
| SSH в контейнер | `fly ssh console` |
| Удалить приложение | `fly apps destroy dental-booking-bot` |

---

## Частые проблемы

| Проблема | Решение |
|----------|---------|
| `Conflict: getUpdates` | Остановите бота на ПК |
| Ошибка Google Sheets | Проверьте `GOOGLE_CREDENTIALS_JSON` и доступ к таблице |
| Имя app занято | Другое имя в `fly.toml` + `fly apps create` |
| Бот не стартует | `fly logs` — смотрите traceback |

---

## Redis (опционально)

На Fly.io Redis **не обязателен**. Бот использует MemoryStorage — сессии сбрасываются при перезапуске контейнера.

Для production с Redis позже можно подключить [Upstash Redis](https://upstash.com/) (free tier) и добавить:

```powershell
fly secrets set REDIS_URL="redis://..."
```
