from __future__ import annotations

import math
import os
import subprocess
import time
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Input, Label, Rule, Select, Static, Switch

from xvcpanel.controls.osc import send_float
from xvcpanel.loader.runner import build_visual, run_visual, stop_visual
from xvcpanel.loader.scanner import scan_library
from xvcpanel.models.visual import Framework, Visual, VisualStatus
from xvcpanel.spout.bridge import SpoutBridge
from xvcpanel.ui.slider import Slider

if TYPE_CHECKING:
    from pathlib import Path
    from xvcpanel.models.visual import Parameter

FW_SHORT = {
    Framework.OPENFRAMEWORKS: "oF",
    Framework.NANNOU: "Nan",
    Framework.PROCESSING: "Proc",
    Framework.GLSL: "GLSL",
    Framework.THREEJS: "3.js",
    Framework.CINDER: "Cin",
    Framework.TOUCHDESIGNER: "TD",
    Framework.VVVV: "vvvv",
    Framework.HYDRA: "Hydra",
    Framework.P5JS: "p5",
    Framework.MAX: "Max",
    Framework.RESOLUME_WIRE: "Wire",
    Framework.NOTCH: "Notch",
    Framework.UNITY: "Unity",
    Framework.UNREAL: "Unreal",
    Framework.GODOT: "Godot",
    Framework.LOVE2D: "Love",
    Framework.ISF: "ISF",
    Framework.CUSTOM: "???",
}

STATUS = {
    VisualStatus.IDLE: "[dim]IDLE[/]",
    VisualStatus.BUILDING: "[yellow]BUILD[/]",
    VisualStatus.RUNNING: "[bold green]LIVE[/]",
    VisualStatus.ERROR: "[bold red]ERROR[/]",
    VisualStatus.STOPPED: "[dim]STOP[/]",
}

CURVES = ("sine", "triangle", "square", "ramp")


