param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$FrontendDir = Join-Path $ProjectRoot "frontend"
Set-Location $FrontendDir

if (-not $env:VITE_USE_MOCK) {
    $env:VITE_USE_MOCK = "false"
}

if (-not (Test-Path "node_modules")) {
    npm install
}

Write-Host "Starting frontend: http://localhost:$Port"
npm run dev -- --host 0.0.0.0 --port $Port
