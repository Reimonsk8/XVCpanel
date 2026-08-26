"""XVCpanel live visual control surface."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from xvcpanel.loader.scanner import scan_library
from xvcpanel.spout.bridge import SpoutBridge
from xvcpanel.ui.tui import XVCpanel


def find_library(base: Path) -> Path:
    lib = base / "library"
    if lib.is_dir():
        return lib
    return base


def add_local_tools(base: Path) -> None:
    """Make runtimes installed by install.ps1 visible without global PATH edits."""
    tools = base / ".tools"
    if not tools.is_dir():
        return
    paths = {str(path.parent) for path in tools.rglob("*.exe")}
    cargo = Path.home() / ".cargo" / "bin"
    if cargo.is_dir():
        paths.add(str(cargo))
    if paths:
        os.environ["PATH"] = os.pathsep.join(sorted(paths)) + os.pathsep + os.environ.get("PATH", "")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="xvcpanel",
        description="Browse, run, route, and modulate code visuals",
    )
    parser.add_argument(
        "-d", "--dir",
        type=Path,
        default=None,
        help="project root (default: script parent)",
    )
    parser.add_argument(
        "--spout-name",
        default="XVCpanel",
        help="Spout sender name (default: XVCpanel)",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="list all visuals and exit",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="enable debug logging",
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    project_root = args.dir or Path(__file__).resolve().parent.parent
    add_local_tools(project_root)
    library_path = find_library(project_root)

    spout = SpoutBridge(name=args.spout_name)

    if args.list:
        visuals = scan_library(library_path)
        if not visuals:
            print("no visuals found in", library_path)
            sys.exit(0)
        print(f"\n{'Name':<30} {'Framework':<15} {'Tags':<25} {'Outputs'}")
        print("-" * 85)
        for v in visuals:
            tags = ", ".join(v.tags) if v.tags else "—"
            outputs = ", ".join(output.protocol for output in v.outputs)
            print(f"{v.name:<30} {v.framework.value:<15} {tags:<25} {outputs}")
        print(f"\n{len(visuals)} visual(s) found")
        sys.exit(0)

    app = XVCpanel(library_path=library_path, spout=spout)
    app.run()


if __name__ == "__main__":
    main()
