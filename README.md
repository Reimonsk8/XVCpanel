# XVCpanel

Terminal visual mixer — browse, build, run, and switch between visual projects across multiple frameworks. Outputs to Resolume via Spout.

![Futuristic TUI with split-panel layout, status columns, and neon styling](https://img.shields.io/badge/status-active-00e5ff?style=flat-square) ![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab?style=flat-square) ![Textual](https://img.shields.io/badge/TUI-Textual-00e5ff?style=flat-square)

## Quick Start

```powershell
git clone https://github.com/Reimonsk8/XVCpanel.git
cd XVCpanel
.\install.ps1
```

Or manual:

```bash
pip install -e .
python -m xvcpanel
```

## Prerequisites

### Python (required)

```bash
pip install textual
```

### Frameworks (install only what you need)

| Framework | Install | Demo |
|-----------|---------|------|
| **openFrameworks** | [openframeworks.cc/download](https://openframeworks.cc/download) → extract to `C:\openframeworks` | Particles, Fluid Sim |
| **Nannou** | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` | Wave Mesh |
| **Processing** | [processing.org/download](https://processing.org/download) → add to PATH | Flow Field |
| **GLSL** | [glslViewer releases](https://github.com/patriciogonzalezvivo/glslViewer/releases) | Warp Shader |

## Usage

```bash
python -m xvcpanel          # Launch TUI
python -m xvcpanel --list   # List all visuals
python -m xvcpanel -d /path # Custom project root
python -m xvcpanel -v       # Verbose logging
```

## TUI Controls

| Key | Action |
|-----|--------|
| `j` / `↓` | Move down |
| `k` / `↑` | Move up |
| `Enter` | Run selected visual |
| `b` | Build selected visual |
| `s` | Stop selected visual |
| `f` | Show all frameworks |
| `1` | Filter: openFrameworks |
| `2` | Filter: Nannou |
| `3` | Filter: GLSL |
| `4` | Filter: Processing |
| `/` | Search by name/tag |
| `Esc` | Clear search |
| `q` | Quit |

## Table Columns

| Column | Description |
|--------|-------------|
| **Status** | `○ idle` → `◉ BUILD` → `● LIVE` / `■ stopped` / `✗ error` |
| **Name** | Visual display name |
| **FW** | Framework abbreviation (oF, Nan, GLSL, Proc) |
| **Tags** | Filterable tags |
| **Spout** | `ON` if sends to Resolume |

## Preview Panel

Right panel shows full details for the selected visual:
- Name, framework, status
- Tags, description
- Build command, run command
- Spout status

## Running Demos Manually

### Curl Noise Particles (openFrameworks)

```bash
cd library/openframeworks/particles
make
./bin/particles
```

**Controls:** `P` pause, `F` fullscreen, `C` clear trails

### Fluid Sim Stable (openFrameworks)

```bash
cd library/openframeworks/fluid
make
./bin/fluid
```

**Controls:** click+drag to inject fluid, `C` clear, `F` fullscreen

### Wave Mesh (Nannou)

```bash
cd library/nannou/wave_mesh
cargo run --release
```

### Warp Shader (GLSL)

```bash
cd library/glsl/warp
glslViewer warp.frag -w 1920 -h 1080
```

**Controls:** `F` fullscreen, `ESC` quit

### Flow Field (Processing)

```bash
cd library/processing/flowfield
processing-java --sketch=$(pwd) --run
```

**Controls:** click+drag to inject, `F` fullscreen, `C` clear

## Adding Your Own Visuals

Create a folder under `library/<framework>/<name>/` with an `xvc.json`:

```json
{
  "name": "My Visual",
  "framework": "openframeworks",
  "build": "make",
  "run": "./bin/myvisual",
  "spout": true,
  "tags": ["particles", "gpu"],
  "description": "Description shown in the UI"
}
```

### xvc.json Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Display name in the TUI |
| `framework` | yes | `openframeworks`, `nannou`, `processing`, `glsl`, `threejs`, `custom` |
| `build` | no | Build command (leave empty if no build step) |
| `run` | yes | Run command |
| `spout` | no | `true` if output goes to Spout for Resolume |
| `tags` | no | Array of tags for filtering |
| `description` | no | Shown in preview panel |

## Spout → Resolume

On Windows, visuals with `"spout": true` send their output via Spout2.

1. Install Spout2 from https://spout.leadedge.com/
2. In Resolume, add a new **Spout** input
3. Select the sender name (matches the visual's window title)

On Mac, use **Syphon** instead (same concept, different protocol).

## Project Structure

```
XVCpanel/
├── library/                    # Visual projects by framework
│   ├── openframeworks/
│   │   ├── particles/          # Curl noise particles (8k GPU)
│   │   └── fluid/              # Stable fluids sim (128x128)
│   ├── nannou/
│   │   └── wave_mesh/          # Animated mesh with HSL
│   ├── glsl/
│   │   └── warp/               # Domain warp shader (fbm)
│   └── processing/
│       └── flowfield/          # 10k particle flow field
├── xvcpanel/                   # Python panel
│   ├── __init__.py
│   ├── __main__.py             # CLI entry point
│   ├── models/                 # Visual, Framework, VisualStatus
│   ├── loader/                 # Scanner + build/run runner
│   ├── spout/                  # Spout2 bridge
│   └── ui/                     # Textual TUI (split-panel, neon CSS)
├── install.ps1                 # One-shot install & run
├── pyproject.toml
└── README.md
```
