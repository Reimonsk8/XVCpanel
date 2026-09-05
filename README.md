# XVCpanel

Windows-first live control surface for code visuals. XVCpanel discovers visual projects, checks their runtimes, builds and launches them, switches configured output commands, and sends OSC parameter values and LFO modulation.

XVCpanel launches renderers; each renderer still owns its window, framebuffer, and video transport. A visual must implement its own Spout, NDI, Syphon, or window output.

## Current Status

| Capability | Status |
|---|---|
| Browse, search, and filter visual projects | Working |
| Build, run, stop, and monitor child processes | Working |
| Rust/Nannou, Processing, and GLSL setup | Automated on 64-bit Windows |
| Manifest-defined output commands | Working |
| OSC float parameters and sine LFO | Working when the visual implements the OSC addresses |
| Bundled openFrameworks demos | Advanced/manual setup required |
| Bundled demo output to Resolume through Spout | Not implemented yet; the existing `spout` flags are legacy metadata |

## Successful Windows Setup

These instructions assume 64-bit Windows 10 or 11 and PowerShell 5.1 or newer.

### 1. Install Git and Python

Install:

- [Git for Windows](https://git-scm.com/download/win)
- [Python 3.10 or newer](https://www.python.org/downloads/windows/)

In the Python installer, enable **Add Python to PATH** and **Install launcher for all users** when those options are available.

Open a new PowerShell window and verify both tools:

```powershell
git --version
py -3 --version
```

If `py` is unavailable but `python --version` works, that is also supported by the installer.

### 2. Download XVCpanel

```powershell
git clone https://github.com/Reimonsk8/XVCpanel.git
Set-Location .\XVCpanel
```

If the repository is already downloaded, open PowerShell in its root folder, where `install.ps1` and `pyproject.toml` are visible.

### 3. Install XVCpanel and the supported runtimes

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -InstallRuntimes -NoLaunch
```

The command:

- Creates `.venv` for isolated Python packages.
- Installs XVCpanel and Textual.
- Installs Rust/Cargo for the Nannou demo if Cargo is missing.
- Downloads portable Processing into `.tools`.
- Downloads portable glslViewer and its required FFmpeg DLLs into `.tools`.
- Prints the final runtime status.

Add `-InstallPresets` to validate the bundled `library/` preset catalog during setup. Without flags, the wizard asks which runtimes to install. `-SkipRuntimes` makes an unattended core-only install.

Processing is approximately a 500 MB download. Keep the terminal open until the command finishes. Re-running the command is safe: the existing virtual environment and portable runtime folders are reused.

Expected final status for the automatically supported demos:

```text
cargo : ready
Processing.exe : ready
glslViewer : ready
```

`make` may remain `not found`. It is only used by the advanced openFrameworks demos.

### 4. Verify the installation

List all discovered visuals:

```powershell
.\.venv\Scripts\python.exe -m xvcpanel --list -d .
```

Run the automated checks:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

The tests should finish with `OK`. A warning that the Spout2 DLL was not found is expected because the Python Spout bridge is currently a placeholder and is not needed for window output.

### 5. Launch XVCpanel

```powershell
.\.venv\Scripts\python.exe -m xvcpanel -d .
```

For later launches, you may instead rerun the installer, which installs updates and launches automatically:

```powershell
.\install.ps1
```

The app scans `library/**/xvc.json`. The table reports `NEED <tool>` when a required executable cannot be found. Portable executables under `.tools` and Cargo under `%USERPROFILE%\.cargo\bin` are added to the app's PATH automatically.

## Running The Bundled Visuals

Use `j`/`k` or the arrow keys to highlight a row and press `Enter` to open its source in the editor. Click `[Run]` to build (when the manifest has a build command) and launch the selected visual.

### Flow Field: Processing

Requirements: `Processing.exe : ready`.

1. Select **Flow Field**.
2. Click `[Run]`.
3. Wait for the Processing window to open.

Controls inside the visual:

- Drag the mouse to alter the flow.
- Press `C` to clear.
- Press `F` to toggle the visual's fullscreen-sized surface.

Stop it from XVCpanel with `s`, or close the Processing window.

Manual diagnostic command:

```powershell
$Processing = Get-ChildItem .\.tools\processing -Filter Processing.exe -Recurse | Select-Object -First 1
& $Processing.FullName --sketch="$PWD\library\processing\flowfield" --run
```

### Warp Shader: GLSL

Requirements: `glslViewer : ready`.

1. Select **Warp Shader**.
2. Click `[Run]`.
3. The shader should open at 1920x1080.

The shader uses glslViewer-provided `time` and `resolution` uniforms. Close its window or press `s` in XVCpanel to stop it.

Manual diagnostic command:

```powershell
$GlslViewer = Get-ChildItem .\.tools\glslViewer -Filter glslViewer.exe -Recurse | Select-Object -First 1
& $GlslViewer.FullName .\library\glsl\warp\warp.frag -w 1920 -h 1080
```

If Windows reports a missing FFmpeg DLL, remove `.tools\glslViewer` and `.tools\ffmpeg`, then rerun `install.ps1 -InstallRuntimes -NoLaunch`.

### Wave Mesh: Nannou/Rust

Requirements: `cargo : ready` and an internet connection for the first Cargo build.

1. Select **Wave Mesh**.
2. Click `[Run]`.
3. Wait for Cargo to download and compile Nannou dependencies. The first build can take several minutes.
4. Later builds reuse Cargo's cache and should be faster.

Manual diagnostic commands:

```powershell
Set-Location .\library\nannou\wave_mesh
cargo build --release
cargo run --release
```

Return to the repository afterward with `Set-Location ..\..\..`.

### openFrameworks Demos

The bundled **Curl Noise Particles** and **Fluid Sim Stable** projects currently use openFrameworks Makefiles:

```makefile
OF_ROOT ?= $(HOME)/openframeworks
```

They are not ready-to-build Visual Studio projects. Seeing `NEED make` is expected on a normal Windows installation. To use them, install a matching openFrameworks MSYS2 distribution/toolchain, make sure `make` is on PATH, and set `OF_ROOT` to the extracted SDK folder before launching XVCpanel:

```powershell
$env:OF_ROOT = "C:\path\to\openFrameworks"
make --version
.\.venv\Scripts\python.exe -m xvcpanel -d .
```

Download the SDK from [openframeworks.cc/download](https://openframeworks.cc/download/). Do not mix a Visual Studio SDK archive with an MSYS2 Makefile toolchain. If you prefer Visual Studio, generate proper openFrameworks project files and update each `xvc.json` build/run command accordingly.

## XVCpanel Controls

| Key | Action |
|---|---|
| `j` / `Down`, `k` / `Up` | Select visual |
| `Enter`, `e` | Open selected visual's source in the editor (`:e` into the left pane inside dev.ps1, else a new window) |
| `r` | Build if needed and run selected visual |
| `b` | Build selected visual |
| `s` | Stop selected visual and its process tree |
| `o` | Toggle the preview route (`[v]`) - opens/closes the in-terminal preview pane |
| `g` | Toggle live reload (0.6 s mtime watcher) |
| `[` / `]` | Select exposed parameter |
| `-` / `=` | Decrease / increase parameter |
| `m` | Toggle a 0.25 Hz sine LFO on the parameter |
| `1`-`4`, `f` | Filter frameworks / show all |
| `/`, `Esc` | Search / clear search |
| `p` | Toggle details panel |
| `q` | Quit XVCpanel |

Action bar buttons: `[Run]` builds if needed and launches the route, `[Stop]` kills the process tree, `[Build]` builds only, `[edit]` opens the source, `[live]` toggles live reload, `[float]`/`[dock]` switches between the multiplexed triptych and separate windows, and `[w] [R] [v]` toggle the window / resolume / preview route per visual. Run, edit, and live also work with nothing selected (live edits the default GLSL sketch).

## Dev Workflow (WezTerm Triptych)

Run `dev.ps1` to open one WezTerm window with nvim on the left and the panel on the right:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\dev.ps1
```

- `Enter` or `e` in the panel types `:e <file>` into the left nvim pane and focuses it (the multiplexed edit). Outside dev.ps1 the file opens in a new terminal window instead.
- `[v]`/`o` spawns an in-terminal Kitty preview pane watching the selected visual's `data/frame.png` (all 7 Processing visuals emit it at ~4 fps); toggling off or changing selection kills it.
- `[float]` moves editor and preview into their own windows and closes the left pane; `[dock]` puts them back in one window.
- `F9` zooms/restores a pane (`wezterm cli zoom-pane --pane-id <N> --toggle`).
- Every `wezterm cli` call is logged to `%TEMP%\xvcpanel-mux.log` - check the last lines there if a pane action silently does nothing.

Quitting XVCpanel does not promise to close every external renderer. Stop active visuals with `s` before quitting.

## Resolume And Output Routing

The current bundled demos open windows. They do not yet contain real Spout sender code, even where an older manifest contains `"spout": true`. Installing the Spout2 DLL alone will not turn a visual into a sender.

For a working Resolume route on Windows:

1. Install [Spout2](https://spout.leadedge.com/).
2. Add a Spout addon or SDK integration to the renderer that owns the OpenGL/DirectX texture.
3. Render the visual into an FBO or texture.
4. Send that texture under a stable sender name.
5. In Resolume, add **Sources > Spout** and select that sender.
6. Add an `outputs` entry to the visual's `xvc.json` whose `run_cmd` enables Spout mode.

Example output configuration:

```json
"outputs": [
  {"name": "Preview", "protocol": "window"},
  {"name": "Resolume", "protocol": "spout", "run_cmd": "myvisual.exe --spout XVC-MyVisual"}
]
```

Configure which output a visual launches into in its `xvc.json` `outputs`; the `[w] [R] [v]` route buttons / `o` toggle the window, resolume, and preview routes. XVCpanel does not convert a window into Spout by itself.

Use NDI for network video. Use Syphon for a native macOS renderer.

## OSC Parameters And Modulation

XVCpanel sends standard OSC float messages over UDP. Controls appear only when a manifest declares parameters, and the renderer must listen on the same host/port and implement the addresses.

```json
"osc": {"host": "127.0.0.1", "port": 9001},
"parameters": [
  {"name": "Speed", "address": "/visual/speed", "min": 0.0, "max": 4.0, "default": 1.0},
  {"name": "Intensity", "address": "/visual/intensity", "min": 0.0, "max": 1.0, "default": 0.7}
]
```

Use brackets to choose a parameter, `-`/`=` to change it, and `m` to toggle the LFO. Declaring JSON fields without adding an OSC receiver to the visual does not change its rendering.

## Adding Any Visual

Create a folder anywhere under `library` and place `xvc.json` beside the source or executable. XVCpanel is command-based, so the implementation can use C++, Rust, Processing, GLSL, JavaScript, Python, TouchDesigner, Unreal, Unity, or another runtime.

```json
{
  "name": "My Visual",
  "framework": "custom",
  "build": "",
  "run": "python visual.py",
  "requires": ["python"],
  "tags": ["generative", "audio"],
  "description": "A controllable visual",
  "outputs": [
    {"name": "Preview", "protocol": "window"},
    {"name": "Resolume", "protocol": "spout", "run_cmd": "python visual.py --spout XVC-MyVisual"}
  ],
  "osc": {"host": "127.0.0.1", "port": 9001},
  "parameters": [
    {"name": "Speed", "address": "/visual/speed", "min": 0.0, "max": 4.0, "default": 1.0}
  ]
}
```

Supported framework labels are `openframeworks`, `nannou`, `processing`, `glsl`, `threejs`, `cinder`, `touchdesigner`, `vvvv`, `hydra`, `p5js`, `max`, `resolume-wire`, `notch`, `unity`, `unreal`, `godot`, `love2d`, `isf`, and `custom`. Labels organize the catalog only: XVCpanel runs the command declared in the manifest, so use the runtime's documented CLI or a `.bat` launcher. `run_cmd` is optional per output; without it, the top-level `run` command is used.

The practical VJ integrations still missing are renderer-side transport adapters, not panel-side labels: implement Spout/NDI/Syphon in the renderer that owns the GPU texture. Use OSC, MIDI-to-OSC, or the framework's own control API for live parameters.

`requires` contains executable names that must be discoverable through PATH. Use absolute commands when a runtime should not be added to PATH.

## Updating And Reinstalling

Update the repository and refresh the editable Python install:

```powershell
git pull
.\install.ps1 -NoLaunch
```

Update or repair supported runtimes:

```powershell
.\install.ps1 -InstallRuntimes -NoLaunch
```

The installer intentionally reuses existing `.tools` folders. To force a clean portable runtime download, delete only that runtime folder and rerun the command:

```powershell
Remove-Item .\.tools\processing -Recurse -Force
.\install.ps1 -InstallRuntimes -NoLaunch
```

To rebuild only the Python environment:

```powershell
Remove-Item .\.venv -Recurse -Force
.\install.ps1 -NoLaunch
```

## Troubleshooting

### PowerShell blocks `install.ps1`

Use the process-scoped bypass command; it does not change the machine-wide execution policy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -InstallRuntimes
```

### `Python 3.10+ was not found`

Install Python from [python.org](https://www.python.org/downloads/windows/), open a new terminal, and run `py -3 --version` or `python --version`.

### A row still says `MISSING: Processing.exe`, `cargo`, or `glslViewer`

1. Quit XVCpanel.
2. Run `.\install.ps1 -InstallRuntimes -NoLaunch` from the repository root.
3. Confirm the installer reports the tool as `ready`.
4. Relaunch with `.\.venv\Scripts\python.exe -m xvcpanel -d .`.

Do not launch an installed `xvcpanel` command from another directory unless you pass `-d C:\path\to\XVCpanel`; local `.tools` discovery is based on the supplied project root.

### GitHub downloads fail

Check the internet connection and whether a firewall, proxy, VPN, or GitHub rate limit blocks `api.github.com` or `github.com`. Delete a partially created runtime folder under `.tools` before retrying.

### Cargo build fails

Run `cargo build --release` manually inside `library\nannou\wave_mesh` to see the complete compiler output. Confirm that Windows Defender or a proxy is not blocking Cargo downloads.

### The visual starts and immediately shows `ERROR`

Run the corresponding manual diagnostic command from this README. XVCpanel intentionally keeps renderer output quiet during normal launch, while a direct terminal command exposes the full error.

### `Spout2 DLL not found - running in stub mode`

This warning is currently harmless for window output. The Python bridge is a placeholder; install and integrate Spout in the visual runtime when implementing Resolume output.

## CLI Reference

```powershell
.\.venv\Scripts\python.exe -m xvcpanel -d .
.\.venv\Scripts\python.exe -m xvcpanel --list -d .
.\.venv\Scripts\python.exe -m xvcpanel -v -d .
.\.venv\Scripts\python.exe -m xvcpanel -d C:\path\to\another-project
```

| Option | Purpose |
|---|---|
| `-d`, `--dir` | Project root or library path |
| `-l`, `--list` | List discovered visuals and exit |
| `-v`, `--verbose` | Enable debug logging |
| `--spout-name` | Set the placeholder Python bridge name; this does not create a renderer-side sender |

## Development Checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m compileall -q xvcpanel tests
```
