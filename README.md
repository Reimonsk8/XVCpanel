# XVCpanel

Windows-first live control surface for code visuals. Browse projects from any language, build and run them, switch their configured output route, and control manifest-exposed OSC parameters with manual values or an LFO.

XVCpanel launches renderers; rendering and video transport stay in each renderer's graphics process. This means a visual must implement its own Spout, NDI, Syphon, or window output. The panel never labels a manifest flag as verified video output.

## Quick Start

Install Python 3.10+, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The script creates `.venv`, installs all Python dependencies, checks optional visual tools, and launches the app. For installation without launch:

```powershell
.\install.ps1 -NoLaunch
.\.venv\Scripts\python.exe -m xvcpanel -d .
```

Install the supported optional runtimes automatically without administrator access:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -InstallRuntimes
```

This installs Rust/Nannou, portable Processing, and portable glslViewer under `.tools`. XVCpanel discovers them automatically, including after reopening the terminal. Processing is roughly a 500 MB download. Re-running the command is safe and skips existing portable tools.

Visual frameworks are optional. Install only those used by your projects:

| Runtime | Windows setup |
|---|---|
| openFrameworks | Manual: [openframeworks.cc/download](https://openframeworks.cc/download) plus its matching Visual Studio toolchain |
| Nannou / Rust | Automatic with `-InstallRuntimes` |
| Processing | Automatic portable install with `-InstallRuntimes` |
| GLSL | Automatic portable glslViewer/FFmpeg install with `-InstallRuntimes` |
| Any other runtime | Put its executable on PATH or use an absolute command in `xvc.json` |

## Controls

| Key | Action |
|---|---|
| `j` / `Down`, `k` / `Up` | Select visual |
| `Enter` | Build if needed and run selected route |
| `b`, `s` | Build, stop |
| `o` | Switch configured output route |
| `[` / `]` | Select exposed parameter |
| `-` / `=` | Decrease / increase parameter |
| `m` | Toggle a 0.25 Hz sine LFO on the parameter |
| `1`-`4`, `f` | Filter frameworks / show all |
| `/`, `Esc` | Search / clear search |
| `p`, `q` | Toggle details / quit |

## Add Any Visual

XVCpanel is command-based, so the source can be C++, Rust, Processing, GLSL, JavaScript, Python, TouchDesigner, Unreal, Unity, or another runtime. Add `xvc.json` beside the project:

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
    {"name": "Resolume", "protocol": "spout", "run_cmd": "python visual.py --spout XVC-MyVisual"},
    {"name": "Network", "protocol": "ndi", "run_cmd": "python visual.py --ndi XVC-MyVisual"}
  ],
  "osc": {"host": "127.0.0.1", "port": 9001},
  "parameters": [
    {"name": "Speed", "address": "/visual/speed", "min": 0.0, "max": 4.0, "default": 1.0},
    {"name": "Intensity", "address": "/visual/intensity", "min": 0.0, "max": 1.0, "default": 0.7}
  ]
}
```

`run_cmd` is optional per output; without it, the top-level `run` command is used. XVCpanel sends parameters as standard OSC float messages. The visual must listen on the declared UDP port and implement each address.

Supported framework labels are `openframeworks`, `nannou`, `processing`, `glsl`, `threejs`, `cinder`, and `custom`. Use `custom` for every other language; it does not limit the command or runtime.

## Resolume

For lowest-latency local Windows video, implement a Spout sender in the visual process that owns the framebuffer:

1. Install [Spout2](https://spout.leadedge.com/) and the appropriate runtime addon or SDK.
2. Render into an FBO/texture in the visual.
3. Send that texture under a stable sender name.
4. Add a Spout source with that sender name in Resolume.
5. Add an `outputs` entry whose command enables that sender.

Use NDI for network video. Use Syphon for a native macOS renderer. These transports cannot be made universal by the Python panel because GPU textures belong to the renderer's graphics context.

## CLI

```powershell
.\.venv\Scripts\python.exe -m xvcpanel
.\.venv\Scripts\python.exe -m xvcpanel --list
.\.venv\Scripts\python.exe -m xvcpanel -d C:\path\to\project
```

The bundled examples demonstrate their visual frameworks. Their current manifests intentionally expose only window output until runtime-local OSC and Spout implementations are added.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```
