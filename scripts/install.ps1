# Trench Coat — Windows one-command installer (legal-first privacy cloak)
# Requires: Python 3.11+, network for pip

$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host "  TRENCH COAT :: INSTALL" -ForegroundColor Green
Write-Host "  THE SHADOWS ARE YOUR ALLY" -ForegroundColor Magenta
Write-Host ""

$Repo = if ($env:TRENCH_COAT_REPO) { $env:TRENCH_COAT_REPO } else { "https://github.com/Pitchfork-and-Torch/trench-coat.git" }
$Target = if ($env:TRENCH_COAT_HOME) { $env:TRENCH_COAT_HOME } else { Join-Path $HOME "trench-coat" }

function Assert-Python {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { throw "Python not found on PATH. Install Python 3.11+ from https://python.org" }
    $ver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    Write-Host "  Python $ver" -ForegroundColor Cyan
}

Assert-Python

if (-not (Test-Path $Target)) {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Host "  Cloning $Repo → $Target" -ForegroundColor Cyan
        git clone $Repo $Target
    } else {
        throw "git not found and $Target missing. Clone the repo manually, then re-run from that directory."
    }
} else {
    Write-Host "  Using existing $Target" -ForegroundColor Cyan
}

Set-Location $Target
if (-not (Test-Path ".venv") ) {
    python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
# Production install (add -Dev for pytest/ruff: $env:TRENCH_DEV=1)
if ($env:TRENCH_DEV) {
    & .\.venv\Scripts\pip.exe install -e ".[dev]"
} else {
    & .\.venv\Scripts\pip.exe install -e .
}

Write-Host ""
Write-Host "  Install complete." -ForegroundColor Green
Write-Host "  Activate:  .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "  Then:      trench banner" -ForegroundColor Yellow
Write-Host "             trench doctor" -ForegroundColor Yellow
Write-Host "             trench up --accept-legal" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Legal-first only. Run: trench legal" -ForegroundColor DarkGray
