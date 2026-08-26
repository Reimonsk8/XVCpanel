Write-Host ""
Write-Host "  XVCpanel - Visual Mixer"
Write-Host ""

Write-Host "[1/2] Installing deps..."
pip install textual 2>$null
pip install -e . 2>$null
Write-Host "  OK"

Write-Host "[2/2] Launching..."
Write-Host ""
python -m xvcpanel
