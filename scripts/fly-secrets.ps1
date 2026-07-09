# Reads .env and credentials, then sets Fly.io secrets.
# Usage: .\scripts\fly-secrets.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $root ".env"
$credsFile = Join-Path $root "credentials\google_service_account.json"
$flyctl = Join-Path $env:USERPROFILE ".fly\bin\flyctl.exe"

if (-not (Test-Path $flyctl)) {
    Write-Error "flyctl not found at $flyctl"
}

if (-not (Test-Path $envFile)) {
    Write-Error ".env not found at $envFile"
}

if (-not (Test-Path $credsFile)) {
    Write-Error "credentials file not found at $credsFile"
}

$vars = @{}
Get-Content $envFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line -match "^([^=]+)=(.*)$") {
        $vars[$Matches[1].Trim()] = $Matches[2].Trim()
    }
}

$required = @("BOT_TOKEN", "ADMIN_CHAT_ID", "GOOGLE_SHEETS_ID")
foreach ($name in $required) {
    if (-not $vars[$name]) {
        Write-Error "Missing $name in .env"
    }
}

function Set-FlySecret {
    param([string]$Name, [string]$Value)
    Write-Host "Setting $Name..."
    # stdin avoids Windows console encoding issues with Cyrillic
    $Value | & $flyctl secrets set "${Name}=-"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to set $Name"
    }
}

Set-FlySecret "BOT_TOKEN" $vars["BOT_TOKEN"]
Set-FlySecret "ADMIN_CHAT_ID" $vars["ADMIN_CHAT_ID"]
Set-FlySecret "GOOGLE_SHEETS_ID" $vars["GOOGLE_SHEETS_ID"]

Write-Host "Setting GOOGLE_CREDENTIALS_JSON..."
Get-Content -Raw -Encoding UTF8 $credsFile | & $flyctl secrets set "GOOGLE_CREDENTIALS_JSON=-"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to set GOOGLE_CREDENTIALS_JSON"
}

$optional = @(
    "CLINIC_NAME", "CLINIC_ABOUT", "CLINIC_ADDRESS", "CLINIC_PHONE", "CLINIC_HOURS",
    "FSM_TIMEOUT_MINUTES", "CALLBACK_THROTTLE_SECONDS", "LOG_LEVEL", "TIMEZONE"
)

foreach ($name in $optional) {
    if ($vars[$name]) {
        Set-FlySecret $name $vars[$name]
    }
}

Write-Host "Done. Fly will restart the app automatically."
