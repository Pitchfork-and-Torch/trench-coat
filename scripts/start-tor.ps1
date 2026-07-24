# Start a headless Tor SOCKS listener on 127.0.0.1:9050 for Trench Coat.
# Requires Tor Browser portable (ships tor.exe). Set TOR_BROWSER_HOME if non-default.

$ErrorActionPreference = "Stop"

function Find-TorBrowser {
  if ($env:TOR_BROWSER_HOME -and (Test-Path $env:TOR_BROWSER_HOME)) {
    return $env:TOR_BROWSER_HOME
  }
  $candidates = @(
    (Join-Path $env:USERPROFILE "Desktop\Tor Browser"),
    (Join-Path $env:LOCALAPPDATA "Tor Browser"),
    "C:\Program Files\Tor Browser",
    "C:\Program Files (x86)\Tor Browser"
  )
  foreach ($c in $candidates) {
    if (Test-Path (Join-Path $c "Browser\TorBrowser\Tor\tor.exe")) { return $c }
  }
  return $null
}

$TorBrowserRoot = Find-TorBrowser
if (-not $TorBrowserRoot) {
  Write-Error "Tor Browser not found. Install from https://www.torproject.org/ or set TOR_BROWSER_HOME."
}

$BrowserDir = Join-Path $TorBrowserRoot "Browser"
$TorExe = Join-Path $BrowserDir "TorBrowser\Tor\tor.exe"
$GeoDir = Join-Path $BrowserDir "TorBrowser\Data\Tor"
$PtDir = Join-Path $BrowserDir "TorBrowser\Tor\PluggableTransports"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$DataDir = Join-Path $RepoRoot ".tor-data"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$existing = Get-NetTCPConnection -LocalPort 9050 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
  Write-Host "Tor already listening on 9050 (pid $($existing[0].OwningProcess))" -ForegroundColor Green
  exit 0
}

$torrc = Join-Path $DataDir "torrc-tb.txt"
$d = $DataDir.Replace('\', '/')
$g = $GeoDir.Replace('\', '/')
$pt = $PtDir.Replace('\', '/')
@(
  "SocksPort 127.0.0.1:9050"
  "ControlPort 127.0.0.1:9051"
  "CookieAuthentication 1"
  "DataDirectory $d"
  "GeoIPFile $g/geoip"
  "GeoIPv6File $g/geoip6"
  "Log notice file $d/notice.log"
  "ClientTransportPlugin meek_lite,obfs2,obfs3,obfs4,scramblesuit,webtunnel exec $pt/lyrebird.exe"
  "ClientTransportPlugin snowflake exec $pt/lyrebird.exe"
) | Set-Content $torrc -Encoding ASCII

Write-Host "Starting Tor from $TorBrowserRoot ..." -ForegroundColor Cyan
$p = Start-Process -FilePath $TorExe -ArgumentList "-f", $torrc -WorkingDirectory $BrowserDir -PassThru -WindowStyle Hidden
Write-Host "tor pid=$($p.Id)"

for ($i = 0; $i -lt 90; $i++) {
  Start-Sleep -Seconds 2
  if ($p.HasExited) {
    Write-Error "Tor exited early. See $DataDir\notice.log"
  }
  $logPath = Join-Path $DataDir "notice.log"
  if (Test-Path $logPath) {
    $raw = Get-Content $logPath -Raw
    if ($raw -match "Bootstrapped 100%") {
      Write-Host "Tor bootstrapped 100% - socks5://127.0.0.1:9050" -ForegroundColor Green
      exit 0
    }
    if ($i % 5 -eq 0) {
      $boot = ([regex]::Matches($raw, "Bootstrapped \d+%[^\r\n]*") | Select-Object -Last 1).Value
      Write-Host "  $boot"
    }
  }
}
Write-Error "Timed out waiting for Tor bootstrap. Check $DataDir\notice.log"
