# Telegram-бот для записи в стоматологическую клинику

Бот для записи на приём через Inline-кнопки. Данные хранятся в Google Sheets, расписание считается из таблицы. Встроен AI-помощник на Groq для ответов об услугах и подбора услуги при записи.

## Возможности

- Запись на приём за 7 шагов (услуга → врач → дата → время → ФИО → телефон → подтверждение)
- AI-помощник: ответы об услугах и подбор услуги по описанию симптомов (Groq)
- Справочники услуг и врачей из Google Sheets
- Расписание из листов: Расписание, Перерывы, Исключения, Занятые слоты
- Сохранение заявок в лист «Заявки»
- Уведомление администратора в Telegram
- Защита от двойного нажатия и истечение сессии записи

## Требования

- Python 3.11+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- Google Sheets с листами: **Услуги**, **Врачи**, **Расписание**, **Перерывы**, **Исключения**, **Занятые слоты**, **Заявки**
- Google Service Account
- API-ключ [Groq](https://console.groq.com/keys) — необязательно; без него бот работает, но AI-помощник отключён

---

## Локальный запуск

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Скопируйте `.env.example` → `.env` и заполните переменные.

Положите JSON-ключ service account в `credentials/google_service_account.json`.

Для AI-помощника добавьте `GROQ_API_KEY` в `.env` (ключ: [console.groq.com/keys](https://console.groq.com/keys), формат `gsk_...`).

```bash
python -m bot.main
```

В Telegram: `/start` → **Записаться** или **Спросить об услугах**.

---

## Переменные окружения

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `BOT_TOKEN` | да | Токен бота |
| `ADMIN_CHAT_ID` | да | Telegram ID администратора |
| `GOOGLE_SHEETS_ID` | да | ID Google-таблицы |
| `GOOGLE_CREDENTIALS_PATH` | локально | Путь к JSON-ключу |
| `GOOGLE_CREDENTIALS_JSON` | на сервере | JSON-ключ одной строкой (альтернатива файлу) |
| `TIMEZONE` | нет | Часовой пояс (по умолчанию `Europe/Moscow`) |
| `GROQ_API_KEY` | нет | API-ключ Groq для AI-помощника |
| `GROQ_MODEL` | нет | Модель Groq (по умолчанию `llama-3.3-70b-versatile`) |
| `GROQ_TEMPERATURE` | нет | Температура ответов (по умолчанию `0.3`) |
| `GROQ_MAX_TOKENS` | нет | Лимит токенов ответа (по умолчанию `300`) |
| `FSM_TIMEOUT_MINUTES` | нет | Таймаут сессии записи (по умолчанию 30) |
| `CALLBACK_THROTTLE_SECONDS` | нет | Задержка между нажатиями кнопок (по умолчанию `0.4`) |
| `REDIS_URL` | нет | Redis для FSM в production |
| `LOG_LEVEL` | нет | INFO, DEBUG, WARNING |

---

## Тексты клиники

Редактируйте `config/clinic.toml` (UTF-8): название, «О клинике», контакты. После изменений — `git push` в `main`, GitHub Actions задеплоит обновление.

## AI-помощник

Промпты и правила ответов — в `config/ai_prompt.toml` (UTF-8). Помощник отвечает только по услугам из Google Sheets и не выдумывает цены или процедуры.

Два сценария:
- **Спросить об услугах** — свободный диалог из главного меню
- **Подобрать услугу** — на шаге выбора услуги при записи

Без `GROQ_API_KEY` оба сценария недоступны; запись через кнопки работает как обычно.

---

## Деплой на Fly.io (рекомендуется)

Бесплатный tier, работает 24/7, без Oracle.

**Полная инструкция:** [docs/DEPLOY-FLY.md](docs/DEPLOY-FLY.md)

Кратко:

```powershell
# 1. CLI + вход
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
fly auth login

# 2. Создать app (имя из fly.toml или своё)
cd c:\Users\Sasha\tg-bot-training
fly apps create dental-booking-bot

# 3. Секреты из .env
.\scripts\fly-secrets.ps1

# 4. Деплой (локальный бот должен быть остановлен!)
fly deploy

# 5. Логи
fly logs
```

---

## Деплой через Docker (локально / VPS)

### 1. Подготовка

Убедитесь, что `.env` заполнен. Для Docker добавьте:

```env
REDIS_URL=redis://redis:6379/0
```

### 2. Запуск

```bash
docker compose up -d --build
```

Бот и Redis запустятся автоматически. Логи:

```bash
docker compose logs -f bot
```

### 3. Остановка

```bash
docker compose down
```

---

## Деплой на Railway / Render

1. Подключите репозиторий к платформе.
2. Добавьте переменные окружения из `.env.example`.
3. **Важно:** вместо файла credentials используйте `GOOGLE_CREDENTIALS_JSON` — скопируйте содержимое JSON-ключа **одной строкой**.
4. Добавьте Redis (Railway Redis plugin) и укажите `REDIS_URL`.
5. Команда запуска: `python -m bot.main`

---

## Деплой на VPS (Ubuntu)

```bash
git clone <repo-url> tg-bot-training
cd tg-bot-training
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Создайте systemd-сервис `/etc/systemd/system/dental-bot.service`:

```ini
[Unit]
Description=Dental Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/tg-bot-training
ExecStart=/home/ubuntu/tg-bot-training/.venv/bin/python -m bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable dental-bot
sudo systemctl start dental-bot
sudo systemctl status dental-bot
```

---

## Структура проекта

```
bot/           — handlers, keyboards, FSM, middlewares
config/        — настройки из .env, тексты клиники, AI-промпты
domain/        — модели данных
integrations/  — Google Sheets
services/      — бизнес-логика, LLM, подбор услуг
utils/         — утилиты
```

---

## Обновление бота

**Локально:** остановите (`Ctrl+C`) и запустите снова:

```bash
python -m bot.main
```

**Docker:**

```bash
docker compose up -d --build
```

**Systemd:**

```bash
sudo systemctl restart dental-bot
```
