# XVCpanel Plan

Working roadmap. Status icons: `[done] [doing] [todo] [decide]`.

## 1. GLSL visuals must behave like the rest (open a window, be controllable)

`[done]` DECIDED: **delete the 3 broken glslViewer manifests** (`glsl/kaleidoscope`, `glsl/neon_tunnel`, `glsl/warp`) and **relabel their `*_processing` twins as framework `glsl`** (they ARE shaders; they render via Processing.exe) so the "3:GLSL" filter shows working, controllable visuals. Also set `requires: ["Processing.exe"]` on them so a missing runtime shows `NEED` instead of failing at launch.
- Impact: removes 3 duplicate/broken rows; tests count changes (also enables #5).

## 2. Theme: dark futuristic, no navy

`[done]` Replace the navy palette in `tui.py` CSS (`#11152a`, `#0b1020`, `#0a0e17`, `#111827`, `#1e3a5f`, `#1a2744`) with a near-black obsidian/charcoal base + one neon accent. Header/borders get the accent; selected rows + status bar use it. Preserve `[bold magenta]`/cyan text accents that indicate "live/control" semantics.
- Base: `#050507` screen, `#0b0c10` panels, `#1a1c24` borders (no blue tint).
- Accent: DECIDED **neon green `#00ff9d`**.
- Ship status: `[done]`

## 3. Mouse + keyboard live controls (per-control LFO)

`[done]` Textual 8.2.8 has **no built-in Slider** — add a small custom drag-to-scrub `Slider` widget (mouse down/move/up + click), ~40 lines, self-contained. (`xvcpanel/ui/slider.py`)

Per-parameter control row (in the preview/live panel, mouse-driven):
- `Name` · drag-slider for value · value readout
- `Switch` LFO on/off
- LFO speed (small slider), Hz
- Curve `Select`: sine / triangle / square / ramp
- Row is clickable to select the control (mirrors `[`/`]`)

Keyboard mirrors (all existing bindings stay):
- `[` `]` select parameter · `-` `=` value
- `m` toggle LFO on selected control
- LFO speed: `,`/`.` · curve cycle: `c`

Model/engine:
- `Parameter` gains `lfo_rate` (Hz, default 0.25) and `lfo_curve` (enum). `done`
- `_tick_modulation` computes per-parameter phase by curve+rate (replaces one global 0.25 Hz sine). `done`
- Bottom "LIVE" status shows running visuals: name · pid · output route · run time. `done`
- Ship status: `[done]`

## 4. Bottom bar: real working controls + status

`[done]` Replace the current text-only help `Label` (tui.py:208) — it looks like buttons but is not clickable (why Build/Route/Stop "do nothing").
- Docked bottom bar with real `Button` widgets: **Build · Run · Stop · Route · Param ◀ ▶ · LFO · Speed · Curve** (each also still bound to its key).
- Implement what "does nothing" today:
  - `Build`: now wired to same `_build` action with visible result. `done`
  - `Stop`: `s` works; wired to button. `done`
  - `Route`: DECIDED — when RUNNING, switching output **stops + relaunches** with the new `run_cmd` (taskkill tree, then run). When idle, just marks route for next launch. `done`
- Status strip: count visuals · how many LIVE · names of running ones · route · missing-tool alerts. `done`
- Ship status: `[done]`

## 5. Fix the failing tests (catalog grew 8 → 13)

`[done]` `tests/test_ui.py:14` now asserts >= 8 (catalog had 13 vs a stale 8). Fold in GLSL change (#1) — both checks green again.

## 6. Cleanup (small)

`[done]`
- Drop stale `"spout": true` flags from manifests (Spout is a stub; flags are misleading — README already says so).
- Ensure every Processing-based manifest declares `requires: ["Processing.exe"]`.
- (Both folded into #1's manifest edits.)

## 7. Static override + UI polish

`[done]`
- Clickable `[Close]` button in the action bar exits the app.
- All emoji glyphs removed from buttons; ASCII bracket labels (`[Run]` `[Stop]` `[Build]` `[<]` `[>]` `[Close]`).
- Bottom bar spans full width with live context: `Visual: <name>` · `Param: <name>`.
- Curve dropdown made prominent (`width: 20`) under "curve" label in SELECTED CONTROL.
- Manual numeric entry: `Input` in the deck — Enter applies a static value, disables LFO, and grays out (opacity 0.35) the LFO rate slider + curve dropdown.
- Bug fixes: `enter` binding was `priority=True` and swallowed `Input.Submitted` (and typed Enter ran the visual) — row-run now happens via `DataTable.RowSelected`; value/LFO keys (`.` `,` `-` `=` `m` `c`) are no longer priority so typing in inputs works. Value-slider equality guard prevents programmatic tick sync from silently turning LFO off.
- Jump-to-control dropdown: `all controls ▾` Select at the top of SELECTED CONTROL lists every parameter of the current visual; picking one switches to it directly (no step-by-step needed). Planted as `on_controls_menu` + `#controls-menu`.

## 8. Livecoding: edit source, see it update

`[doing]`
- `e` / `[edit]` opens the visual's source in `$EDITOR`/`$VISUAL`/notepad (resolved via `Visual.source_path`, framework-aware).
- `g` / `[live]` toggles a 0.6 s mtime watcher: GLSL saves hot-reload in the sketch window (sketches re-`loadShader` on mtime change, keeping the old shader on compile error); all other frameworks stop + rebuild + relaunch if the visual is running.
- GLSL hot reload planted in `kaleidoscope_processing.pde`, `neon_tunnel_processing.pde`, `warp_processing.pde`. Shader edits are instant; `.pde`/`.rs` edits are restart-on-save (1–3 s).
- Action bar decluttered: dropped keyboard-duplicate buttons (LFO / r- / r+ / wv) and the two ctx labels (folded into the status bar) so all pills fit at 120 columns.

## 9. Dev triptych: everything in one WezTerm window

`[done]`
- `dev.ps1` opens one WezTerm window with 2 panes: left nvim, right xvcpanel TUI. The in-terminal preview pane is NOT created up front — the panel lazily `wezterm cli split-pane --top`s a `preview.py` watcher for the selected visual, and `close-pane`s it on toggle-off/selection change (`Visual.route` multi-toggle, buttons `[w] [R] [v]`, `o` = preview; `resolume` is a stub).
- Preview rendering is pure-Python Kitty Graphics (`xvcpanel/preview.py` — no timg/wezterm-imgcat), mtime watch, banner ~6 s after the visual stops.
- Frames flow over the filesystem only: all 7 Processing visuals call `snapshotToFrame()` (~4 fps scaled 320x180 `data/frame.png`, `data/` auto-created); `Visual.route` preview watches the selected visual's own `data/frame.png`.
- Pane collapse/show/hide: `F9` (wezterm.lua `TogglePaneZoomState`) zooms the focused pane, `F9` again restores; scriptable via `wezterm cli zoom-pane --pane-id <N> --toggle`.
- WezTerm provisioned into `.tools/wezterm` by install.ps1.