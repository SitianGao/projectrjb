param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

& (Join-Path $PSScriptRoot "init-db.ps1")

Write-Host "Starting backend: http://localhost:$Port"
python -m uvicorn app:app --app-dir backend --host 0.0.0.0 --port $Port --reload
