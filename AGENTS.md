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

## Livecoding

- `e`/`[edit]` opens the selected visual's source via `$EDITOR`/`$VISUAL`, else the bundled `.tools/neovim/nvim-win64/bin/nvim.exe`, else notepad. Console editors (vim/nvim/lvim/hx/micro/...) launch inside a new Windows Terminal window (`wt` resolved at `%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe`, off-PATH aliases not found via `which`).
- `g`/`[live]` toggles a 0.6 s mtime watcher (`_poll_live`). GLSL saves push hot-reload directly into the running sketch (the 3 `*_processing.pde` re-`loadShader()` on mtime change and keep the previous shader on compile error). Every other framework does stop → rebuild → relaunch (`reload_visual`) while the visual is running.
- Don't "simplify" the relaunch path into calling `run_visual` alone — it would spawn a duplicate process; `reload_visual` calls `stop_visual` first.

## Dev triptych (WezTerm)

- `dev.ps1` opens one WezTerm window with 2 panes: left = nvim editor, right = the xvcpanel TUI. The in-terminal preview pane is NOT pre-opened — toggle the route `[v]` (or `o`) in the panel; the panel then `wezterm cli split-pane --top`s a `preview.py` watcher for the selected visual, and `kill-pane`s it when toggled off or the selection changes (this WezTerm build has no `close-pane` subcommand). Runs must be started from the panel for frames to flow.
- Route is per-visual multi-toggle (`Visual.route`: `["window", "resolume", "preview"]`, defaults `["preview"]`), not a cyclic single output: buttons `[w] [R] [v]` in the action bar flip each sink independently. The panel auto-spawns the in-terminal preview pane at startup when the selected visual's route has `preview` on. `resolume` is a stub (transport TBD) — only `preview` changes runtime behavior today.
- Rendering bridge is filesystem-only: all 7 Processing visuals (the 3 GLSL `*_processing.pde` + flowfield/confetti/bouncing balls/sine waves) call `snapshotToFrame()` in `draw()` (gated to ~4 fps, `data/` auto-created) and save a 320x180 `data/frame.png`; `xvcpanel/preview.py` watches that file (pure-Python Kitty Graphics, no subprocess/imgcat — `WEZTERM_EXECUTABLE` points at wezterm-gui.exe which has no imgcat) and re-renders on mtime change, dropping to a banner ~6 s after the visual stops. Copy `snapshotToFrame()` into other Processing sketches to extend.
- Collapse/show/hide panes: `F9` (set in `wezterm.lua` via `TogglePaneZoomState`) zooms the focused pane, `F9` again restores the layout. Scripted: `wezterm cli zoom-pane --pane-id <N> --toggle`.
- Editor pop-out toggle: `[float]` in the action bar switches the whole layout to floating mode — the editor spawns into its own window (`wezterm cli spawn --new-window`) and closes the left pane; if the preview route is on it moves to its own window too. `[dock]` reverses it (`split-pane --left` respawns the editor, floating windows are `kill-pane`d, preview returns in-terminal). One button flips between multiplex and separate-window modes; every `wezterm cli` call is logged to `%TEMP%\xvcpanel-mux.log` for diagnosis.
- WezTerm runs from `.tools/wezterm` (provisioned by install.ps1); the panel resolves the CLI via PATH, then `WEZTERM_EXECUTABLE`'s sibling `wezterm.exe`, then the bundled `.tools/wezterm/*/wezterm.exe`, so pane actions work without any PATH setup in the panel pane.

## OSC

- Sender: `xvcpanel/controls/osc.py::send_float` — big-endian f32 with `,f` tag.
- Each Nannou visual embeds its own UDP receiver thread on a hardcoded port that must match its `xvc.json` `"osc": {"port"}`: wave_mesh 9002, starfield 9007, aurora 9008, particle_swarm 9009.
- Processing visuals (native `.pde` + GLSL sketches) embed the same stdlib-only `OscIn` thread: flowfield 9004, kaleidoscope 9005, neon tunnel 9006, warp 9003, confetti 9010, bouncing balls 9011, sine waves 9012. Ports must stay unique and match `xvc.json`.

## Spout

- Spout is a **stub**. `"spout": true` in manifests and `xvcpanel/spout/bridge.py` are placeholders. Do not implement real Spout sending from Python; renderers must implement their own sender (see README).

## Conventions

- Conventional Commits with short subjects (`fix:`, `feat:`, `chore:`).
- `xvcpanel/` is installed editable (`pip install -e .`) — Python edits apply immediately, no reinstall.
- Don't commit tooling state files (e.g. `.opencode/goals/**/owner.json`). Setup/install belongs in `install.ps1` (`.venv`, `.tools`, runtimes are gitignored).