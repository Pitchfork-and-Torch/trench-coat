# Best-effort packaging hooks (Phase 4 expands Tauri / PyInstaller)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Building wheel..." -ForegroundColor Cyan
python -m pip install build --quiet
python -m build
Write-Host "Artifacts in dist/ — AppImage/dmg/exe require Phase 4 Tauri pipeline." -ForegroundColor Yellow
