from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path

from xvcpanel.models.visual import Visual, VisualStatus

log = logging.getLogger(__name__)


async def build_visual(visual: Visual) -> tuple[bool, str]:
    if not visual.build_cmd:
        return True, "no build command"

    visual.status = VisualStatus.BUILDING
    log.info("building %s: %s", visual.name, visual.build_cmd)

    try:
        proc = await asyncio.create_subprocess_shell(
            visual.build_cmd,
            cwd=str(visual.path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = (stdout or b"").decode(errors="replace") + (stderr or b"").decode(errors="replace")

        if proc.returncode != 0:
            visual.status = VisualStatus.ERROR
            return False, output

        return True, output
    except Exception as e:
        visual.status = VisualStatus.ERROR
        return False, str(e)


async def run_visual(visual: Visual) -> tuple[bool, str]:
    if not visual.run_cmd:
        return False, "no run command"

    ok, output = await build_visual(visual)
    if not ok:
        return False, f"build failed:\n{output}"

    log.info("running %s: %s", visual.name, visual.run_cmd)
    try:
        proc = await asyncio.create_subprocess_shell(
            visual.run_cmd,
            cwd=str(visual.path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        visual.process = proc
        visual.status = VisualStatus.RUNNING
        return True, "started"
    except Exception as e:
        visual.status = VisualStatus.ERROR
        return False, str(e)


def stop_visual(visual: Visual) -> bool:
    proc = visual.process
    if proc is None or proc.returncode is not None:
        visual.status = VisualStatus.STOPPED
        return True

    try:
        proc.terminate()
        visual.status = VisualStatus.STOPPED
        visual.process = None
        return True
    except Exception:
        log.exception("failed to stop %s", visual.name)
        return False
