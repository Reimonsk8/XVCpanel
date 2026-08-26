from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Input, Label, Static

from xvcpanel.loader.runner import build_visual, run_visual, stop_visual
from xvcpanel.loader.scanner import scan_library
from xvcpanel.models.visual import Framework, Visual, VisualStatus
from xvcpanel.spout.bridge import SpoutBridge

if TYPE_CHECKING:
    from pathlib import Path


FILTER_BINDINGS = [
    Binding("f", "filter_all", "All"),
    Binding("1", "filter_of", "oF", key_display="1"),
    Binding("2", "filter_nannou", "Nannou", key_display="2"),
    Binding("3", "filter_glsl", "GLSL", key_display="3"),
    Binding("4", "filter_processing", "Processing", key_display="4"),
]

STATUS_ICONS = {
    VisualStatus.IDLE: "[dim]-[/]",
    VisualStatus.BUILDING: "[yellow]*[/]",
    VisualStatus.RUNNING: "[green]@[/]",
    VisualStatus.ERROR: "[red]X[/]",
    VisualStatus.STOPPED: "[dim]#[/]",
}


class VisualList(Static):
    """Table of all visuals with status indicators."""

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type="row")
        yield Footer()


class FilterBar(Static):
    """Active filter display."""

    current_filter: reactive[str] = reactive("all")

    def compose(self) -> ComposeResult:
        yield Label("filter: [bold]all[/]", id="filter-label")

    def watch_current_filter(self, value: str) -> None:
        label = self.query_one("#filter-label", Label)
        label.update(f"filter: [bold]{value}[/]")


class StatusBar(Static):
    """Bottom status bar."""

    status_text: reactive[str] = reactive("ready")

    def compose(self) -> ComposeResult:
        yield Label(id="status-label")

    def watch_status_text(self, value: str) -> None:
        label = self.query_one("#status-label", Label)
        label.update(value)


class XVCpanel(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main {
        height: 1fr;
    }
    #table-container {
        height: 1fr;
    }
    DataTable {
        height: 1fr;
    }
    #filter-bar {
        height: 1;
        dock: top;
        padding: 0 1;
    }
    #status-bar {
        height: 1;
        dock: bottom;
        padding: 0 1;
        background: $accent-darken-2;
    }
    #search-bar {
        height: 3;
        dock: top;
        padding: 0 1;
    }
    #search-input {
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("b", "build", "Build"),
        Binding("r", "run", "Run"),
        Binding("s", "stop", "Stop"),
        Binding("q", "quit", "Quit"),
        Binding("slash", "focus_search", "Search", show=False),
        Binding("escape", "unfocus_search", show=False, key_display="Esc"),
    ] + FILTER_BINDINGS

    TITLE = "XVCpanel"
    SUB_TITLE = "visual mixer"

    def __init__(self, library_path: Path, spout: SpoutBridge | None = None) -> None:
        super().__init__()
        self.library_path = library_path
        self.visuals: list[Visual] = []
        self.spout = spout or SpoutBridge()
        self.active_filter: Framework | None = None
        self.search_query: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="search-bar"):
            yield Input(placeholder="search visuals... (Esc to clear)", id="search-input")
        with Vertical(id="main"):
            yield FilterBar(id="filter-bar")
            with Vertical(id="table-container"):
                yield VisualList(id="visual-list")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        self._load_visuals()

    def _load_visuals(self) -> None:
        self.visuals = scan_library(self.library_path)
        self._refresh_table()

    def _filtered_visuals(self) -> list[Visual]:
        result = self.visuals
        if self.active_filter:
            result = [v for v in result if v.framework == self.active_filter]
        if self.search_query:
            q = self.search_query.lower()
            result = [v for v in result if q in v.filter_key()]
        return result

    def _refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        table.add_columns(" ", "Name", "Framework", "Tags", "Status")

        for v in self._filtered_visuals():
            icon = STATUS_ICONS[v.status]
            tags = ", ".join(v.tags[:3]) if v.tags else "—"
            table.add_row(icon, v.name, v.framework.value, tags, v.status.value)

        self._update_status()

    def _update_status(self) -> None:
        running = [v for v in self.visuals if v.status == VisualStatus.RUNNING]
        spout_status = "Spout ✓" if self.spout.available else "Spout stub"
        if running:
            names = ", ".join(v.name for v in running)
            self.query_one(StatusBar).status_text = f"running: {names} → {spout_status}"
        else:
            self.query_one(StatusBar).status_text = f"ready — {spout_status} — {len(self.visuals)} visuals loaded"

    def _selected_visual(self) -> Visual | None:
        table = self.query_one(DataTable)
        if table.cursor_row is None or table.cursor_row >= len(self._filtered_visuals()):
            return None
        return self._filtered_visuals()[table.cursor_row]

    # --- Actions ---

    def action_filter_all(self) -> None:
        self.active_filter = None
        self.query_one(FilterBar).current_filter = "all"
        self._refresh_table()

    def action_filter_of(self) -> None:
        self._set_filter(Framework.OPENFRAMEWORKS)

    def action_filter_nannou(self) -> None:
        self._set_filter(Framework.NANNOU)

    def action_filter_glsl(self) -> None:
        self._set_filter(Framework.GLSL)

    def action_filter_processing(self) -> None:
        self._set_filter(Framework.PROCESSING)

    def _set_filter(self, fw: Framework) -> None:
        if self.active_filter == fw:
            self.active_filter = None
            self.query_one(FilterBar).current_filter = "all"
        else:
            self.active_filter = fw
            self.query_one(FilterBar).current_filter = fw.value
        self._refresh_table()

    def action_build(self) -> None:
        vis = self._selected_visual()
        if vis:
            self._do_build(vis)

    def action_run(self) -> None:
        vis = self._selected_visual()
        if vis:
            self._do_run(vis)

    def action_stop(self) -> None:
        vis = self._selected_visual()
        if vis:
            self._do_stop(vis)

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_unfocus_search(self) -> None:
        self.query_one(DataTable).focus()
        inp = self.query_one("#search-input", Input)
        inp.value = ""
        self.search_query = ""
        self._refresh_table()

    # --- Event handlers ---

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.search_query = event.value
        self._refresh_table()

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        vis = self._selected_visual()
        if vis and vis.description:
            self.query_one(StatusBar).status_text = f"{vis.name}: {vis.description}"

    # --- Async workers ---

    def _set_status(self, text: str) -> None:
        self.query_one(StatusBar).status_text = text

    @work(thread=True)
    def _do_build(self, visual: Visual) -> None:
        self.call_from_thread(self._set_status, f"building {visual.name}...")
        ok, output = asyncio.run(build_visual(visual))
        self.call_from_thread(self._refresh_table)
        if not ok:
            self.call_from_thread(self._set_status, f"build failed: {output[:120]}")

    @work(thread=True)
    def _do_run(self, visual: Visual) -> None:
        self.call_from_thread(self._set_status, f"starting {visual.name}...")
        ok, output = asyncio.run(run_visual(visual))
        self.call_from_thread(self._refresh_table)
        if not ok:
            self.call_from_thread(self._set_status, f"run failed: {output[:120]}")
        else:
            self.call_from_thread(self._set_status, f"{visual.name} running → Spout")

    @work(thread=True)
    def _do_stop(self, visual: Visual) -> None:
        stop_visual(visual)
        self.call_from_thread(self._refresh_table)
        self.call_from_thread(self._set_status, f"{visual.name} stopped")
