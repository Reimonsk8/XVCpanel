param(
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Tools = Join-Path $PSScriptRoot ".tools"

function Install-GitHubZip($Repository, $AssetPattern, $Destination) {
    if (Test-Path $Destination) {
        Write-Host "  ready: $Destination"
        return
    }
    $Release = Invoke-RestMethod "https://api.github.com/repos/$Repository/releases/latest"
    $Asset = $Release.assets | Where-Object { $_.name -match $AssetPattern } | Select-Object -First 1
    if (-not $Asset) { throw "No $AssetPattern asset found in $Repository latest release" }
    $Archive = Join-Path $env:TEMP $Asset.name
    Write-Host "  downloading $($Asset.name)..."
    Invoke-WebRequest $Asset.browser_download_url -OutFile $Archive
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Expand-Archive $Archive -DestinationPath $Destination -Force
    Remove-Item $Archive -Force
}

function Install-Zip($Url, $Destination) {
    if (Test-Path $Destination) { return }
    $Archive = Join-Path $env:TEMP ([IO.Path]::GetFileName($Url))
    Invoke-WebRequest $Url -OutFile $Archive
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Expand-Archive $Archive -DestinationPath $Destination -Force
    Remove-Item $Archive -Force
}

# ── Python check ──────────────────────────────────────────────────────────────
$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) { throw "Python 3.10+ was not found. Install it from https://python.org/downloads/" }
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "  XVCpanel / LIVE VISUAL CONTROL"
Write-Host ""

# ── Step 1: venv ──────────────────────────────────────────────────────────────
Write-Host "[1/4] Creating local Python environment..."
if (-not (Test-Path $VenvPython)) {
    if ($Python.Name -eq "py.exe") {
        & $Python.Source -3 -m venv (Join-Path $PSScriptRoot ".venv")
    } else {
        & $Python.Source -m venv (Join-Path $PSScriptRoot ".venv")
    }
    if ($LASTEXITCODE -ne 0) { throw "Could not create .venv" }
} else {
    Write-Host "  ready: .venv"
}

# ── Step 2: pip install ───────────────────────────────────────────────────────
Write-Host "[2/4] Installing XVCpanel..."
& $VenvPython -m pip install -e $PSScriptRoot -q
if ($LASTEXITCODE -ne 0) { throw "XVCpanel installation failed" }

# ── Step 3: health check ──────────────────────────────────────────────────────
Write-Host "[3/5] Health check..."
& $VenvPython (Join-Path $PSScriptRoot "test_health.py")
if ($LASTEXITCODE -ne 0) { throw "Health check failed — fix errors before running" }

# ── Step 4: ask about runtimes ────────────────────────────────────────────────
Write-Host "[4/5] Visual runtimes"
Write-Host ""
Write-Host "  Which frameworks do you want to install?"
Write-Host ""
Write-Host "    [1] Rust / Nannou        (cargo)           ~200 MB"
Write-Host "    [2] Processing           (processing-java) ~500 MB"
Write-Host "    [3] glslViewer           (glslViewer)      ~50 MB"
Write-Host "    [4] All of the above"
Write-Host "    [S] Skip all"
Write-Host ""
$Choice = Read-Host "  Select (1/2/3/4/S)"

$InstallRust = $false
$InstallProcessing = $false
$InstallGlsl = $false

switch ($Choice.ToUpper()) {
    "1" { $InstallRust = $true }
    "2" { $InstallProcessing = $true }
    "3" { $InstallGlsl = $true }
    "4" { $InstallRust = $true; $InstallProcessing = $true; $InstallGlsl = $true }
    default { Write-Host "  Skipping runtimes." }
}

if ($InstallRust -or $InstallProcessing -or $InstallGlsl) {
    New-Item -ItemType Directory -Force -Path $Tools | Out-Null
}

if ($InstallRust) {
    Write-Host "  Installing Rust..."
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        $Rustup = Join-Path $env:TEMP "rustup-init.exe"
        Invoke-WebRequest "https://win.rustup.rs/x86_64" -OutFile $Rustup
        & $Rustup -y
        if ($LASTEXITCODE -ne 0) { throw "Rust installation failed" }
        Remove-Item $Rustup -Force
        $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
    }
    Write-Host "  ready: cargo"
}

if ($InstallProcessing) {
    Write-Host "  Installing Processing..."
    try {
        Install-GitHubZip "processing/processing4" "windows-x64-portable\.zip$" (Join-Path $Tools "processing")
        Write-Host "  ready: processing-java"
    } catch {
        Write-Host "  WARNING: Processing download failed: $_"
    }
}

if ($InstallGlsl) {
    Write-Host "  Installing glslViewer..."
    try {
        $Glsl = Join-Path $Tools "glslViewer"
        Install-GitHubZip "patriciogonzalezvivo/glslViewer" "win64-AMD64\.zip$" $Glsl
        Write-Host "  ready: glslViewer"
    } catch {
        Write-Host "  WARNING: glslViewer download failed: $_"
    }
}

Write-Host ""
Write-Host "  openFrameworks: install manually from https://openframeworks.cc/download/"

# ── Step 5: status ────────────────────────────────────────────────────────────
Write-Host "[5/5] Runtime status..."
$LocalBins = Get-ChildItem $Tools -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.Directory.FullName } | Select-Object -Unique
if ($LocalBins) { $env:PATH = ($LocalBins -join ";") + ";" + $env:PATH }
foreach ($Tool in @("cargo", "processing-java", "glslViewer", "make")) {
    $State = if (Get-Command $Tool -ErrorAction SilentlyContinue) { "ready" } else { "not found" }
    Write-Host "  $Tool : $State"
}

if (-not $NoLaunch) {
    Write-Host ""
    & $VenvPython -m xvcpanel -d $PSScriptRoot
}
