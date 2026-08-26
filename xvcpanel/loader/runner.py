from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from xvcpanel.models.visual import Visual, VisualStatus

log = logging.getLogger(__name__)


def build_visual(visual: Visual) -> tuple[bool, str]:
    if not visual.build_cmd:
        return True, "no build command"

    visual.status = VisualStatus.BUILDING
    log.info("building %s: %s", visual.name, visual.build_cmd)

    try:
        result = subprocess.run(
            visual.build_cmd,
            shell=True,
            cwd=str(visual.path),
            capture_output=True,
            timeout=120,
        )
        output = result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")

        if result.returncode != 0:
            visual.status = VisualStatus.ERROR
            return False, output

        return True, output
    except subprocess.TimeoutExpired:
        visual.status = VisualStatus.ERROR
        return False, "build timed out after 120s"
    except Exception as e:
        visual.status = VisualStatus.ERROR
        return False, str(e)


def run_visual(visual: Visual) -> tuple[bool, str]:
    if not visual.run_cmd:
        return False, "no run command"

    ok, output = build_visual(visual)
    if not ok:
        return False, f"build failed:\n{output}"

    log.info("running %s: %s", visual.name, visual.run_cmd)
    try:
        proc = subprocess.Popen(
            visual.run_cmd,
            shell=True,
            cwd=str(visual.path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        visual.process = proc
        visual.status = VisualStatus.RUNNING
        return True, "started"
    except Exception as e:
        visual.status = VisualStatus.ERROR
        return False, str(e)


def stop_visual(visual: Visual) -> bool:
    proc = visual.process
    if proc is None or proc.poll() is not None:
        visual.status = VisualStatus.STOPPED
        visual.process = None
        return True

    try:
        proc.terminate()
        proc.wait(timeout=5)
        visual.status = VisualStatus.STOPPED
        visual.process = None
        return True
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        visual.status = VisualStatus.STOPPED
        visual.process = None
        return False
