# AGENTS.md

Windows-first TUI that scans `library/**/xvc.json` for visual projects, builds/launches them, and sends OSC floats from Textual. Python app lives in `xvcpanel/`; each bundled visual is a self-contained project under `library/`. Only runtime dep is Textual; OSC is stdlib-only (`socket`+`struct`, no python-osc).

## Verify

- Health check (run before push): `python test_health.py`
- Unit tests: `.venv\Scripts\python.exe -m unittest discover -s tests`
- Both must pass. `tests/test_ui.py` asserts >= 8 visuals and `test_health.py:65` >= 8 — adding/removing a bundled visual means updating both counts.
- The `Spout2 DLL not found - running in stub mode` stderr warning is expected and harmless.

## Windows footguns

- Child processes are launched via a generated `.bat` that sets a minimal `PATH` (`_minimal_path()` in `xvcpanel/loader/runner.py`) because `subprocess.run` with a list won't find cargo/Processing/glslViewer on Windows. Never "simplify" this away.
- Inline `python -c "..."` breaks on cmd/PowerShell quoting — write a temp `.py` file instead.
- `rtk` is used for git; normal git works too.

## Visual runtime gotchas (hard-earned)

- **Nannou 0.19 is pinned** in all 4 visuals. `nannou::app::Builder::new(model).size(w,h).run()` silently creates NO window and the app exits in ~0.3s on Windows. Correct pattern: `nannou::app(model).update(update).run()` and create the window inside `model(app: &App)` via `app.new_window().size(1920,1080).view(view).build().unwrap()`. All 4 visuals already use this — preserve it.
- **Do not bump nannou to 0.20** — it is a Bevy rewrite with a completely different `Builder`/`Entity` API (no `hsla`, no `Update`/`Frame`, etc.); migrating 4 visuals is a large risky rewrite that the 0.19 window bug does not require.
- **Processing**: `Processing.exe cli --sketch=<ABSOLUTE path> --run` — a relative sketch path fails and `--run` must be the last argument.
- **glslViewer is broken on Windows** (FFmpeg DLL issues); the `*_processing` GLSL sketches are the working path. Treat glslViewer bugs as known, not something to fix.
- **openFrameworks visuals are intentionally blocked** (`requires: ["openFrameworks"]`, needs `make`/MSYS2 + `OF_ROOT`); the `ready()` gate in `tui.py:303` prevents launching. Manual setup only.

## OSC

- Sender: `xvcpanel/controls/osc.py::send_float` — big-endian f32 with `,f` tag.
- Each Nannou visual embeds its own UDP receiver thread on a hardcoded port that must match its `xvc.json` `"osc": {"port"}`: wave_mesh 9002, starfield 9007, aurora 9008, particle_swarm 9009.

## Spout

- Spout is a **stub**. `"spout": true` in manifests and `xvcpanel/spout/bridge.py` are placeholders. Do not implement real Spout sending from Python; renderers must implement their own sender (see README).

## Conventions

- Conventional Commits with short subjects (`fix:`, `feat:`, `chore:`).
- `xvcpanel/` is installed editable (`pip install -e .`) — Python edits apply immediately, no reinstall.
- Don't commit tooling state files (e.g. `.opencode/goals/**/owner.json`). Setup/install belongs in `install.ps1` (`.venv`, `.tools`, runtimes are gitignored).