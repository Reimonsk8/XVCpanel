from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Rule,
    Static,
)

from xvcpanel.loader.runner import build_visual, run_visual, stop_visual
from xvcpanel.loader.scanner import scan_library
from xvcpanel.models.visual import Framework, Visual, VisualStatus
from xvcpanel.spout.bridge import SpoutBridge

if TYPE_CHECKING:
    from pathlib import Path


# ── Status icons ──────────────────────────────────────────────────────────────

STATUS_STYLE = {
    VisualStatus.IDLE:    "[dim]○ idle[/]",
    VisualStatus.BUILDING:"[bold yellow]◉ build[/]",
    VisualStatus.RUNNING: "[bold green]● live[/]",
    VisualStatus.ERROR:   "[bold red]✗ error[/]",
    VisualStatus.STOPPED: "[dim]■ stopped[/]",
}

STATUS_SHORT = {
    VisualStatus.IDLE:    "○ idle",
    VisualStatus.BUILDING: "◉ BUILD",
    VisualStatus.RUNNING: "● LIVE",
    VisualStatus.ERROR:   "✗ ERR",
    VisualStatus.STOPPED: "■ stop",
}

FRAMEWORK_SHORT = {
    Framework.OPENFRAMEWORKS: "oF",
    Framework.NANNOU:         "Nan",
    Framework.PROCESSING:     "Proc",
    Framework.GLSL:           "GLSL",
    Framework.THREEJS:        "3.js",
    Framework.CINDER:         "Cin",
    Framework.CUSTOM:         "???",
}

FRAMEWORK_FILTER_KEYS = {
    "1": Framework.OPENFRAMEWORKS,
    "2": Framework.NANNOU,
    "3": Framework.GLSL,
    "4": Framework.PROCESSING,
}


# ── Widgets ───────────────────────────────────────────────────────────────────

class PreviewPanel(Static):
    """Right-side panel showing selected visual details."""

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview-inner"):
            yield Label("[bold cyan]NAME[/]", id="pv-name-label")
            yield Label("—", id="pv-name")
            yield Rule()
            yield Label("[bold cyan]FRAMEWORK[/]", id="pv-fw-label")
            yield Label("—", id="pv-fw")
            yield Rule()
            yield Label("[bold cyan]STATUS[/]", id="pv-status-label")
            yield Label("—", id="pv-status")
            yield Rule()
            yield Label("[bold cyan]TAGS[/]", id="pv-tags-label")
            yield Label("—", id="pv-tags")
            yield Rule()
            yield Label("[bold cyan]DESCRIPTION[/]", id="pv-desc-label")
            yield Label("—", id="pv-desc")
            yield Rule()
            yield Label("[bold cyan]BUILD[/]", id="pv-build-label")
            yield Label("[dim]—[/]", id="pv-build")
            yield Rule()
            yield Label("[bold cyan]RUN[/]", id="pv-run-label")
            yield Label("[dim]—[/]", id="pv-run")
            yield Rule()
            yield Label("[bold cyan]SPOUT[/]", id="pv-spout-label")
            yield Label("—", id="pv-spout")

    def update_visual(self, vis: Visual | None) -> None:
        if vis is None:
            for lbl_id in ["pv-name", "pv-fw", "pv-status", "pv-tags",
                           "pv-desc", "pv-build", "pv-run", "pv-spout"]:
                self.query_one(f"#{lbl_id}", Label).update("[dim]—[/]")
            return

        self.query_one("#pv-name", Label).update(f"[bold white]{vis.name}[/]")
        self.query_one("#pv-fw", Label).update(
            f"[bold magenta]{vis.framework.value}[/]  "
            f"[dim]({FRAMEWORK_SHORT.get(vis.framework, '?')})[/]"
        )
        self.query_one("#pv-status", Label).update(STATUS_STYLE[vis.status])
        self.query_one("#pv-tags", Label).update(
            "  ".join(f"[dim]\\[{t}][/]" for t in vis.tags) if vis.tags else "[dim]none[/]"
        )
        self.query_one("#pv-desc", Label).update(
            vis.description if vis.description else "[dim]no description[/]"
        )
        self.query_one("#pv-build", Label).update(
            f"[green]{vis.build_cmd}[/]" if vis.build_cmd else "[dim]no build step[/]"
        )
        self.query_one("#pv-run", Label).update(
            f"[green]{vis.run_cmd}[/]" if vis.run_cmd else "[dim]no run command[/]"
        )
        spout_txt = "[bold green]ENABLED[/]" if vis.spout else "[dim]disabled[/]"
        self.query_one("#pv-spout", Label).update(spout_txt)


