Write-Host ""
Write-Host "  XVCpanel - Visual Mixer"
Write-Host ""

Write-Host "[1/2] Installing deps..."
pip install textual 2>$null
pip install -e .
if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARN: pip install -e . failed, trying pip install . instead..."
    pip install . 2>$null
}
Write-Host "  OK"

Write-Host "[2/2] Launching..."
Write-Host ""
python -m xvcpanel
