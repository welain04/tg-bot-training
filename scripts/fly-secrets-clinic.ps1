# Updates only CLINIC_* secrets on Fly.io (UTF-8 safe).
# Usage: .\scripts\fly-secrets-clinic.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $root ".env"
$flyctl = Join-Path $env:USERPROFILE ".fly\bin\flyctl.exe"

$vars = @{}
Get-Content $envFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line -match "^([^=]+)=(.*)$") {
        $vars[$Matches[1].Trim()] = $Matches[2].Trim()
    }
}

foreach ($name in @("CLINIC_NAME", "CLINIC_ABOUT", "CLINIC_ADDRESS", "CLINIC_PHONE", "CLINIC_HOURS")) {
    if ($vars[$name]) {
        Write-Host "Setting $name..."
        $vars[$name] | & $flyctl secrets set "${name}=-"
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to set $name"
        }
    }
}

Write-Host "Done. Check bot: About / Contacts in Telegram."
