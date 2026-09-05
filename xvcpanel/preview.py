"""Render a PNG frame into the current WezTerm/Kitty pane as it changes.

Pure-Python Kitty Graphics Protocol — no external binaries, no deps.
Usage: preview.py [--width CELLS] <frame.png>

Redraws on mtime change (fs-only bridge; the visuals write frame.png).
"""

from __future__ import annotations

import base64
import struct
import sys
import time
from pathlib import Path

INTERVAL = 0.25
CHUNK = 4096
STALE = 6.0

# kitty cells are ~2x as tall as wide; adjust placement rows to keep aspect
CELL_ASPECT = 2.0


def png_dims(path: Path) -> tuple[int, int] | None:
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
    except OSError:
        return None
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def kitty_show(path: Path, width_cells: int | None) -> str:
    """Return the escape sequence that draws `path` into the pane."""
    payload = base64.b64encode(path.read_bytes()).decode()
    chunks = [payload[i : i + CHUNK] for i in range(0, len(payload), CHUNK)]

    out: list[str] = []
    for i, chunk in enumerate(chunks):
        more = "0" if i == len(chunks) - 1 else "1"
        out.append(f"\x1b_Ga=T,f=100,q=2,m={more};{chunk}\x1b\\")

    cols = width_cells or 46
    dims = png_dims(path)
    if dims:
        rows = max(1, round(cols * dims[1] / dims[0] / CELL_ASPECT))
    else:
        rows = max(1, cols // 2)
    out.append(f"\x1b_Ga=p,q=2,X=0,Y=0,c={cols},r={rows};\x1b\\")
    return "".join(out)


def main(argv: list[str]) -> int:
    width = None
    frame = Path("frame.png")
    if argv and argv[0] == "--width" and len(argv) >= 3:
        width = int(argv[1])
        frame = Path(argv[2])
    elif argv:
        frame = Path(argv[0])

    print(f"[preview] watching {frame} (run a visual from the panel; 4 fps)")
    last: float | None = None
    reported_missing = False
    while True:
        try:
            mtime = frame.stat().st_mtime
        except OSError:
            mtime = None
        if mtime is not None and time.time() - mtime > STALE:
            mtime = None
        if mtime is None:
            if not reported_missing:
                sys.stdout.write("\x1b[2J\x1b[H[preview] no frame yet - run the visual from xvcpanel\n")
                sys.stdout.flush()
                reported_missing = True
            time.sleep(INTERVAL)
            continue
        reported_missing = False
        if mtime != last:
            last = mtime
            sys.stdout.write("\x1b[2J\x1b[H" + kitty_show(frame, width))
            sys.stdout.flush()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))