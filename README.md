# XVCpanel

Terminal visual mixer — browse, build, run, and switch between visual projects across multiple frameworks. Outputs to Resolume via Spout.

## Quick Start

```bash
git clone https://github.com/Reimonsk8/XVCpanel.git
cd XVCpanel
pip install -e .
python -m xvcpanel
```

## Prerequisites

### Python (required for the panel itself)

```bash
pip install textual
```

### Frameworks (install only what you need)

#### openFrameworks (particles + fluid demos)

1. Download from https://openframeworks.cc/download
2. Extract to `C:\openframeworks` (Windows) or `~/openframeworks` (Mac/Linux)
3. Set the environment variable or edit the Makefile:
   ```bash
   # Windows
   set OF_ROOT=C:\openframeworks

   # Mac/Linux
   export OF_ROOT=~/openframeworks
   ```
4. Install the Visual Studio project generators (Windows) or use `make` (Mac/Linux)

#### Nannou (wave mesh demo)

```bash
# Install Rust if you haven't
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify
cargo --version
```

#### Processing (flow field demo)

1. Download from https://processing.org/download
2. Install the CLI tool:
   ```bash
   # After installing Processing, add to PATH:
   # Windows: C:\Program Files\Processing
   # Mac: /Applications/Processing.app/Contents/MacOS
   ```

#### GLSL (warp shader demo)

```bash
# Install glslViewer
# Mac
brew install glslViewer

# Windows — download from https://github.com/patriciogonzalezvivo/glslViewer/releases
# Linux
cargo install glslViewer
```

## Usage

### Launch the TUI

```bash
python -m xvcpanel
```

### List all visuals (non-interactive)

```bash
python -m xvcpanel --list
```

### Point to a custom project root

```bash
python -m xvcpanel -d /path/to/your/visuals
```

### Verbose logging

```bash
python -m xvcpanel -v
```

## TUI Controls

| Key | Action |
|-----|--------|
| `↑↓` | Navigate visuals |
| `Enter` | Select / show description |
| `b` | Build selected visual |
| `r` | Run selected visual |
| `s` | Stop selected visual |
| `f` | Show all frameworks |
| `1` | Filter: openFrameworks |
| `2` | Filter: Nannou |
| `3` | Filter: GLSL |
| `4` | Filter: Processing |
| `/` | Search by name/tag |
| `Esc` | Clear search |
| `q` | Quit |

## Running Demos Manually

If you want to run a visual directly without the panel:

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

Press `F` for fullscreen, `ESC` to quit.

### Flow Field (Processing)

```bash
cd library/processing/flowfield
processing-java --sketch=$(pwd) --run
```

**Controls:** click+drag to inject, `F` fullscreen, `C` clear

## Adding Your Own Visuals

Each visual is a folder under `library/<framework>/<name>/` with an `xvc.json`:

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

### xvc.json fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Display name in the TUI |
| `framework` | yes | `openframeworks`, `nannou`, `processing`, `glsl`, `threejs`, `custom` |
| `build` | no | Build command (leave empty if no build step) |
| `run` | yes | Run command |
| `spout` | no | `true` if output goes to Spout for Resolume |
| `tags` | no | Array of tags for filtering |
| `description` | no | Shown when a visual is selected |

## Spout → Resolume

On Windows, visuals with `"spout": true` send their output via Spout2. To capture in Resolume:

1. Install Spout2 from https://spout.leadedge.com/
2. In Resolume, add a new **Spout** input
3. Select the sender name (matches the visual's window title)

On Mac, use **Syphon** instead (same concept, different protocol).

## Project Structure

```
XVCpanel/
├── library/                    # Visual projects by framework
│   ├── openframeworks/
│   │   ├── particles/          # Curl noise particles
│   │   │   ├── src/
│   │   │   │   ├── main.cpp
│   │   │   │   ├── ofApp.h
│   │   │   │   └── ofApp.cpp
│   │   │   ├── Makefile
│   │   │   └── xvc.json
│   │   └── fluid/              # Stable fluids sim
│   │       ├── src/
│   │       │   ├── main.cpp
│   │       │   ├── ofApp.h
│   │       │   └── ofApp.cpp
│   │       ├── Makefile
│   │       └── xvc.json
│   ├── nannou/
│   │   └── wave_mesh/          # Animated mesh
│   │       ├── src/main.rs
│   │       ├── Cargo.toml
│   │       └── xvc.json
│   ├── glsl/
│   │   └── warp/               # Domain warp shader
│   │       ├── warp.frag
│   │       ├── warp.vert
│   │       └── xvc.json
│   └── processing/
│       └── flowfield/          # Perlin flow field
│           ├── flowfield.pde
│           └── xvc.json
├── xvcpanel/                   # Python panel
│   ├── __init__.py
│   ├── __main__.py             # CLI entry point
│   ├── models/                 # Visual, Framework, VisualStatus
│   ├── loader/                 # Scanner + build/run runner
│   ├── spout/                  # Spout2 bridge
│   └── ui/                     # Textual TUI
├── pyproject.toml
└── README.md
```
