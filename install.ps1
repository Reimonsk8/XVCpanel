param(
    [switch]$NoLaunch,
    [switch]$InstallRuntimes,
    [switch]$InstallPresets,
    [switch]$SkipRuntimes,
    [switch]$SkipPresets
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Root = $PSScriptRoot
$Tools = Join-Path $Root ".tools"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$VenvScripts = Join-Path $Root ".venv\Scripts"

function Write-Stage($Text) { Write-Host "`n  $Text" -ForegroundColor Cyan }
function Write-Ok($Text) { Write-Host "  OK  $Text" -ForegroundColor Green }
function Write-Info($Text) { Write-Host "  ::  $Text" -ForegroundColor DarkGray }
function Write-Warn($Text) { Write-Host "  !!  $Text" -ForegroundColor Yellow }
function Write-Fail($Text) { Write-Host "  XX  $Text" -ForegroundColor Red }

function Add-ToUserPath([string]$Dir) {
    if (-not (Test-Path $Dir)) { return }
    $Dir = [IO.Path]::GetFullPath($Dir)
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $Parts = @($UserPath -split ";" | Where-Object { $_ })
    if (-not ($Parts | Where-Object { $_.TrimEnd('\') -ieq $Dir.TrimEnd('\') })) {
        [Environment]::SetEnvironmentVariable("Path", (($Parts + $Dir) -join ";"), "User")
        Write-Info "Added to user PATH: $Dir"
    }
    if (-not (($env:PATH -split [IO.Path]::PathSeparator) | Where-Object { $_.TrimEnd('\') -ieq $Dir.TrimEnd('\') })) {
        $env:PATH = "$Dir$([IO.Path]::PathSeparator)$env:PATH"
    }
}

function Add-AllToolBins {
    if (-not (Test-Path $Tools)) { return }
    Get-ChildItem $Tools -Filter "*.exe" -Recurse -File -ErrorAction SilentlyContinue |
        ForEach-Object { Add-ToUserPath $_.Directory.FullName }
}

function Find-Tool([string]$Name) {
    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($Command) { return $Command.Source }
    return $null
}

function Require-Command([string]$Name) {
    if (-not (Find-Tool $Name)) { throw "$Name was not available after installation." }
    Write-Ok "$Name ready"
}

function Install-GitHubZip([string]$Repository, [string]$AssetPattern, [string]$Destination) {
    if (Test-Path $Destination) {
        Write-Info "Reusing $Destination"
        return
    }
    $Release = Invoke-RestMethod "https://api.github.com/repos/$Repository/releases/latest"
    $Asset = $Release.assets | Where-Object { $_.name -match $AssetPattern } | Select-Object -First 1
    if (-not $Asset) { throw "No matching release asset in ${Repository}: $AssetPattern" }
    $Archive = Join-Path $env:TEMP ("xvcpanel-" + $Asset.name)
    try {
        Write-Info "Downloading $($Asset.name)"
        Invoke-WebRequest $Asset.browser_download_url -OutFile $Archive
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        Expand-Archive $Archive -DestinationPath $Destination -Force
    } finally {
        Remove-Item $Archive -Force -ErrorAction SilentlyContinue
    }
}

function Read-RuntimeChoice {
    if ($InstallRuntimes) { return "4" }
    if ($SkipRuntimes) { return "S" }
    Write-Host ""
    Write-Host "  [1] Rust / Nannou       cargo             ~200 MB" -ForegroundColor White
    Write-Host "  [2] Processing           Processing.exe    ~500 MB" -ForegroundColor White
    Write-Host "  [3] glslViewer           GLSL effects      ~50 MB" -ForegroundColor White
    Write-Host "  [4] Everything above     recommended" -ForegroundColor Magenta
    Write-Host "  [S] Core panel only" -ForegroundColor DarkGray
    do { $Choice = (Read-Host "  Select 1, 2, 3, 4, or S").Trim().ToUpper() } while ($Choice -notin @("1", "2", "3", "4", "S"))
    return $Choice
}

function Read-PresetChoice {
    if ($InstallPresets) { return $true }
    if ($SkipPresets) { return $false }
    Write-Host ""
    Write-Host "  [Y] Validate the 8 bundled visual presets" -ForegroundColor Magenta
    Write-Host "  [N] Skip preset validation" -ForegroundColor DarkGray
    do { $Choice = (Read-Host "  Include presets? Y/n").Trim().ToUpper() } while ($Choice -notin @("", "Y", "N"))
    return $Choice -ne "N"
}

function Read-LaunchChoice {
    if ($NoLaunch) { return $false }
    do { $Choice = (Read-Host "  Launch XVCpanel now? Y/n").Trim().ToUpper() } while ($Choice -notin @("", "Y", "N"))
    return $Choice -ne "N"
}

if ($InstallRuntimes -and $SkipRuntimes) { throw "Use either -InstallRuntimes or -SkipRuntimes, not both." }
if ($InstallPresets -and $SkipPresets) { throw "Use either -InstallPresets or -SkipPresets, not both." }

Write-Host ""
Write-Host "  XVCpanel" -ForegroundColor Cyan -NoNewline
Write-Host "  // LIVE VISUAL CONTROL SURFACE" -ForegroundColor Magenta
Write-Host "  --------------------------------" -ForegroundColor DarkCyan

Write-Stage "[1/5] Checking Python"
$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) { throw "Python 3.10+ is required: https://python.org/downloads/" }
if ($Python.Name -eq "py.exe") { $Version = & $Python.Source -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" } else { $Version = & $Python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" }
if ([version]$Version -lt [version]"3.10") { throw "Python 3.10+ is required; found $Version." }
Write-Ok "Python $Version"

Write-Stage "[2/5] Installing XVCpanel"
if (-not (Test-Path $VenvPython)) {
    if ($Python.Name -eq "py.exe") { & $Python.Source -3 -m venv (Join-Path $Root ".venv") } else { & $Python.Source -m venv (Join-Path $Root ".venv") }
    if ($LASTEXITCODE -ne 0) { throw "Could not create .venv." }
} else { Write-Info "Reusing .venv" }
& $VenvPython -m pip install --disable-pip-version-check -e $Root -q
if ($LASTEXITCODE -ne 0) { throw "XVCpanel installation failed." }
Add-ToUserPath $VenvScripts
Require-Command "xvcpanel"

Write-Stage "[3/5] Validating core panel"
& $VenvPython (Join-Path $Root "test_health.py")
if ($LASTEXITCODE -ne 0) { throw "Health check failed." }
Write-Ok "Core panel validated"

Write-Stage "[4/5] Visual runtimes"
$Choice = Read-RuntimeChoice
$InstallRust = $Choice -in @("1", "4")
$InstallProcessing = $Choice -in @("2", "4")
$InstallGlsl = $Choice -in @("3", "4")
if ($InstallRust -or $InstallProcessing -or $InstallGlsl) { New-Item -ItemType Directory -Force -Path $Tools | Out-Null }

if ($InstallRust) {
    if (-not (Find-Tool "cargo")) {
        $Rustup = Join-Path $env:TEMP "rustup-init.exe"
        try {
            Write-Info "Installing Rust stable toolchain"
            Invoke-WebRequest "https://win.rustup.rs/x86_64" -OutFile $Rustup
            & $Rustup -y
            if ($LASTEXITCODE -ne 0) { throw "Rust installation failed." }
        } finally { Remove-Item $Rustup -Force -ErrorAction SilentlyContinue }
    }
    Add-ToUserPath (Join-Path $env:USERPROFILE ".cargo\bin")
    Require-Command "cargo"
}

if ($InstallProcessing) {
    Install-GitHubZip "processing/processing4" "windows-x64-portable\.zip$" (Join-Path $Tools "processing")
    Add-AllToolBins
    Require-Command "Processing.exe"
}

if ($InstallGlsl) {
    Install-GitHubZip "patriciogonzalezvivo/glslViewer" "win64-AMD64\.zip$" (Join-Path $Tools "glslViewer")
    Add-AllToolBins
    Require-Command "glslViewer"
}

Install-GitHubZip "neovim/neovim" "nvim-win64\.zip$" (Join-Path $Tools "neovim")
Add-AllToolBins

Install-GitHubZip "wez/wezterm" "windows.*\.zip$" (Join-Path $Tools "wezterm")
Add-AllToolBins

Write-Stage "[5/5] Presets and global commands"
$UsePresets = Read-PresetChoice
if ($UsePresets) {
    $PresetCount = @(Get-ChildItem (Join-Path $Root "library") -Filter "xvc.json" -Recurse -File).Count
    Write-Ok "$PresetCount bundled visual presets are ready in library/"
} else {
    Write-Info "Bundled presets are already in library/. Re-run with -InstallPresets to list them."
}
Add-AllToolBins
foreach ($Tool in @("xvcpanel", "cargo", "Processing.exe", "glslViewer")) {
    if (Find-Tool $Tool) { Write-Ok "$Tool available in this terminal and future terminals" } else { Write-Info "$Tool not installed" }
}
Write-Warn "Commercial and host-based runtimes (TouchDesigner, Resolume Wire, Notch, Max, Unity, Unreal, vvvv) remain user-installed; add their CLI folder to PATH and a manifest will run them."
Write-Host ""
Write-Host "  Setup complete. New PowerShell, cmd, Git Bash, and Windows Terminal sessions inherit the user PATH." -ForegroundColor Green
Write-Host "  Launch anywhere: xvcpanel -d `"$Root`"" -ForegroundColor Cyan

if (Read-LaunchChoice) { & $VenvPython -m xvcpanel -d $Root }
