Write-Host ""
Write-Host "  XVCpanel — Visual Mixer" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Installing deps..." -ForegroundColor Yellow
pip install textual 2>$null
pip install -e . 2>$null
Write-Host "  OK" -ForegroundColor Green

Write-Host "[2/3] Done." -ForegroundColor Green
Write-Host ""
python -m xvcpanel
