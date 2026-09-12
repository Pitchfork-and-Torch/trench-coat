# One-shot Windows engage: Tor + Casual Shadow cloak.
# Processes are started via Win32_Process.Create so they survive closed terminals.
#
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File .\scripts\engage-windows.ps1
# Point apps at: socks5://127.0.0.1:1080
# Verify: trench check-ip

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

function Test-Port([int]$Port) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $iar = $c.BeginConnect("127.0.0.1", $Port, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne(400)
    if ($ok -and $c.Connected) { $c.Close(); return $true }
    $c.Close()
  } catch {}
  return $false
}

function Start-Breakaway([string]$CommandLine, [string]$WorkDir) {
  $r = ([wmiclass]"\\.\root\cimv2:Win32_Process").Create($CommandLine, $WorkDir, $null)
  if ($r.ReturnValue -ne 0) {
    throw "Win32_Process.Create failed code=$($r.ReturnValue) for: $CommandLine"
  }
  return [int]$r.ProcessId
}

Write-Host ""
Write-Host "  TRENCH COAT :: ENGAGE (Windows)" -ForegroundColor Green
Write-Host "  THE SHADOWS ARE YOUR ALLY" -ForegroundColor Magenta
Write-Host ""

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Write-Host "No .venv. Run: python -m venv .venv ; .\.venv\Scripts\pip install -e ." -ForegroundColor Yellow
  exit 1
}

$chain = if ($env:TRENCH_CHAIN) { $env:TRENCH_CHAIN } else { "casual-shadow" }
& $py -m trenchcoat chain use $chain | Out-Host

# --- Tor ---
# Local lab hops for Ghost/Journalist multi-hop (skip if only casual-shadow)
if ($chain -ne "casual-shadow") {
  Write-Host "Ensuring local lab hops (1081/1088)..." -ForegroundColor Cyan
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "start-local-hops.ps1")
}

if (-not (Test-Port 9050) -and -not (Test-Port 9150)) {
  Write-Host "Starting Tor..." -ForegroundColor Cyan
  & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "start-tor.ps1")
  Start-Sleep -Seconds 2
  if (-not (Test-Port 9050) -and -not (Test-Port 9150)) {
    $torExe = Join-Path $env:USERPROFILE "Desktop\Tor Browser\Browser\TorBrowser\Tor\tor.exe"
    $torrc = Join-Path $Root ".tor-data\torrc-tb.txt"
    if ((Test-Path $torExe) -and (Test-Path $torrc)) {
      $pidTor = Start-Breakaway "`"$torExe`" -f `"$torrc`"" (Split-Path $torExe)
      Write-Host "  tor pid=$pidTor (breakaway)"
      for ($i = 0; $i -lt 45; $i++) {
        if (Test-Port 9050) { break }
        Start-Sleep -Seconds 2
      }
    }
  }
} else {
  Write-Host "Tor SOCKS already listening." -ForegroundColor Green
}

if (-not (Test-Port 9050) -and -not (Test-Port 9150)) {
  Write-Host "Tor not up. Install Tor Browser (Desktop\Tor Browser) or set TOR_BROWSER_HOME." -ForegroundColor Red
  exit 1
}

# --- Cloak ---
if (Test-Port 1080) {
  Write-Host "Cloak entry already up on 1080." -ForegroundColor Green
} else {
  Write-Host "Starting cloak (breakaway)..." -ForegroundColor Cyan
  $cmd = "`"$py`" -m trenchcoat up --accept-legal --wait-tor 90 --chain $chain"
  $pidCloak = Start-Breakaway $cmd $Root
  Write-Host "  cloak pid=$pidCloak"
  $ok = $false
  for ($i = 0; $i -lt 60; $i++) {
    if (Test-Port 1080) { $ok = $true; break }
    Start-Sleep -Seconds 2
  }
  if (-not $ok) {
    Write-Host "Cloak did not bind :1080. Run: trench doctor" -ForegroundColor Red
    exit 1
  }
}

Write-Host ""
Write-Host "  Point apps at: socks5://127.0.0.1:1080" -ForegroundColor Cyan
Write-Host "  Verify:        trench check-ip" -ForegroundColor Cyan
Write-Host "  GUI:           trench gui  -> http://127.0.0.1:8742" -ForegroundColor Cyan
Write-Host ""
& $py -m trenchcoat check-ip
exit $LASTEXITCODE
