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
Write-Host "[1/3] Checking Python..." -ForegroundColor Yellow
try {
    $pyVer = python --version 2>&1
    Write-Host "  OK  $pyVer" -ForegroundColor Green
} catch {
    Write-Host "  ERR Python not found. Install from https://python.org" -ForegroundColor Red
    exit 1
}

# ── Install deps ──────────────────────────────────────────────────────────────
Write-Host "[2/3] Installing dependencies..." -ForegroundColor Yellow
pip install textual --quiet 2>&1 | Out-Null
pip install -e . --quiet 2>&1 | Out-Null
Write-Host "  OK  textual + xvcpanel installed" -ForegroundColor Green

# ── Run ───────────────────────────────────────────────────────────────────────
Write-Host "[3/3] Launching XVCpanel..." -ForegroundColor Yellow
Write-Host ""
python -m xvcpanel
