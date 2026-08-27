from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Header, Input, Label, Rule, Static

from xvcpanel.controls.osc import send_float
from xvcpanel.loader.runner import build_visual, run_visual, stop_visual
from xvcpanel.loader.scanner import scan_library
from xvcpanel.models.visual import Framework, Visual, VisualStatus
from xvcpanel.spout.bridge import SpoutBridge

if TYPE_CHECKING:
    from pathlib import Path

FW_SHORT = {
    Framework.OPENFRAMEWORKS: "oF",
    Framework.NANNOU: "Nan",
    Framework.PROCESSING: "Proc",
    Framework.GLSL: "GLSL",
    Framework.THREEJS: "3.js",
    Framework.CINDER: "Cin",
    Framework.CUSTOM: "???",
}

STATUS = {
    VisualStatus.IDLE: "[dim]IDLE[/]",
    VisualStatus.BUILDING: "[yellow]BUILD[/]",
    VisualStatus.RUNNING: "[bold green]LIVE[/]",
    VisualStatus.ERROR: "[bold red]ERROR[/]",
    VisualStatus.STOPPED: "[dim]STOP[/]",
}


class PreviewPanel(Static):
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview-inner"):
            yield Label("[bold cyan]NAME[/]", id="pv-name-label")
            yield Label("--", id="pv-name")
            yield Rule()
            yield Label("[bold cyan]OUTPUT ROUTE[/]", id="pv-output-label")
            yield Label("--", id="pv-output")
            yield Rule()
            yield Label("[bold cyan]LIVE CONTROLS[/]", id="pv-controls-label")
            yield Label("--", id="pv-controls")
            yield Rule()
            yield Label("[bold cyan]FRAMEWORK[/]", id="pv-fw-label")
            yield Label("--", id="pv-fw")
            yield Rule()
            yield Label("[bold cyan]TAGS[/]", id="pv-tags-label")
            yield Label("--", id="pv-tags")
            yield Rule()
            yield Label("[bold cyan]DESCRIPTION[/]", id="pv-desc-label")
            yield Label("--", id="pv-desc")
            yield Rule()
            yield Label("[bold cyan]REQUIRES[/]", id="pv-requires-label")
            yield Label("--", id="pv-requires")
            yield Rule()
            yield Label("[bold cyan]INSTALL[/]", id="pv-install-label")
            yield Label("[dim]--[/]", id="pv-install")
            yield Rule()
            yield Label("[bold cyan]BUILD[/]", id="pv-build-label")
            yield Label("[dim]--[/]", id="pv-build")
            yield Rule()
            yield Label("[bold cyan]RUN[/]", id="pv-run-label")
            yield Label("[dim]--[/]", id="pv-run")

    def update_visual(self, vis: Visual | None) -> None:
        ids = ["pv-name", "pv-output", "pv-controls", "pv-fw", "pv-tags", "pv-desc", "pv-requires", "pv-install", "pv-build", "pv-run"]
        if vis is None:
            for i in ids:
                self.query_one(f"#{i}", Label).update("[dim]--[/]")
            return
        self.query_one("#pv-name", Label).update(f"[bold white]{vis.name}[/]")
        output = vis.output
        configured = "[green]CONFIGURED[/]" if output.protocol == "window" else "[yellow]APP-SIDE[/]"
        self.query_one("#pv-output", Label).update(
            f"[bold magenta]{output.name}[/]  [dim]{output.protocol.upper()}[/]  {configured}\n"
            "[dim]o: switch route · transport runs inside the visual[/]"
        )
        if vis.parameters:
            controls = []
            for index, parameter in enumerate(vis.parameters):
                marker = "[bold cyan]>[/]" if index == getattr(self.app, "parameter_index", 0) else " "
                lfo = " [bold magenta]~LFO[/]" if parameter.lfo else ""
                controls.append(f"{marker} {parameter.name:<14} [bold white]{parameter.value:7.3f}[/]{lfo}")
            controls.append("[dim]brackets:select  -/=:value  m:LFO[/]")
            self.query_one("#pv-controls", Label).update("\n".join(controls))
        else:
            self.query_one("#pv-controls", Label).update("[dim]No parameters declared in xvc.json[/]")
        self.query_one("#pv-fw", Label).update(f"[bold magenta]{vis.framework.value}[/]")
        self.query_one("#pv-tags", Label).update(
            " ".join(f"[dim][{t}][/]" for t in vis.tags) if vis.tags else "[dim]none[/]"
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
    Screen { background: #070912; }
    #app-header { dock: top; height: 3; background: #11152a; border-bottom: tall #6d28d9; }
    #app-header .header--title { color: #00e5ff; text-style: bold; }
    #search-box { dock: top; height: 3; background: #0b1020; border-bottom: tall #1a2744; padding: 0 2; }
    #search-input { background: #111827; border: tall #1e3a5f; color: #00e5ff; width: 100%; }
    #search-input:focus { border: tall #00e5ff; }
    #filter-bar { dock: top; height: 3; background: #0b1020; border-bottom: tall #1a2744; padding: 0 1; }
    .fkey { color: #00e5ff; text-style: bold; }
    #main-split { height: 1fr; }
    #list-panel { width: 58%; border-right: tall #1a2744; background: #0a0e17; }
    #list-panel.wide { width: 100%; border-right: none; }
    #visual-table { background: #0a0e17; }
    #visual-table > .datatable--cursor { background: #111d33; color: #00e5ff; }
    #preview-panel { width: 42%; background: #0b1020; padding: 1 2; border-left: tall #6d28d9; }
    #preview-panel.hidden { display: none; }
    #preview-inner { height: 1fr; }
    #preview-inner Rule { color: #1a2744; }
    #status-bar { dock: bottom; height: 1; background: #00e5ff; color: #070912; text-style: bold; padding: 0 1; }
    #help-bar { dock: bottom; height: 3; background: #0f1423; border-top: tall #1a2744; padding: 0 1; color: #4a6a8a; }
    """

    BINDINGS = [
        Binding("j,down", "cursor_down", "down", show=True, priority=True),
        Binding("k,up", "cursor_up", "up", show=True, priority=True),
        Binding("enter", "run_visual", "Run", show=True, priority=True),
        Binding("b", "build_visual", "Build", show=True, priority=True),
        Binding("s", "stop_visual", "Stop", show=True, priority=True),
        Binding("o", "next_output", "Output", show=True, priority=True),
        Binding("left_square_bracket", "previous_parameter", "Control", show=False, priority=True),
        Binding("right_square_bracket", "next_parameter", "Control", show=False, priority=True),
        Binding("minus", "decrease_parameter", "Value", show=False, priority=True),
        Binding("equals_sign", "increase_parameter", "Value", show=False, priority=True),
        Binding("m", "toggle_lfo", "Modulate", show=True, priority=True),
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
        self.lfo_started = time.monotonic()

    def compose(self) -> ComposeResult:
        yield Header(id="app-header")
        with Vertical(id="search-box"):
            yield Input(placeholder=" search visuals...", id="search-input")
        with Horizontal(id="filter-bar"):
            yield Label(" [bold cyan]1[/][dim]:oF[/]  [bold cyan]2[/][dim]:Nan[/]  [bold cyan]3[/][dim]:GLSL[/]  [bold cyan]4[/][dim]:Proc[/]  [dim]f:All[/]   ", id="filter-display")
            yield Label("--", id="active-filter")
        with Horizontal(id="main-split"):
            with Vertical(id="list-panel"):
                yield DataTable(cursor_type="row", id="visual-table")
            with Vertical(id="preview-panel"):
                yield PreviewPanel(id="preview")
        yield Label(id="status-bar")
        yield Label(" j/k move  Enter run  b build  s stop  o route  brackets control  -/= value  m LFO  / search", id="help-bar")

    def on_mount(self) -> None:
        self._bootstrap_path()
        table = self.query_one("#visual-table", DataTable)
        table.add_columns("State", "Name", "FW", "Output", "Controls", "Tags")
        self.visuals = scan_library(self.library_path)
        self._refresh()
        self.set_interval(0.05, self._tick_modulation)
        table.focus()

    def _bootstrap_path(self) -> None:
        import os
        tools = self.library_path.parent / ".tools"
        if tools.is_dir():
            for exe in tools.rglob("*.exe"):
                d = str(exe.parent)
                if d not in os.environ["PATH"]:
                    os.environ["PATH"] = d + ";" + os.environ["PATH"]
        cargo_bin = Path.home() / ".cargo" / "bin"
        if cargo_bin.is_dir():
            d = str(cargo_bin)
            if d not in os.environ["PATH"]:
                os.environ["PATH"] = d + ";" + os.environ["PATH"]

    def _filtered(self) -> list[Visual]:
        r = self.visuals
        if self.active_filter:
            r = [v for v in r if v.framework == self.active_filter]
        if self.search_query:
            q = self.search_query.lower()
            r = [v for v in r if q in v.filter_key()]
        return r

    def _refresh(self) -> None:
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
        vis = self._selected()
        self.query_one("#preview", PreviewPanel).update_visual(vis)
        n = len(self.visuals)
        r = sum(1 for v in self.visuals if v.ready())
        live = sum(1 for v in self.visuals if v.status == VisualStatus.RUNNING)
        shown = len(self._filtered())
        self.query_one("#status-bar").update(f" {shown}/{n} VISUALS  ·  {live} LIVE  ·  {r} TOOLS READY  ·  ROUTE + MODULATION ARMED")

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
            self.query_one("#preview", PreviewPanel).update_visual(self._selected())

    def action_cursor_up(self) -> None:
        t = self.query_one("#visual-table", DataTable)
        r = max(0, (t.cursor_row or 1) - 1)
        t.move_cursor(row=r)
        self.query_one("#preview", PreviewPanel).update_visual(self._selected())

    def action_build_visual(self) -> None:
        vis = self._selected()
        if vis and vis.build_cmd:
            self._build(vis)
        elif vis:
            self.query_one("#status-bar").update(f" {vis.name}: no build step")

    def action_run_visual(self) -> None:
        vis = self._selected()
        if vis and (vis.output.run_cmd or vis.run_cmd):
            self._run(vis)
        elif vis:
            self.query_one("#status-bar").update(f" {vis.name}: no run command")

    @work(thread=True, exclusive=True, group="build")
    def _build(self, vis: Visual) -> None:
        ok, output = build_visual(vis)
        message = f" {vis.name}: {'build complete' if ok else 'build failed'}"
        if not ok and output:
            message += f" · {output.strip().splitlines()[-1][:100]}"
        self.call_from_thread(self._finish_action, message)

    @work(thread=True, exclusive=True, group="run")
    def _run(self, vis: Visual) -> None:
        ok, output = run_visual(vis)
        self.call_from_thread(self._finish_action, f" {vis.name}: {output if ok else 'failed · ' + output[-100:]}")

    def _finish_action(self, message: str) -> None:
        self._refresh()
        self.query_one("#status-bar").update(message)

    def action_stop_visual(self) -> None:
        vis = self._selected()
        if vis:
            stop_visual(vis)
            self._finish_action(f" {vis.name}: stopped")

    def action_next_output(self) -> None:
        vis = self._selected()
        if vis:
            output = vis.select_next_output()
            self._refresh()
            self.query_one("#status-bar").update(f" {vis.name} → {output.name} ({output.protocol})")

    def _parameter(self):
        vis = self._selected()
        if not vis or not vis.parameters:
            return vis, None
        self.parameter_index %= len(vis.parameters)
        return vis, vis.parameters[self.parameter_index]

    def action_previous_parameter(self) -> None:
        vis = self._selected()
        if vis and vis.parameters:
            self.parameter_index = (self.parameter_index - 1) % len(vis.parameters)
            self.query_one("#preview", PreviewPanel).update_visual(vis)

    def action_next_parameter(self) -> None:
        vis = self._selected()
        if vis and vis.parameters:
            self.parameter_index = (self.parameter_index + 1) % len(vis.parameters)
            self.query_one("#preview", PreviewPanel).update_visual(vis)

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
            self.query_one("#preview", PreviewPanel).update_visual(vis)

    def action_toggle_lfo(self) -> None:
        vis, parameter = self._parameter()
        if parameter:
            parameter.lfo = not parameter.lfo
            self.query_one("#preview", PreviewPanel).update_visual(vis)

    def _tick_modulation(self) -> None:
        changed = False
        phase = (time.monotonic() - self.lfo_started) * math.tau * 0.25
        for vis in self.visuals:
            if vis.status == VisualStatus.RUNNING and vis.process.poll() is not None:
                vis.status = VisualStatus.STOPPED if vis.process.returncode == 0 else VisualStatus.ERROR
                vis.process = None
                changed = True
            for parameter in vis.parameters:
                if parameter.lfo:
                    parameter.set_value(parameter.minimum + (math.sin(phase) + 1) * 0.5 * (parameter.maximum - parameter.minimum))
                    self._send_parameter(vis, parameter)
                    changed = True
        if changed:
            self.query_one("#preview", PreviewPanel).update_visual(self._selected())

    def _send_parameter(self, vis: Visual, parameter) -> None:
        if not vis.osc_port:
            return
        try:
            send_float(vis.osc_host, vis.osc_port, parameter.address, parameter.value)
        except (OSError, ValueError) as error:
            self.query_one("#status-bar").update(f" OSC error: {error}")

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
        self.query_one("#active-filter").update(f"[bold magenta]{txt}[/]")
        self._refresh()

    @on(Input.Changed, "#search-input")
    def on_search(self, event: Input.Changed) -> None:
        self.search_query = event.value
        self._refresh()

    @on(DataTable.RowSelected)
    def on_row(self, event: DataTable.RowSelected) -> None:
        self.query_one("#preview", PreviewPanel).update_visual(self._selected())

    @on(DataTable.RowHighlighted)
    def on_highlight(self, event: DataTable.RowHighlighted) -> None:
        self.parameter_index = 0
        self.query_one("#preview", PreviewPanel).update_visual(self._selected())
