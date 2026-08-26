from __future__ import annotations

import json
import logging
from pathlib import Path

from xvcpanel.models.visual import Visual

log = logging.getLogger(__name__)


def scan_library(library_path: Path) -> list[Visual]:
    visuals: list[Visual] = []
    if not library_path.is_dir():
        log.warning("library path does not exist: %s", library_path)
        return visuals

    for xvc_json in library_path.rglob("xvc.json"):
        try:
            data = json.loads(xvc_json.read_text(encoding="utf-8"))
            base = xvc_json.parent
            visuals.append(Visual.from_dict(data, base))
            log.info("loaded visual: %s (%s)", data.get("name"), base)
        except Exception:
            log.exception("failed to load %s", xvc_json)

    visuals.sort(key=lambda v: (v.framework.value, v.name))
    return visuals
