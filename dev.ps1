# dev.ps1 - open the XVCpanel dev window in one WezTerm window:
#
#      ┌──────────────┬──────────────┐
#      │  nvim        │  xvcpanel    │   right: control panel
#      │  (editor)    │              │
#      └──────────────┴──────────────┘
#
# The live in-terminal preview pane is NOT opened here - toggle it from the
# panel with the "[v]" route button (or `o`). The panel spawns/kills the
# preview pane via `wezterm cli split-pane/close-pane` on the fly, watching
# the selected visual's own data/frame.png.
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
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Panel   = Join-Path $Root "xvcpanel\__main__.py"

# Run inside a fresh WezTerm window when launched from Explorer/cmd.
if (-not $env:WEZTERM_PANE) {
    & $Gui --config-file $Config start -- powershell -ExecutionPolicy Bypass -NoProfile -File $PSCommandPath
    exit
}

# Give every pane the wezterm CLI so the panel can split/close the preview pane.
$env:PATH = "$WezDir;$env:PATH"

# Splits happen against the pane that runs this script (pane 0).
$EditorPane = $env:WEZTERM_PANE
$PanelOut = & $Wez cli split-pane --right --pane-id $EditorPane --cwd $Root -- $Python $Panel -d $Root
$PanelPane = ($PanelOut | Select-Object -Last 1).Trim()

Write-Host "  layout: editor ($EditorPane)  |  panel ($PanelPane)"
Write-Host "  F9 in a pane to collapse/show/hide the other panes. Quit nvim when done."
Write-Host "  route [v] (or `o`) in the panel opens the in-terminal preview pane for the selected visual."

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