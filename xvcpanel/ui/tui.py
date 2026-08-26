from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Header, Input, Label, Rule, Static

from xvcpanel.loader.scanner import scan_library
from xvcpanel.models.visual import Framework, Visual, VisualStatus
from xvcpanel.spout.bridge import SpoutBridge

if TYPE_CHECKING:
    from pathlib import Path

# ponytail: status is display-only, no process tracking. add when you need live state.

FW_SHORT = {
    Framework.OPENFRAMEWORKS: "oF",
    Framework.NANNOU: "Nan",
    Framework.PROCESSING: "Proc",
    Framework.GLSL: "GLSL",
    Framework.THREEJS: "3.js",
    Framework.CINDER: "Cin",
    Framework.CUSTOM: "???",
}


def _open_cmd(command: str, cwd: Path) -> None:
    """Open a new terminal window running command. User closes it manually."""
    # ponytail: Windows-only. macOS: replace with ["open", "-a", "Terminal", ...]
    subprocess.Popen(
        f'start cmd /k "cd /d {cwd} && {command} && pause"',
        shell=True,
    )


class PreviewPanel(Static):
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview-inner"):
            yield Label("[bold cyan]NAME[/]", id="pv-name-label")
            yield Label("--", id="pv-name")
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
            yield Label("[bold cyan]BUILD[/]", id="pv-build-label")
            yield Label("[dim]--[/]", id="pv-build")
            yield Rule()
            yield Label("[bold cyan]RUN[/]", id="pv-run-label")
            yield Label("[dim]--[/]", id="pv-run")
            yield Rule()
            yield Label("[bold cyan]SPOUT[/]", id="pv-spout-label")
            yield Label("--", id="pv-spout")

    def update_visual(self, vis: Visual | None) -> None:
        ids = ["pv-name", "pv-fw", "pv-tags", "pv-desc", "pv-build", "pv-run", "pv-spout"]
        if vis is None:
            for i in ids:
                self.query_one(f"#{i}", Label).update("[dim]--[/]")
            return
        self.query_one("#pv-name", Label).update(f"[bold white]{vis.name}[/]")
        self.query_one("#pv-fw", Label).update(f"[bold magenta]{vis.framework.value}[/]")
        self.query_one("#pv-tags", Label).update(
            " ".join(f"[dim][{t}][/]" for t in vis.tags) if vis.tags else "[dim]none[/]"
        )
        self.query_one("#pv-desc", Label).update(vis.description or "[dim]no description[/]")
        self.query_one("#pv-build", Label).update(
            f"[green]{vis.build_cmd}[/]" if vis.build_cmd else "[dim]no build step[/]"
        )
        self.query_one("#pv-run", Label).update(
            f"[green]{vis.run_cmd}[/]" if vis.run_cmd else "[dim]no run command[/]"
        )
        self.query_one("#pv-spout", Label).update(
            "[bold green]ON[/]" if vis.spout else "[dim]off[/]"
        )


class XVCpanel(App):
    CSS = r"""
    Screen { background: #0a0e17; }
    #app-header { dock: top; height: 3; background: #0f1423; border-bottom: tall #1a2744; }
    #app-header .header--title { color: #00e5ff; text-style: bold; }
    #search-box { dock: top; height: 3; background: #0c1020; border-bottom: tall #1a2744; padding: 0 2; }
    #search-input { background: #111827; border: tall #1e3a5f; color: #00e5ff; width: 100%; }
    #search-input:focus { border: tall #00e5ff; }
    #filter-bar { dock: top; height: 3; background: #0c1020; border-bottom: tall #1a2744; padding: 0 1; }
    .fkey { color: #00e5ff; text-style: bold; }
    #main-split { height: 1fr; }
    #list-panel { width: 58%; border-right: tall #1a2744; background: #0a0e17; }
    #list-panel.wide { width: 100%; border-right: none; }
    #visual-table { background: #0a0e17; }
    #visual-table > .datatable--cursor { background: #111d33; color: #00e5ff; }
    #preview-panel { width: 42%; background: #0c1020; padding: 1 2; }
    #preview-panel.hidden { display: none; }
    #preview-inner { height: 1fr; }
    #preview-inner Rule { color: #1a2744; }
    #status-bar { dock: bottom; height: 1; background: #00e5ff; color: #0a0e17; text-style: bold; padding: 0 1; }
    #help-bar { dock: bottom; height: 3; background: #0f1423; border-top: tall #1a2744; padding: 0 1; color: #4a6a8a; }
    """

    BINDINGS = [
        Binding("j,down", "cursor_down", "down", show=True, priority=True),
        Binding("k,up", "cursor_up", "up", show=True, priority=True),
        Binding("enter", "run_visual", "Run", show=True, priority=True),
        Binding("b", "build_visual", "Build", show=True, priority=True),
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
    SUB_TITLE = "terminal visual mixer"

    def __init__(self, library_path: Path, spout: SpoutBridge | None = None) -> None:
        super().__init__()
        self.library_path = library_path
        self.visuals: list[Visual] = []
        self.spout = spout or SpoutBridge()
        self.active_filter: Framework | None = None
        self.search_query: str = ""
        self.preview_visible: bool = True

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
        yield Label(" j/Down:move  Enter:run  b:build  p:preview  1-4:filter  /:search  q:quit", id="help-bar")

    def on_mount(self) -> None:
        table = self.query_one("#visual-table", DataTable)
        table.add_columns("Name", "FW", "Tags", "Spout")
        self.visuals = scan_library(self.library_path)
        self._refresh()
        table.focus()

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
            tags = ", ".join(v.tags[:3]) if v.tags else "--"
            spout = "ON" if v.spout else "--"
            table.add_row(v.name, FW_SHORT.get(v.framework, "?"), tags, spout)
        vis = self._selected()
        self.query_one("#preview", PreviewPanel).update_visual(vis)
        n = len(self.visuals)
        self.query_one("#status-bar").update(f" {n} visuals loaded")

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
            _open_cmd(vis.build_cmd, vis.path)

    def action_run_visual(self) -> None:
        vis = self._selected()
        if vis and vis.run_cmd:
            _open_cmd(vis.run_cmd, vis.path)

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
