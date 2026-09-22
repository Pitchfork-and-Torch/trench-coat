# Start local SOCKS hops for Ghost (1088) and Journalist (1081 + 1088).
# Loopback lab hops so multi-hop chains engage without a paid VPN.
# Replace with real VPN/VPS SOCKS when you have endpoints (edit config hops).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\start-local-hops.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  throw "Missing venv python. Create with: python -m venv .venv ; .\.venv\Scripts\pip install -e ."
}

function Test-Port([int]$Port) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $iar = $c.BeginConnect("127.0.0.1", $Port, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne(300)
    $live = $ok -and $c.Connected
    $c.Close()
    return $live
  } catch {
    return $false
  }
}

function Start-Breakaway([string]$CommandLine, [string]$WorkDir) {
  $r = ([wmiclass]"\\.\root\cimv2:Win32_Process").Create($CommandLine, $WorkDir, $null)
  if ($r.ReturnValue -ne 0) {
    throw "Create failed $($r.ReturnValue): $CommandLine"
  }
  return [int]$r.ProcessId
}

Write-Host ""
Write-Host "  TRENCH COAT :: LOCAL HOPS" -ForegroundColor Green
Write-Host "  1088 = ghost vpn-lab" -ForegroundColor Cyan
Write-Host "  1081 = journalist relay-lab" -ForegroundColor Cyan
Write-Host ""

$script = Join-Path $Root "scripts\local_socks_hop.py"

if (-not (Test-Port 1088)) {
  $cmd = "`"$py`" `"$script`" --port 1088 --label vpn-lab"
  $pid8 = Start-Breakaway $cmd $Root
  Write-Host "  started vpn-lab :1088 pid=$pid8" -ForegroundColor Green
} else {
  Write-Host "  :1088 already listening" -ForegroundColor Yellow
}

if (-not (Test-Port 1081)) {
  $cmd = "`"$py`" `"$script`" --port 1081 --label relay-lab"
  $pid1 = Start-Breakaway $cmd $Root
  Write-Host "  started relay-lab :1081 pid=$pid1" -ForegroundColor Green
} else {
  Write-Host "  :1081 already listening" -ForegroundColor Yellow
}

Start-Sleep -Seconds 1
foreach ($p in 1081, 1088) {
  $st = if (Test-Port $p) { "UP" } else { "DOWN" }
  Write-Host "  127.0.0.1:$p  $st"
}

Write-Host ""
Write-Host "  Next:" -ForegroundColor Cyan
Write-Host "    trench chain use ghost"
Write-Host "    trench up --accept-legal --wait-tor 60"
Write-Host "    trench check-ip"
Write-Host ""
Write-Host "  Real VPN later: edit ghost vpn-entry host/port to your provider SOCKS" -ForegroundColor DarkGray
Write-Host ""
