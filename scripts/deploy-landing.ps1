# Deploy Trench Coat landing to Cloudflare Pages (trenchcoat.jonbailey.xyz)
# Project: trench-coat · account from landing/.wrangler/cache/pages.json

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Landing = Join-Path $Root "landing"
$Project = "trench-coat"

Set-Location $Landing

# Ensure OG card exists
$og = Join-Path $Landing "assets\og-card.png"
if (-not (Test-Path $og)) {
  Write-Host "Rendering og-card.png..." -ForegroundColor Cyan
  & (Join-Path $Root ".venv\Scripts\python.exe") (Join-Path $Root "scripts\render_og_card.py")
  if (-not (Test-Path $og)) {
    python (Join-Path $Root "scripts\render_og_card.py")
  }
}

Write-Host ""
Write-Host "  TRENCH COAT :: LANDING DEPLOY" -ForegroundColor Green
Write-Host "  project=$Project  dir=$Landing" -ForegroundColor Cyan
Write-Host ""

npx --yes wrangler pages deploy $Landing `
  --project-name $Project `
  --branch main `
  --commit-dirty=true

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# IndexNow ping (Bing / compatible engines)
$key = "7577922ed4d3ec3df303933b78cbd0ee"
$hostName = "trenchcoat.jonbailey.xyz"
$keyLoc = "https://$hostName/$key.txt"
$urls = @(
  "https://$hostName/",
  "https://$hostName/llms.txt",
  "https://$hostName/sitemap.xml",
  "https://$hostName/robots.txt",
  "https://$hostName/assets/og-card.png",
  "https://$hostName/assets/trench-coat-gui-online.png"
)
$body = @{
  host        = $hostName
  key         = $key
  keyLocation = $keyLoc
  urlList     = $urls
} | ConvertTo-Json -Compress

Write-Host ""
Write-Host "  IndexNow notify..." -ForegroundColor Cyan
try {
  $resp = Invoke-RestMethod -Method Post -Uri "https://api.indexnow.org/indexnow" `
    -ContentType "application/json; charset=utf-8" `
    -Body $body
  Write-Host "  IndexNow OK" -ForegroundColor Green
} catch {
  Write-Host "  IndexNow: $($_.Exception.Message) (non-fatal)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Live:    https://trenchcoat.jonbailey.xyz/" -ForegroundColor Green
Write-Host "  OG card: https://trenchcoat.jonbailey.xyz/assets/og-card.png" -ForegroundColor Green
Write-Host "  llms:    https://trenchcoat.jonbailey.xyz/llms.txt" -ForegroundColor Green
Write-Host "  Preview checkers: opengraph.xyz · X compose paste" -ForegroundColor Gray
Write-Host ""
