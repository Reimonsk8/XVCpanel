# XVCpanel — one-shot install & run
# Usage: .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║       XVCpanel — Visual Mixer        ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Check Python ──────────────────────────────────────────────────────────────
Write-Host "[1/3] Checking Python..." -ForegroundColor Yellow
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "  ERR Python not found — install from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "  OK  python found" -ForegroundColor Green

# ── Install deps ──────────────────────────────────────────────────────────────
Write-Host "[2/3] Installing dependencies..." -ForegroundColor Yellow
pip install textual 2>$null
pip install -e . 2>$null
Write-Host "  OK  textual + xvcpanel installed" -ForegroundColor Green

# ── Run ───────────────────────────────────────────────────────────────────────
Write-Host "[3/3] Launching XVCpanel..." -ForegroundColor Yellow
Write-Host ""
python -m xvcpanel
