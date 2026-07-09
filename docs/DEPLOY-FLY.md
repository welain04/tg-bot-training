# Деплой на Fly.io

## Источник кода: GitHub (рекомендуется)

Бот деплоится **из GitHub**, не с локального ПК.

1. Push в ветку `main` → GitHub Actions собирает и деплоит на Fly.io
2. Секреты бота (`BOT_TOKEN`, Google и т.д.) хранятся **на Fly.io** (`fly secrets`)
3. Локальный `fly deploy` **не используйте**

### Однократная настройка GitHub Actions

1. Создайте deploy-токен Fly (скрипт копирует токен в буфер):
   ```powershell
   .\scripts\create-fly-github-token.ps1
   ```
   Или вручную:
   ```powershell
   C:\Users\Sasha\.fly\bin\flyctl.exe tokens create deploy --app dental-booking-bot --name github-actions
   ```
   **Важно:** скопируйте токен **целиком**, включая префикс `FlyV1` и пробел после него.

2. Добавьте секрет в GitHub:
   - https://github.com/welain04/tg-bot-training/settings/secrets/actions
   - **New repository secret** (или **Update** если секрет уже есть)
   - Name: `FLY_API_TOKEN` (имя строго такое)
   - Value: вставьте токен без лишних пробелов/переносов строк

3. Запустите деплой:
   - https://github.com/welain04/tg-bot-training/actions
   - Workflow **Deploy to Fly.io** → **Run workflow**

После этого каждый `git push` в `main` автоматически обновляет бота на Fly.

**Как работает CI:** GitHub Actions собирает Docker-образ на своём runner, пушит в `registry.fly.io`, затем `flyctl deploy --image ...`. Remote builder Fly.io не используется — это надёжнее с deploy-токеном.

### Обновление текстов клиники

Тексты хранятся в **`config/clinic.toml`** в репозитории (UTF-8), не в Fly secrets.

1. Отредактируйте `config/clinic.toml`
2. `git push` в `main` — деплой через GitHub Actions подхватит изменения

Старые секреты `CLINIC_*` на Fly больше не используются (ломали кириллицу). При желании удалите их:
```powershell
C:\Users\Sasha\.fly\bin\flyctl.exe secrets unset CLINIC_NAME CLINIC_ABOUT CLINIC_ADDRESS CLINIC_PHONE CLINIC_HOURS --app dental-booking-bot
```

---

## Локальный деплой (устарело)

<details>
<summary>Только для отладки</summary>

Пошаговая инструкция для Windows ниже. Для production используйте GitHub Actions.

</details>

---

## Локальная инструкция (Windows)

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
| GitHub Actions: `unauthorized` / `remote builder heartbeat` | Deploy-токен не может поднять remote builder Fly. Workflow собирает Docker на GitHub runner — пересоздайте `FLY_API_TOKEN` (см. скрипт выше). Если не помогает: `flyctl auth token` → обновите секрет |

---

## Redis (опционально)

На Fly.io Redis **не обязателен**. Бот использует MemoryStorage — сессии сбрасываются при перезапуске контейнера.

Для production с Redis позже можно подключить [Upstash Redis](https://upstash.com/) (free tier) и добавить:

```powershell
fly secrets set REDIS_URL="redis://..."
```