class FilterPill(Static):
    """A small filter indicator chip."""
    def __init__(self, label: str, **kwargs) -> None:
        super().__init__(label, **kwargs)


# ── Main App ──────────────────────────────────────────────────────────────────

class XVCpanel(App):

    CSS = r"""
    Screen {
        background: #0a0e17;
    }

    /* ── Header ── */
    #app-header {
        dock: top;
        height: 3;
        background: #0f1423;
        border-bottom: tall #1a2744;
        padding: 0 1;
    }
    #app-header .header--title {
        color: #00e5ff;
        text-style: bold;
    }
    #app-header .header--subtitle {
        color: #4a6a8a;
    }

    /* ── Search ── */
    #search-container {
        dock: top;
        height: 3;
        background: #0c1020;
        border-bottom: tall #1a2744;
        padding: 0 2;
    }
    #search-input {
        background: #111827;
        border: tall #1e3a5f;
        color: #00e5ff;
        width: 100%;
    }
    #search-input:focus {
        border: tall #00e5ff;
    }

    /* ── Filter bar ── */
    #filter-bar {
        dock: top;
        height: 3;
        background: #0c1020;
        border-bottom: tall #1a2744;
        padding: 0 1;
    }
    .filter-active {
        color: #00e5ff;
        text-style: bold;
    }
    .filter-inactive {
        color: #3a4a5a;
    }

    /* ── Main split ── */
    #main-split {
        height: 1fr;
    }

    /* ── Left: visual list ── */
    #list-panel {
        width: 58%;
        border-right: tall #1a2744;
        background: #0a0e17;
    }
    #visual-table {
        background: #0a0e17;
    }
    #visual-table > .datatable--cursor {
        background: #111d33;
        color: #00e5ff;
    }
    #visual-table > .datatable--hover {
        background: #0e1628;
    }
    #visual-table DataTable > .datatable--cursor > Label:first-child {
        color: #00e5ff;
        text-style: bold;
    }

    /* ── Right: preview ── */
    #preview-panel {
        width: 45%;
        background: #0c1020;
        padding: 1 2;
    }
    #preview-inner {
        height: 1fr;
    }
    #preview-inner Label {
        padding: 0 0;
    }
    #preview-inner Rule {
        color: #1a2744;
        margin: 0 0;
    }

    /* ── Footer / help ── */
    #help-bar {
        dock: bottom;
        height: 3;
        background: #0f1423;
        border-top: tall #1a2744;
        padding: 0 1;
        color: #4a6a8a;
    }
    .help-key {
        color: #00e5ff;
        text-style: bold;
    }
    .help-label {
        color: #3a5a7a;
    }

    /* ── Status bar ── */
    #status-bar {
        dock: bottom;
        height: 1;
        background: #00e5ff;
        color: #0a0e17;
        text-style: bold;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("j,down",     "cursor_down",  "↓",   show=True),
        Binding("k,up",       "cursor_up",    "↑",   show=True),
        Binding("enter",      "run_visual",   "Run",  show=True),
        Binding("b",          "build_visual", "Build",show=True),
        Binding("s",          "stop_visual",  "Stop", show=True),
        Binding("f",          "filter_all",   "All",  show=True),
        Binding("1",          "filter_of",    "oF",   show=True),
        Binding("2",          "filter_nannou","Nan",  show=True),
        Binding("3",          "filter_glsl",  "GLSL", show=True),
        Binding("4",          "filter_proc",  "Proc", show=True),
        Binding("slash",      "focus_search", "/",    show=False),
        Binding("escape",     "clear_search", "Esc",  show=False),
        Binding("q",          "quit",         "Quit", show=True),
    ]

    TITLE = " XVCpanel "
    SUB_TITLE = "terminal visual mixer"

    def __init__(self, library_path: Path, spout: SpoutBridge | None = None) -> None:
        super().__init__()
        self.library_path = library_path
        self.visuals: list[Visual] = []
        self.spout = spout or SpoutBridge()
        self.active_filter: Framework | None = None
        self.search_query: str = ""

    def compose(self) -> ComposeResult:
        yield Header(id="app-header")

        with Vertical(id="search-container"):
            yield Input(placeholder=" search visuals by name, tag, framework...", id="search-input")

        with Horizontal(id="filter-bar"):
            yield Label("[bold cyan]FILTERS[/]  ", id="filter-label")
            yield Label("[bold cyan]1[/][dim]:oF[/]  ", classes="filter-active")
            yield Label("[bold cyan]2[/][dim]:Nan[/]  ", classes="filter-active")
            yield Label("[bold cyan]3[/][dim]:GLSL[/]  ", classes="filter-active")
            yield Label("[bold cyan]4[/][dim]:Proc[/]  ", classes="filter-active")
            yield Label("[dim]f:All[/]", classes="filter-active")
            yield Label("   ", id="active-filter-display")

        with Horizontal(id="main-split"):
            with Vertical(id="list-panel"):
                yield DataTable(cursor_type="row", id="visual-table")
            with Vertical(id="preview-panel"):
                yield PreviewPanel(id="preview")

        yield Label(id="status-bar")
        yield Label(
            "[dim] j/↓[/][help-key] down[/]  "
            "[dim] k/↑[/][help-key] up[/]  "
            "[dim] ⏎[/][help-key] run[/]  "
            "[dim] b[/][help-key] build[/]  "
            "[dim] s[/][help-key] stop[/]  "
            "[dim] /[/][help-key] search[/]  "
            "[dim] 1-4[/][help-key] filter[/]  "
            "[dim] q[/][help-key] quit[/]",
            id="help-bar",
        )

    def on_mount(self) -> None:
        table = self.query_one("#visual-table", DataTable)
        table.add_columns("  Status  ", "Name", "FW", "Tags", "Spout")
        self._load_visuals()
        table.focus()

    # ── Data ──────────────────────────────────────────────────────────────

    def _load_visuals(self) -> None:
        self.visuals = scan_library(self.library_path)
        self._refresh()

    def _filtered(self) -> list[Visual]:
        result = self.visuals
        if self.active_filter:
            result = [v for v in result if v.framework == self.active_filter]
        if self.search_query:
            q = self.search_query.lower()
            result = [v for v in result if q in v.filter_key()]
        return result

    def _refresh(self) -> None:
        table = self.query_one("#visual-table", DataTable)
        table.clear()
        for v in self._filtered():
            status = STATUS_SHORT[v.status]
            tags = ", ".join(v.tags[:3]) if v.tags else "—"
            spout = "[green]ON[/]" if v.spout else "[dim]--[/]"
            table.add_row(status, v.name, FRAMEWORK_SHORT.get(v.framework, "?"), tags, spout)
        self._update_preview()
        self._update_status()

    def _update_preview(self) -> None:
        vis = self._selected()
        self.query_one("#preview", PreviewPanel).update_visual(vis)

    def _update_status(self) -> None:
        running = [v for v in self.visuals if v.status == VisualStatus.RUNNING]
        spout_s = "Spout OK" if self.spout.available else "Spout stub"
        if running:
            names = ", ".join(v.name for v in running)
            self.query_one("#status-bar").update(
                f" ▶ {names}  →  {spout_s}"
            )
        else:
            self.query_one("#status-bar").update(
                f" ○ {len(self.visuals)} visuals loaded  │  {spout_s}"
            )

    def _selected(self) -> Visual | None:
        table = self.query_one("#visual-table", DataTable)
        flt = self._filtered()
        if table.cursor_row is None or table.cursor_row >= len(flt):
            return None
        return flt[table.cursor_row]

    # ── Actions ───────────────────────────────────────────────────────────

    def action_cursor_down(self) -> None:
        table = self.query_one("#visual-table", DataTable)
        table.move_cursor(row=table.cursor_row + 1 if table.cursor_row is not None else 0)
        self._update_preview()

    def action_cursor_up(self) -> None:
        table = self.query_one("#visual-table", DataTable)
        row = table.cursor_row - 1 if table.cursor_row and table.cursor_row > 0 else 0
        table.move_cursor(row=row)
        self._update_preview()

    def action_filter_all(self) -> None:
        self.active_filter = None
        self.query_one("#active-filter-display").update("[bold green]ALL[/]")
        self._refresh()

    def action_filter_of(self) -> None:
        self._toggle_filter(Framework.OPENFRAMEWORKS, "oF")

    def action_filter_nannou(self) -> None:
        self._toggle_filter(Framework.NANNOU, "Nannou")

    def action_filter_glsl(self) -> None:
        self._toggle_filter(Framework.GLSL, "GLSL")

    def action_filter_proc(self) -> None:
        self._toggle_filter(Framework.PROCESSING, "Processing")

    def _toggle_filter(self, fw: Framework, label: str) -> None:
        if self.active_filter == fw:
            self.active_filter = None
            self.query_one("#active-filter-display").update("[bold green]ALL[/]")
        else:
            self.active_filter = fw
            self.query_one("#active-filter-display").update(
                f"[bold magenta]{label.upper()}[/]"
            )
        self._refresh()

    def action_build_visual(self) -> None:
        vis = self._selected()
        if vis:
            self._do_build(vis)

    def action_run_visual(self) -> None:
        vis = self._selected()
        if vis:
            self._do_run(vis)

    def action_stop_visual(self) -> None:
        vis = self._selected()
        if vis:
            self._do_stop(vis)

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_clear_search(self) -> None:
        self.query_one("#search-input", Input).value = ""
        self.search_query = ""
        self.query_one("#visual-table", DataTable).focus()
        self._refresh()

    # ── Events ────────────────────────────────────────────────────────────

    @on(Input.Changed, "#search-input")
    def on_search(self, event: Input.Changed) -> None:
        self.search_query = event.value
        self._refresh()

    @on(DataTable.RowSelected)
    def on_row(self, event: DataTable.RowSelected) -> None:
        self._update_preview()

    # ── Workers ───────────────────────────────────────────────────────────

    def _set_status(self, text: str) -> None:
        self.query_one("#status-bar").update(f" {text}")

    @work(thread=True)
    def _do_build(self, visual: Visual) -> None:
        self.call_from_thread(self._set_status, f" ⏳ building {visual.name}...")
        ok, output = asyncio.run(build_visual(visual))
        self.call_from_thread(self._refresh)
        if not ok:
            self.call_from_thread(self._set_status, f" ✗ build failed: {output[:100]}")

    @work(thread=True)
    def _do_run(self, visual: Visual) -> None:
        self.call_from_thread(self._set_status, f" ⏳ starting {visual.name}...")
        ok, output = asyncio.run(run_visual(visual))
        self.call_from_thread(self._refresh)
        if not ok:
            self.call_from_thread(self._set_status, f" ✗ run failed: {output[:100]}")
        else:
            self.call_from_thread(self._set_status, f" ▶ {visual.name} → Spout")

    @work(thread=True)
    def _do_stop(self, visual: Visual) -> None:
        stop_visual(visual)
        self.call_from_thread(self._refresh)
        self.call_from_thread(self._set_status, f" ■ {visual.name} stopped")
