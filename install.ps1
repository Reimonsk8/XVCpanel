# XVCpanel — one-shot install & run
# Usage: irm https://raw.githubusercontent.com/Reimonsk8/XVCpanel/main/install.ps1 | iex
#   or:  .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║       XVCpanel — Visual Mixer        ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Check Python ──────────────────────────────────────────────────────────────
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
try {
    $pyVer = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "not found" }
    Write-Host "  OK  $pyVer" -ForegroundColor Green
} catch {
    Write-Host "  ERR Python not found" -ForegroundColor Red
    Write-Host "  Download: https://python.org/downloads" -ForegroundColor Gray
    exit 1
}

# ── Check pip ─────────────────────────────────────────────────────────────────
Write-Host "[2/4] Checking pip..." -ForegroundColor Yellow
try {
    pip --version 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "not found" }
    Write-Host "  OK  pip available" -ForegroundColor Green
} catch {
    Write-Host "  ERR pip not found — run: python -m ensurepip" -ForegroundColor Red
    exit 1
}

# ── Install deps ──────────────────────────────────────────────────────────────
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow
pip install textual --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARN textual install had issues, continuing..." -ForegroundColor DarkYellow
}
pip install -e . --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERR Failed to install xvcpanel" -ForegroundColor Red
    exit 1
}
Write-Host "  OK  textual + xvcpanel installed" -ForegroundColor Green

# ── Run ───────────────────────────────────────────────────────────────────────
Write-Host "[4/4] Launching XVCpanel..." -ForegroundColor Yellow
Write-Host ""
python -m xvcpanel
