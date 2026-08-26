# XVCpanel

Terminal visual mixer — browse, build, run, and switch between visual projects across multiple frameworks. Outputs to Resolume via Spout.

## Setup

```bash
pip install -e .
```

## Usage

```bash
# Launch the TUI
xvcpanel

# List all visuals (non-interactive)
xvcpanel --list

# Point to a custom project root
xvcpanel -d /path/to/project
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

## Adding Visuals

Each visual project is a folder under `library/<framework>/<name>/` with an `xvc.json`:

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

### Supported frameworks

| Framework | Build | Run |
|-----------|-------|-----|
| `openframeworks` | `make` | `./bin/<name>` |
| `nannou` | `cargo build --release` | `cargo run --release` |
| `processing` | — | `processing-java --sketch=$(pwd) --run` |
| `glsl` | — | `glslViewer <shader> -w 1920 -h 1080` |
| `threejs` | `npm run build` | `npm start` |
| `custom` | user-defined | user-defined |

## Spout Output

On Windows, visuals with `"spout": true` can be captured by Resolume as a Spout input.

## Project Structure

```
XVCpanel/
├── library/              # Visual projects by framework
│   ├── openframeworks/
│   ├── nannou/
│   ├── glsl/
│   └── processing/
├── xvcpanel/
│   ├── __main__.py       # CLI entry point
│   ├── models/           # Data models (Visual, Framework)
│   ├── loader/           # Library scanner + build/run runner
│   ├── spout/            # Spout2 bridge
│   └── ui/               # Textual TUI
├── pyproject.toml
└── README.md
```
