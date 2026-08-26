param(
    [switch]$InstallRuntimes,
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

function Install-OptionalRuntimes {
    New-Item -ItemType Directory -Force -Path $Tools | Out-Null

    Write-Host "  Rust / Nannou"
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        $Rustup = Join-Path $env:TEMP "rustup-init.exe"
        Invoke-WebRequest "https://win.rustup.rs/x86_64" -OutFile $Rustup
        & $Rustup -y
        if ($LASTEXITCODE -ne 0) { throw "Rust installation failed" }
        Remove-Item $Rustup -Force
        $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
    }

    Write-Host "  Processing (portable, about 500 MB)"
    Install-GitHubZip "processing/processing4" "windows-x64-portable\.zip$" (Join-Path $Tools "processing")

    Write-Host "  glslViewer"
    $Glsl = Join-Path $Tools "glslViewer"
    Install-GitHubZip "patriciogonzalezvivo/glslViewer" "win64-AMD64\.zip$" $Glsl
    $GlslExe = Get-ChildItem $Glsl -Filter "glslViewer.exe" -Recurse | Select-Object -First 1
    if ($GlslExe -and -not (Get-ChildItem $GlslExe.Directory -Filter "avcodec*.dll" -ErrorAction SilentlyContinue)) {
        $Ffmpeg = Join-Path $Tools "ffmpeg"
        Install-Zip "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n4.4-latest-win64-gpl-shared-4.4.zip" $Ffmpeg
        Get-ChildItem $Ffmpeg -Filter "*.dll" -Recurse | Copy-Item -Destination $GlslExe.Directory -Force
    }

    Write-Host "  openFrameworks: manual SDK/toolchain selection still required"
    Write-Host "  https://openframeworks.cc/download/"
}

$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) { throw "Python 3.10+ was not found. Install it from https://python.org/downloads/" }
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "  XVCpanel / LIVE VISUAL CONTROL"
Write-Host ""
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

Write-Host "[2/4] Installing XVCpanel and Python dependencies..."
& $VenvPython -m pip install -e $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw "XVCpanel installation failed" }

Write-Host "[3/4] Optional visual runtimes..."
if ($InstallRuntimes) {
    Install-OptionalRuntimes
} else {
    Write-Host "  skipped (use -InstallRuntimes to install Rust, Processing, and glslViewer)"
}

Write-Host "[4/4] Runtime status..."
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
