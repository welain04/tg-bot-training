# Создаёт deploy-токен Fly.io для GitHub Actions и копирует в буфер обмена.
# Запуск: .\scripts\create-fly-github-token.ps1

$ErrorActionPreference = "Stop"
$flyctl = "C:\Users\Sasha\.fly\bin\flyctl.exe"
$app = "dental-booking-bot"

if (-not (Test-Path $flyctl)) {
    Write-Error "flyctl не найден: $flyctl. Установите Fly CLI и выполните fly auth login."
}

Write-Host "Проверка входа в Fly.io..."
& $flyctl auth whoami | Out-Null

Write-Host "Создание deploy-токена для app=$app ..."
$token = & $flyctl tokens create deploy --app $app --name github-actions 2>&1 | Out-String
$token = $token.Trim()

if (-not $token.StartsWith("FlyV1")) {
    Write-Error "Неожиданный формат токена. Ожидался префикс FlyV1. Вывод:`n$token"
}

Set-Clipboard -Value $token

Write-Host ""
Write-Host "Токен скопирован в буфер обмена (начинается с FlyV1)."
Write-Host ""
Write-Host "Добавьте его в GitHub:"
Write-Host "  https://github.com/welain04/tg-bot-training/settings/secrets/actions"
Write-Host "  Secret name: FLY_API_TOKEN"
Write-Host "  Value: вставьте из буфера (Ctrl+V), без пробелов в начале/конце"
Write-Host ""
Write-Host "Если deploy-токен не помогает, используйте полный токен:"
Write-Host "  & $flyctl auth token"
Write-Host "  (тоже скопируйте целиком, включая FlyV1)"
