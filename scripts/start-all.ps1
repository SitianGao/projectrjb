param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

& (Join-Path $PSScriptRoot "init-db.ps1")

$backendScript = Join-Path $PSScriptRoot "start-backend.ps1"
$frontendScript = Join-Path $PSScriptRoot "start-frontend.ps1"

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $backendScript,
    "-Port",
    $BackendPort
)

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $frontendScript,
    "-Port",
    $FrontendPort
)

Write-Host "Backend:  http://localhost:$BackendPort"
Write-Host "Swagger:  http://localhost:$BackendPort/docs"
Write-Host "Health:   http://localhost:$BackendPort/api/health"
Write-Host "Frontend: http://localhost:$FrontendPort"
