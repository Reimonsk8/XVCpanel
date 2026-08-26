param(
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw "Python 3.10+ was not found. Install it from https://python.org/downloads/"
}
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "  XVCpanel / LIVE VISUAL CONTROL"
Write-Host ""
Write-Host "[1/3] Creating local Python environment..."
if ($Python.Name -eq "py.exe") {
    & $Python.Source -3 -m venv (Join-Path $PSScriptRoot ".venv")
} else {
    & $Python.Source -m venv (Join-Path $PSScriptRoot ".venv")
}
if ($LASTEXITCODE -ne 0) { throw "Could not create .venv" }

Write-Host "[2/3] Installing XVCpanel and Python dependencies..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw "XVCpanel installation failed" }

Write-Host "[3/3] Checking optional visual runtimes..."
foreach ($Tool in @("cargo", "processing-java", "glslViewer", "make")) {
    $State = if (Get-Command $Tool -ErrorAction SilentlyContinue) { "ready" } else { "optional / not found" }
    Write-Host "  $Tool : $State"
}

if (-not $NoLaunch) {
    Write-Host ""
    & $VenvPython -m xvcpanel -d $PSScriptRoot
}
