# dev.ps1 - open the XVCpanel triptych in one WezTerm window:
#
#      ┌──────────────┬──────────────┐
#      │  nvim        │  preview     │   top-right: live in-terminal preview
#      │  (editor)    ├──────────────┤
#      │              │  xvcpanel    │   bottom-right: control panel
#      └──────────────┴──────────────┘
#
# Panes collapse/show/hide: focus a pane and press F9 (toggle back with F9 again),
# or per-pane: wezterm cli zoom-pane --pane-id <N> --toggle.
#
# Usage: powershell -ExecutionPolicy Bypass -File dev.ps1   (from anywhere, incl. Explorer)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

$WezDir = Get-ChildItem (Join-Path $Root ".tools\wezterm") -Recurse -Filter wezterm-gui.exe |
    Select-Object -First 1 -ExpandProperty DirectoryName
if (-not $WezDir) { throw "wezterm not found under $Root\.tools\wezterm - run install.ps1 first." }
$Wez = Join-Path $WezDir "wezterm.exe"
$Gui = Join-Path $WezDir "wezterm-gui.exe"
$Config = Join-Path $Root "wezterm.lua"

$Sketch = Join-Path $Root "library\glsl\kaleidoscope_processing"
$Frame  = Join-Path $Sketch "data\frame.png"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Preview = Join-Path $Root "xvcpanel\preview.py"
$Panel   = Join-Path $Root "xvcpanel\__main__.py"

# Run inside a fresh WezTerm window when launched from Explorer/cmd.
if (-not $env:WEZTERM_PANE) {
    & $Gui --config-file $Config start -- powershell -ExecutionPolicy Bypass -NoProfile -File $PSCommandPath
    exit
}

New-Item -ItemType Directory -Force (Join-Path $Sketch "data") | Out-Null

# Splits happen against the pane that runs this script (pane 0).
$EditorPane = $env:WEZTERM_PANE
$PanelOut = & $Wez cli split-pane --right --pane-id $EditorPane --cwd $Root -- $Python $Panel -d $Root
$PanelPane = ($PanelOut | Select-Object -Last 1).Trim()
$PreviewOut = & $Wez cli split-pane --top --pane-id $PanelPane --cwd $Sketch -- $Python $Preview --width 46 $Frame
$PreviewPane = ($PreviewOut | Select-Object -Last 1).Trim()

Write-Host "  layout: editor ($EditorPane)  |  preview ($PreviewPane) / panel ($PanelPane)"
Write-Host "  F9 in a pane to collapse/show/hide the other panes. Quit nvim when done."

# Editor for this pane: $EDITOR, then bundled nvim, then nvim on PATH.
$Editor = $env:EDITOR
if (-not $Editor) {
    $BundledNvim = Get-ChildItem (Join-Path $Root ".tools\neovim") -Recurse -Filter nvim.exe |
        Select-Object -First 1 -ExpandProperty FullName
    $Editor = if ((Get-Command nvim -ErrorAction SilentlyContinue)) { "nvim" }
              elseif ($BundledNvim) { $BundledNvim }
              else { "notepad" }
}
& $Editor (Join-Path $Sketch "kaleidoscope_processing.pde")