class ParameterDeck(Static):
    """Mouse-driven controls for the selected parameter: value, LFO, rate, curve."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="deck-jump"):
            yield Label("all controls", classes="deck-label")
            yield Select([], id="controls-menu", allow_blank=True, prompt="pick a control")
        with Horizontal(id="deck-row"):
            yield Label(id="deck-name")
            yield Label(id="deck-value")
        yield Slider(0.0, 1.0, 0.5, id="value-slider")
        with Horizontal(id="deck-lfo"):
            yield Label(" LFO", classes="deck-label")
            yield Switch(id="lfo-switch")
            yield Label("rate", classes="deck-label")
            yield Slider(0.05, 4.0, 0.25, id="rate-slider")
            yield Label(id="rate-readout")
        with Horizontal(id="deck-meta"):
            yield Label("curve", classes="deck-label")
            yield Select([(name.capitalize(), name) for name in CURVES], value="sine", id="curve-select", compact=True, allow_blank=False)
            yield Label("set", classes="deck-label")
            yield Input(placeholder="numeric value + Enter = static", id="manual-input")

    def update_for(self, vis: Visual | None, index: int) -> None:
        if not vis or not vis.parameters or index >= len(vis.parameters):
            self.add_class("hidden")
            return
        self.remove_class("hidden")
        p = vis.parameters[index]
        menu = self.query_one("#controls-menu", Select)
        menu.set_options([(p.name, i) for i, p in enumerate(vis.parameters)])
        menu.value = index
        slider = self.query_one("#value-slider", Slider)
        slider.minimum = p.minimum
        slider.maximum = p.maximum
        slider.value = p.value
        self.query_one("#deck-name", Label).update(f" {p.name}")
        self.query_one("#deck-value", Label).update(f"{p.value:7.3f}")
        self.query_one("#lfo-switch", Switch).value = p.lfo
        rate = self.query_one("#rate-slider", Slider)
        rate.value = p.lfo_rate
        self.query_one("#rate-readout", Label).update(f"{p.lfo_rate:4.2f}Hz")
        self.query_one("#curve-select", Select).value = p.lfo_curve
        self.query_one("#manual-input", Input).value = f"{p.value:g}"
        self._set_static(not p.lfo)

    def refresh_values(self, vis: Visual | None, index: int) -> None:
        if not vis or not vis.parameters or index >= len(vis.parameters):
            return
        p = vis.parameters[index]
        self.query_one("#controls-menu", Select).value = index
        self.query_one("#value-slider", Slider).value = p.value
        self.query_one("#deck-value", Label).update(f"{p.value:7.3f}")
        self.query_one("#lfo-switch", Switch).value = p.lfo
        self.query_one("#rate-readout", Label).update(f"{p.lfo_rate:4.2f}Hz")
        self._set_static(not p.lfo)

    def _set_static(self, static: bool) -> None:
        self.query_one("#rate-slider", Slider).set_class(static, "static")
        self.query_one("#curve-select", Select).set_class(static, "static")


class PreviewPanel(Static):
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview-inner"):
            yield Label("[bold #8a93a6]NAME[/]", id="pv-name-label")
            yield Label("--", id="pv-name")
            yield Rule()
            yield Label("[bold #8a93a6]OUTPUT ROUTE[/]", id="pv-output-label")
            yield Label("--", id="pv-output")
            yield Rule()
            yield Label("[bold #8a93a6]LIVE CONTROLS[/]", id="pv-controls-label")
            with Vertical(id="controls-list"):
                yield Label("[dim]No parameters declared in xvc.json[/]", id="controls-empty")
            yield Label("[bold #8a93a6]SELECTED CONTROL[/]", id="pv-deck-label")
            yield ParameterDeck(id="param-deck")
            yield Rule()
            yield Label("[bold #8a93a6]FRAMEWORK[/]", id="pv-fw-label")
            yield Label("--", id="pv-fw")
            yield Rule()
            yield Label("[bold #8a93a6]TAGS[/]", id="pv-tags-label")
            yield Label("--", id="pv-tags")
            yield Rule()
            yield Label("[bold #8a93a6]DESCRIPTION[/]", id="pv-desc-label")
            yield Label("--", id="pv-desc")
            yield Rule()
            yield Label("[bold #8a93a6]REQUIRES[/]", id="pv-requires-label")
            yield Label("--", id="pv-requires")
            yield Rule()
            yield Label("[bold #8a93a6]INSTALL[/]", id="pv-install-label")
            yield Label("[dim]--[/]", id="pv-install")
            yield Rule()
            yield Label("[bold #8a93a6]BUILD[/]", id="pv-build-label")
            yield Label("[dim]--[/]", id="pv-build")
            yield Rule()
            yield Label("[bold #8a93a6]RUN[/]", id="pv-run-label")
            yield Label("[dim]--[/]", id="pv-run")

    def update_visual(self, vis: Visual | None, parameter_index: int = 0) -> None:
        self._update_info(vis)
        self._update_context(vis, parameter_index)
        clist = self.query_one("#controls-list", Vertical)
        clist.remove_children()
        if vis and vis.parameters:
            for index, p in enumerate(vis.parameters):
                clist.mount(Button(self._row_label(index, p), classes="param-row"))
        else:
            clist.mount(Label("[dim]No parameters declared in xvc.json[/]"))
        self.query_one("#param-deck", ParameterDeck).update_for(vis, parameter_index)

    def _update_context(self, vis: Visual | None, parameter_index: int) -> None:
        p = None
        if vis and vis.parameters:
            p = vis.parameters[parameter_index % len(vis.parameters)]
        vis_name = f"[bold]{vis.name}[/]" if vis else "--"
        param_name = f"[bold]{p.name}[/]" if p else "--"
        self.app.query_one("#status-bar", Label).update(f" {vis_name} · {param_name}")

    def refresh_values(self, vis: Visual | None, parameter_index: int = 0) -> None:
        if not vis:
            return
        for index, (btn, p) in enumerate(zip(self.query(".param-row"), vis.parameters)):
            btn.label = self._row_label(index, p)
        self.query_one("#param-deck", ParameterDeck).refresh_values(vis, parameter_index)

    def _row_label(self, index: int, p: "Parameter") -> str:
        lfo = " [bold #00ff9d]~LFO[/]" if p.lfo else ""
        return f"  {p.name:<16} [bold white]{p.value:7.3f}[/]{lfo}"

    def _update_info(self, vis: Visual | None) -> None:
        ids = ["pv-name", "pv-output", "pv-fw", "pv-tags", "pv-desc", "pv-requires", "pv-install", "pv-build", "pv-run"]
        if vis is None:
            for i in ids:
                self.query_one(f"#{i}", Label).update("[dim]--[/]")
            return
        self.query_one("#pv-name", Label).update(f"[bold white]{vis.name}[/]")
        output = vis.output
        configured = "[green]CONFIGURED[/]" if output.protocol == "window" else "[yellow]APP-SIDE[/]"
        self.query_one("#pv-output", Label).update(
            f"[bold #8a93a6]{output.name}[/]  [dim]{output.protocol.upper()}[/]  {configured}\n"
            "[dim]o / Route: switch output · transport runs inside the visual[/]"
        )
        self.query_one("#pv-fw", Label).update(f"[bold #8a93a6]{vis.framework.value}[/]")
        self.query_one("#pv-tags", Label).update(
            " ".join(f"[#aeb6c6 on #161a24] {t} [/]" for t in vis.tags) if vis.tags else "[dim]none[/]"
        )
        self.query_one("#pv-desc", Label).update(vis.description or "[dim]no description[/]")

        missing = vis.missing_deps()
        if not vis.requires:
            self.query_one("#pv-requires", Label).update("[dim]none[/]")
        elif not missing:
            self.query_one("#pv-requires", Label).update(f"[green]{', '.join(vis.requires)}[/]")
        else:
            self.query_one("#pv-requires", Label).update(
                f"[green]{', '.join(r for r in vis.requires if r not in missing)}[/]"
                f" [red]MISSING:[/]{', '.join(missing)}"
            )

        self.query_one("#pv-install", Label).update(vis.install_hint or "[dim]--[/]")
        self.query_one("#pv-build", Label).update(
            f"[green]{vis.build_cmd}[/]" if vis.build_cmd else "[dim]no build step[/]"
        )
        self.query_one("#pv-run", Label).update(
            f"[green]{vis.run_cmd}[/]" if vis.run_cmd else "[dim]no run command[/]"
        )


class XVCpanel(App):
    CSS = r"""
    Screen { background: #050507; }
    .hidden { display: none; }
    #topbar { dock: top; height: 3; background: #0b0c10; border-bottom: tall #1a1c24; padding: 0 1; align-vertical: middle; align-horizontal: right; }
    #app-title { width: 1fr; color: #8a93a6; text-style: bold; }
    #btn-close { height: 1; min-width: 7; border: none; background: #12141a; color: #ff4d5e; }
    #btn-close:hover { background: #2a1518; color: #ff5b6b; }
    #search-box { dock: top; height: 3; background: #0b0c10; border-bottom: tall #1a1c24; padding: 0 2; align-vertical: middle; }
    #search-input { background: #0d0f14; border: tall #262a33; color: #dfe6ee; width: 100%; }
    #search-input:focus { border: tall #00ff9d; }
    #main-split { height: 1fr; }
    #list-panel { width: 58%; border-right: tall #1a1c24; background: #09090c; }
    #list-panel.wide { width: 100%; border-right: none; }
    #visual-table { background: #09090c; }
    #visual-table > .datatable--cursor { background: #12201a; color: #00ff9d; }
    #preview-panel { width: 42%; background: #0b0c10; padding: 1 2; border-left: tall #1a1c24; }
    #preview-panel.hidden { display: none; }
    #preview-inner { height: 1fr; }
    #preview-inner Rule { color: #1a1c24; }
    #status-bar { width: 100%; height: 1; background: #0b0c10; color: #8a93a6; padding: 0 1; }
    #bottom-dock { dock: bottom; width: 100%; height: 4; background: #0b0c10; }
    #action-bar { width: 100%; height: 3; background: #0b0c10; border-top: tall #1a1c24; padding: 0 1; align-horizontal: left; align-vertical: middle; }
    #action-bar Button { margin: 0 1; min-width: 7; height: 1; border: none; background: #12141a; color: #8a93a6; padding: 0 2; }
    #action-bar Button:hover { background: #1a2330; color: #00ff9d; }
    #action-bar #btn-stop { color: #ff4d5e; }
    #action-bar #btn-stop:hover { color: #ff5b6b; background: #2a1518; }
    #action-bar #btn-live.active { color: #00ff9d; background: #12201a; }
    #action-bar Label { color: #5a6077; height: 1; margin: 0 1; }
    #controls-list Button.param-row { height: 1; width: 1fr; border: none; background: transparent; color: #dfe6ee; padding: 0 1; align-horizontal: left; }
    #controls-list Button.param-row:hover { background: #0d0f14; }
    #param-deck { border: tall #1a1c24; background: #0d0f14; padding: 0 1; margin-top: 1; }
    #param-deck.hidden { display: none; }
    #deck-jump, #deck-row, #deck-lfo, #deck-meta { height: 3; align-vertical: middle; align-horizontal: left; }
    #controls-menu { width: 1fr; }
    #deck-name { color: #00ff9d; text-style: bold; width: 1fr; }
    #deck-value { color: #dfe6ee; width: 12; text-align: right; }
    .deck-label { color: #8a93a6; min-width: 10; margin: 0 2 0 0; }
    #deck-lfo #rate-readout { color: #00ff9d; width: 7; }
    #value-slider { width: 1fr; height: 3; }
    #rate-slider { width: 22; height: 3; margin-right: 2; }
    #rate-slider.static, #curve-select.static { opacity: 0.35; }
    #curve-select { width: 20; }
    #manual-input { width: 1fr; height: 3; background: #0b0c10; color: #dfe6ee; border: tall #262a33; margin: 0 0 1 0; }
    #manual-input:focus { border: tall #00ff9d; }
    Switch { background: #262a33; border: tall #1a1c24; }
    Switch > .switch--button { color: #ff4d5e; }
    Switch.on > .switch--button { color: #00ff9d; }
    """

    BINDINGS = [
        Binding("j,down", "cursor_down", "down", show=True, priority=True),
        Binding("k,up", "cursor_up", "up", show=True, priority=True),
        Binding("b", "build_visual", "Build", show=True, priority=True),
        Binding("s", "stop_visual", "Stop", show=True, priority=True),
        Binding("o", "next_output", "Output", show=True, priority=True),
        Binding("left_square_bracket", "previous_parameter", "Control", show=False, priority=True),
        Binding("right_square_bracket", "next_parameter", "Control", show=False, priority=True),
        Binding("minus", "decrease_parameter", "Value", show=False),
        Binding("equals_sign", "increase_parameter", "Value", show=False),
        Binding("m", "toggle_lfo", "Modulate", show=True),
        Binding("comma", "rate_down", "LFO −", show=False),
        Binding("period", "rate_up", "LFO +", show=False),
        Binding("c", "cycle_curve", "Curve", show=False),
        Binding("e", "open_source", "Edit", show=True, priority=True),
        Binding("g", "toggle_live", "Live", show=True),
        Binding("p", "toggle_preview", "Preview", show=True, priority=True),
        Binding("f", "filter_all", "All", show=True, priority=True),
        Binding("1", "filter_of", "oF", show=True, priority=True),
        Binding("2", "filter_nannou", "Nan", show=True, priority=True),
        Binding("3", "filter_glsl", "GLSL", show=True, priority=True),
        Binding("4", "filter_proc", "Proc", show=True, priority=True),
        Binding("slash", "focus_search", "/", show=False, priority=True),
        Binding("escape", "clear_search", "Esc", show=False, priority=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    TITLE = " XVCpanel "
    SUB_TITLE = "live visual control surface"

    def __init__(self, library_path: Path, spout: SpoutBridge | None = None) -> None:
        super().__init__()
        self.library_path = library_path
        self.visuals: list[Visual] = []
        self.spout = spout or SpoutBridge()
        self.active_filter: Framework | None = None
        self.search_query: str = ""
        self.preview_visible: bool = True
        self.parameter_index: int = 0
        self.live_mode: bool = False
        self._live_source: Path | None = None
        self._live_mtime: float = 0.0

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Label(" XVCpanel ", id="app-title")
            yield Button(r"\[X\]", id="btn-close")
        with Vertical(id="search-box"):
            yield Input(placeholder=" search visuals...", id="search-input")
        yield Label("", id="active-filter", classes="hidden")
        with Horizontal(id="main-split"):
            with Vertical(id="list-panel"):
                yield DataTable(cursor_type="row", id="visual-table")
            with Vertical(id="preview-panel"):
                yield PreviewPanel(id="preview")
        with Vertical(id="bottom-dock"):
            yield Label(id="status-bar")
            with Horizontal(id="action-bar"):
                yield Button(r"\[Run\]", id="btn-run")
                yield Button(r"\[Stop\]", id="btn-stop")
                yield Button(r"\[Build\]", id="btn-build")
                yield Button(r"\[edit\]", id="btn-edit")
                yield Button(r"\[live\]", id="btn-live")
                yield Button("Route: --", id="btn-route")
                yield Button(r"\[<\]", id="btn-prev", classes="mini")
                yield Button(r"\[>\]", id="btn-next", classes="mini")

    def on_mount(self) -> None:
        self._bootstrap_path()
        table = self.query_one("#visual-table", DataTable)
        table.add_columns("State", "Name", "FW", "Output", "Controls", "Tags")
        self.visuals = scan_library(self.library_path)
        self._refresh()
        self.set_interval(0.05, self._tick_modulation)
        self.set_interval(0.6, self._poll_live)
        table.focus()

    def _bootstrap_path(self) -> None:
        import os
        import platform
        from pathlib import Path
        sep = ";" if platform.system() == "Windows" else ":"
        tools = self.library_path.parent / ".tools"
        if tools.is_dir():
            for exe in tools.rglob("glslViewer*" if platform.system() == "Windows" else "glslViewer"):
                if exe.is_file():
                    s = str(exe.parent)
                    if s not in os.environ["PATH"]:
                        os.environ["PATH"] = f"{s}{sep}{os.environ['PATH']}"
            for exe in tools.rglob("Processing.exe"):
                if exe.is_file():
                    s = str(exe.parent)
                    if s not in os.environ["PATH"]:
                        os.environ["PATH"] = f"{s}{sep}{os.environ['PATH']}"
        cargo_bin = Path.home() / ".cargo" / "bin"
        if cargo_bin.is_dir():
            d = str(cargo_bin)
            if d not in os.environ["PATH"]:
                os.environ["PATH"] = f"{d}{sep}{os.environ['PATH']}"

    def _filtered(self) -> list[Visual]:
        r = self.visuals
        if self.active_filter:
            r = [v for v in r if v.framework == self.active_filter]
        if self.search_query:
            q = self.search_query.lower()
            r = [v for v in r if q in v.filter_key()]
        return r

    def _refresh(self) -> None:
        vis = self._selected()
        table = self.query_one("#visual-table", DataTable)
        table.clear()
        for v in self._filtered():
            state = STATUS[v.status]
            if not v.ready():
                missing = ", ".join(v.missing_deps())
                state = f"[red]NEED[/] [dim]{missing}[/]"
            tags = ", ".join(v.tags[:3]) if v.tags else "--"
            params = str(len(v.parameters)) if v.parameters else "--"
            table.add_row(state, v.name, FW_SHORT.get(v.framework, "?"), v.output.name, params, tags)
        self.query_one("#preview", PreviewPanel).update_visual(vis, self.parameter_index)
        self._update_status_bar()
        route = self.query_one("#btn-route", Button)
        route.label = f"Route: {vis.output.name}" if vis else "Route:"

    def _update_status_bar(self) -> None:
        n = len(self.visuals)
        r = sum(1 for v in self.visuals if v.ready())
        shown = len(self._filtered())
        live = [v for v in self.visuals if v.status == VisualStatus.RUNNING]
        parts = [f"{shown}/{n} VISUALS", f"{r} TOOLS READY"]
        if live:
            parts.append("LIVE: " + ", ".join(
                f"{v.name}#{v.process.pid}@{v.output.name}" if v.process else v.name
                for v in live
            ))
        self.query_one("#status-bar").update("  " + "  ·  ".join(parts))

    def _selected(self) -> Visual | None:
        table = self.query_one("#visual-table", DataTable)
        flt = self._filtered()
        if table.cursor_row is None or table.cursor_row >= len(flt):
            return None
        return flt[table.cursor_row]

    # -- Actions --

    def action_cursor_down(self) -> None:
        t = self.query_one("#visual-table", DataTable)
        r = (t.cursor_row or 0) + 1
        if r < len(self._filtered()):
            t.move_cursor(row=r)
            self.query_one("#preview", PreviewPanel).update_visual(self._selected(), self.parameter_index)

    def action_cursor_up(self) -> None:
        t = self.query_one("#visual-table", DataTable)
        r = max(0, (t.cursor_row or 1) - 1)
        t.move_cursor(row=r)
        self.query_one("#preview", PreviewPanel).update_visual(self._selected(), self.parameter_index)

    def action_build_visual(self) -> None:
        vis = self._selected()
        if vis and vis.build_cmd:
            self._build(vis)
        elif vis:
            self.query_one("#status-bar").update(f" {vis.name}: no build step")

    def action_run_visual(self) -> None:
        vis = self._selected()
        if not vis:
            return
        if not vis.ready():
            missing = ", ".join(vis.missing_deps())
            self.query_one("#status-bar").update(f" {vis.name}: missing {missing} - run install.ps1")
            return
        if vis.status == VisualStatus.BUILDING:
            self.query_one("#status-bar").update(f" {vis.name}: build in progress...")
            return
        if vis.output.run_cmd or vis.run_cmd:
            self._build_and_run(vis)
        else:
            self.query_one("#status-bar").update(f" {vis.name}: no run command")

    @work(thread=True, exclusive=True, group="build")
    def _build(self, vis: Visual) -> None:
        ok, output = build_visual(vis)
        message = f" {vis.name}: {'build complete' if ok else 'build failed'}"
        if not ok and output:
            message += f" · {output.strip().splitlines()[-1][:100]}"
        self.call_from_thread(self._finish_action, message)

    @work(thread=True, exclusive=True, group="run")
    def _build_and_run(self, vis: Visual) -> None:
        if vis.build_cmd:
            self.call_from_thread(self._refresh)
            ok, output = build_visual(vis)
            if not ok:
                message = f" {vis.name}: build failed"
                if output:
                    message += f" · {output.strip().splitlines()[-1][:100]}"
                self.call_from_thread(self._finish_action, message)
                return
        ok, output = run_visual(vis)
        self.call_from_thread(self._finish_action, f" {vis.name}: {output if ok else 'failed · ' + output[-100:]}")

    def _finish_action(self, message: str) -> None:
        self._refresh()
        self.query_one("#status-bar").update(message)

    def action_stop_visual(self) -> None:
        vis = self._selected()
        if vis:
            pid = vis.process.pid if vis.process else None
            ok = stop_visual(vis)
            suffix = f" (killed pid {pid})" if ok and pid else (" (already stopped)" if pid is None else " (kill failed)")
            self._finish_action(f" {vis.name}: stopped{suffix}")

    def action_next_output(self) -> None:
        vis = self._selected()
        if not vis:
            return
        output = vis.select_next_output()
        if vis.status == VisualStatus.RUNNING:
            stop_visual(vis)
            ok, msg = run_visual(vis)
            self._finish_action(f" {vis.name}: route → {output.name} — {'relaunched' if ok else 'RESTART FAILED · ' + msg}")
        else:
            self._finish_action(f" {vis.name}: route → {output.name} (applies on next run)")

    def _parameter(self) -> tuple[Visual | None, Parameter | None]:
        vis = self._selected()
        if not vis or not vis.parameters:
            return vis, None
        self.parameter_index %= len(vis.parameters)
        return vis, vis.parameters[self.parameter_index]

    def action_previous_parameter(self) -> None:
        vis = self._selected()
        if vis and vis.parameters:
            self.parameter_index = (self.parameter_index - 1) % len(vis.parameters)
            self.query_one("#preview", PreviewPanel).update_visual(vis, self.parameter_index)

    def action_next_parameter(self) -> None:
        vis = self._selected()
        if vis and vis.parameters:
            self.parameter_index = (self.parameter_index + 1) % len(vis.parameters)
            self.query_one("#preview", PreviewPanel).update_visual(vis, self.parameter_index)

    def action_decrease_parameter(self) -> None:
        self._nudge_parameter(-1)

    def action_increase_parameter(self) -> None:
        self._nudge_parameter(1)

    def _nudge_parameter(self, direction: int) -> None:
        vis, parameter = self._parameter()
        if parameter:
            parameter.lfo = False
            parameter.set_value(parameter.value + direction * (parameter.maximum - parameter.minimum) / 50)
            self._send_parameter(vis, parameter)
            self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)

    def action_toggle_lfo(self) -> None:
        vis, parameter = self._parameter()
        if parameter:
            parameter.lfo = not parameter.lfo
            self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)

    def action_rate_down(self) -> None:
        self._nudge_rate(-1)

    def action_rate_up(self) -> None:
        self._nudge_rate(1)

    def _nudge_rate(self, direction: int) -> None:
        vis, parameter = self._parameter()
        if parameter and parameter.lfo:
            parameter.lfo_rate = round(max(0.05, min(4.0, parameter.lfo_rate + direction * 0.05)), 2)
            self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)

    def action_cycle_curve(self) -> None:
        vis, parameter = self._parameter()
        if parameter and parameter.lfo:
            parameter.lfo_curve = CURVES[(CURVES.index(parameter.lfo_curve) + 1) % len(CURVES)]
            self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)

    def _lfo_offset(self, p: Parameter) -> float:
        return (sum(ord(c) for c in p.address) % 360) / 360 * math.tau

    def _curve(self, name: str, phase: float) -> float:
        if name == "triangle":
            t = (phase / math.tau) % 1.0
            return 1.0 - 2.0 * abs(t - math.floor(t + 0.5))
        if name == "square":
            return 0.0 if (phase / math.tau) % 1.0 < 0.5 else 1.0
        if name == "ramp":
            return (phase / math.tau) % 1.0
        return (math.sin(phase) + 1.0) * 0.5

    def _tick_modulation(self) -> None:
        changed = False
        now = time.monotonic()
        for vis in self.visuals:
            if vis.status == VisualStatus.RUNNING and vis.process.poll() is not None:
                vis.status = VisualStatus.STOPPED if vis.process.returncode == 0 else VisualStatus.ERROR
                vis.process = None
                changed = True
            for p in vis.parameters:
                if p.lfo:
                    phase = now * p.lfo_rate * math.tau + self._lfo_offset(p)
                    p.set_value(p.minimum + self._curve(p.lfo_curve, phase) * (p.maximum - p.minimum))
                    self._send_parameter(vis, p)
                    changed = True
        if changed:
            self.query_one("#preview", PreviewPanel).refresh_values(self._selected(), self.parameter_index)
            self._update_status_bar()

    def _send_parameter(self, vis: Visual, parameter: Parameter) -> None:
        if not vis.osc_port:
            return
        try:
            send_float(vis.osc_host, vis.osc_port, parameter.address, parameter.value)
        except (OSError, ValueError) as error:
            self.query_one("#status-bar").update(f" OSC error: {error}")

    def action_open_source(self) -> None:
        vis = self._selected()
        src = vis.source_path if vis else None
        if src is None:
            self.query_one("#status-bar").update(" no editable source found for this visual")
            return
        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "notepad"
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", f'"{editor}"', f'"{str(src)}"'],
                cwd=str(src.parent),
            )
        except Exception as error:
            self.query_one("#status-bar").update(f" edit failed: {error}")
            return
        where = src.relative_to(self.library_path)
        suffix = " · save to reload" if self.live_mode else ""
        self.query_one("#status-bar").update(f" edit: {editor} {where}{suffix}")

    def action_toggle_live(self) -> None:
        self.live_mode = not self.live_mode
        self.query_one("#btn-live", Button).set_class(self.live_mode, "active")
        if self.live_mode:
            vis = self._selected()
            src = vis.source_path if vis else None
            self._live_source = src
            self._live_mtime = src.stat().st_mtime if src else 0.0
            msg = (f" live ON: watching {src.relative_to(self.library_path)} — save to reload"
                   if src else " live ON: no source file for this visual")
        else:
            msg = " live OFF"
        self.query_one("#status-bar").update(msg)

    def _poll_live(self) -> None:
        if not self.live_mode:
            return
        vis = self._selected()
        src = vis.source_path if vis else None
        if src is None:
            self._live_source = None
            self._live_mtime = 0.0
            return
        if src != self._live_source:
            self._live_source = src
            self._live_mtime = src.stat().st_mtime
            return
        try:
            mtime = src.stat().st_mtime
        except OSError:
            return
        if mtime == 0.0 or mtime == self._live_mtime:
            return
        self._live_mtime = mtime
        if vis.framework == Framework.GLSL:
            self.query_one("#status-bar").update(f" {vis.name}: shader saved — hot reloading in sketch window")
            return
        if vis.status == VisualStatus.RUNNING:
            self.query_one("#status-bar").update(f" {vis.name}: source saved — rebuilding + relaunching")
            self.reload_visual(vis)

    @work(thread=True, exclusive=True, group="run")
    def reload_visual(self, vis: Visual) -> None:
        stop_visual(vis)
        self.call_from_thread(self._refresh)
        if vis.build_cmd:
            ok, output = build_visual(vis)
            if not ok:
                self.call_from_thread(
                    self._finish_action,
                    f" {vis.name}: live reload build failed · {output.strip().splitlines()[-1][:100]}",
                )
                return
        ok, output = run_visual(vis)
        msg = f" {vis.name}: live reload → {output if ok else 'FAILED · ' + output[-100:]}"
        self.call_from_thread(self._finish_action, msg)

    def action_toggle_preview(self) -> None:
        self.preview_visible = not self.preview_visible
        p = self.query_one("#preview-panel")
        l = self.query_one("#list-panel")
        if self.preview_visible:
            p.remove_class("hidden")
            l.remove_class("wide")
        else:
            p.add_class("hidden")
            l.add_class("wide")

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_clear_search(self) -> None:
        self.query_one("#search-input", Input).value = ""
        self.search_query = ""
        self.query_one("#visual-table", DataTable).focus()
        self._refresh()

    def action_filter_all(self) -> None:
        self.active_filter = None
        self.query_one("#active-filter").update("[bold green]ALL[/]")
        self._refresh()

    def action_filter_of(self) -> None:
        self._toggle(Framework.OPENFRAMEWORKS, "oF")

    def action_filter_nannou(self) -> None:
        self._toggle(Framework.NANNOU, "Nannou")

    def action_filter_glsl(self) -> None:
        self._toggle(Framework.GLSL, "GLSL")

    def action_filter_proc(self) -> None:
        self._toggle(Framework.PROCESSING, "Processing")

    def _toggle(self, fw: Framework, label: str) -> None:
        self.active_filter = None if self.active_filter == fw else fw
        txt = label.upper() if self.active_filter else "ALL"
        self.query_one("#active-filter").update(f"[bold #00ff9d]{txt}[/]")
        self._refresh()

    @on(Button.Pressed, ".param-row")
    def on_param_row(self, event: Button.Pressed) -> None:
        self.parameter_index = list(self.query(".param-row")).index(event.button)
        self.query_one("#preview", PreviewPanel).update_visual(self._selected(), self.parameter_index)

    @on(Button.Pressed, "#btn-run")
    def on_btn_run(self, event: Button.Pressed) -> None:
        self.action_run_visual()

    @on(Button.Pressed, "#btn-stop")
    def on_btn_stop(self, event: Button.Pressed) -> None:
        self.action_stop_visual()

    @on(Button.Pressed, "#btn-build")
    def on_btn_build(self, event: Button.Pressed) -> None:
        self.action_build_visual()

    @on(Button.Pressed, "#btn-edit")
    def on_btn_edit(self, event: Button.Pressed) -> None:
        self.action_open_source()

    @on(Button.Pressed, "#btn-live")
    def on_btn_live(self, event: Button.Pressed) -> None:
        self.action_toggle_live()

    @on(Button.Pressed, "#btn-route")
    def on_btn_route(self, event: Button.Pressed) -> None:
        self.action_next_output()

    @on(Button.Pressed, "#btn-prev")
    def on_btn_prev(self, event: Button.Pressed) -> None:
        self.action_previous_parameter()

    @on(Button.Pressed, "#btn-next")
    def on_btn_next(self, event: Button.Pressed) -> None:
        self.action_next_parameter()

    @on(Button.Pressed, "#btn-close")
    def on_btn_close(self, event: Button.Pressed) -> None:
        self.exit()

    @on(Input.Submitted, "#manual-input")
    def on_manual_input(self, event: Input.Submitted) -> None:
        vis, parameter = self._parameter()
        if not parameter:
            return
        raw = event.value.strip()
        if raw:
            try:
                value = float(raw)
            except ValueError:
                self.query_one("#status-bar").update(f" invalid number: {raw!r}")
                return
            parameter.lfo = False
            parameter.set_value(value)
            self._send_parameter(vis, parameter)
            self.query_one("#status-bar").update(f" {parameter.name} = {parameter.value:g} (static)")
            self.query_one("#manual-input", Input).value = ""
        self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)
        self.query_one("#visual-table", DataTable).focus()

    @on(Slider.Changed, "#value-slider")
    def on_value_slider(self, event: Slider.Changed) -> None:
        vis, parameter = self._parameter()
        if not parameter or event.value == parameter.value:
            return
        parameter.lfo = False
        parameter.set_value(event.value)
        self._send_parameter(vis, parameter)
        self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)

    @on(Slider.Changed, "#rate-slider")
    def on_rate_slider(self, event: Slider.Changed) -> None:
        vis, parameter = self._parameter()
        if parameter and parameter.lfo:
            parameter.lfo_rate = round(max(0.05, min(4.0, event.value)), 2)
            self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)

    @on(Switch.Changed, "#lfo-switch")
    def on_lfo_switch(self, event: Switch.Changed) -> None:
        vis, parameter = self._parameter()
        if parameter:
            parameter.lfo = event.value
            self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)

    @on(Select.Changed, "#curve-select")
    def on_curve_select(self, event: Select.Changed) -> None:
        vis, parameter = self._parameter()
        if parameter and parameter.lfo and event.value:
            parameter.lfo_curve = event.value
            self.query_one("#preview", PreviewPanel).refresh_values(vis, self.parameter_index)

    @on(Select.Changed, "#controls-menu")
    def on_controls_menu(self, event: Select.Changed) -> None:
        if not isinstance(event.value, int) or event.value == self.parameter_index:
            return
        self.parameter_index = event.value
        self.query_one("#preview", PreviewPanel).update_visual(self._selected(), self.parameter_index)

    @on(Input.Changed, "#search-input")
    def on_search(self, event: Input.Changed) -> None:
        self.search_query = event.value
        self._refresh()

    @on(DataTable.RowSelected)
    def on_row(self, event: DataTable.RowSelected) -> None:
        self.action_run_visual()

    @on(DataTable.RowHighlighted)
    def on_highlight(self, event: DataTable.RowHighlighted) -> None:
        self.parameter_index = 0
        self.query_one("#preview", PreviewPanel).update_visual(self._selected(), self.parameter_index)