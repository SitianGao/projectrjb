param(
    [switch]$KeepExisting
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

$backendPath = Join-Path $ProjectRoot "backend"
if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $backendPath
} elseif (-not $env:PYTHONPATH.Contains($backendPath)) {
    $env:PYTHONPATH = "$backendPath;$env:PYTHONPATH"
}

$clearExisting = if ($KeepExisting) { "False" } else { "True" }

$pythonCode = @"
import json
import logging

from rag.knowledge_loader import quick_load

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
stats = quick_load(clear=$clearExisting)
print(json.dumps(stats, ensure_ascii=False, indent=2))

if stats.get("errors"):
    raise SystemExit(1)
"@

$pythonCode | python -
