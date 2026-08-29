from __future__ import annotations

import logging
import os
import platform
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

from xvcpanel.models.visual import Visual, VisualStatus

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


def _find_terminal():
    if IS_WINDOWS:
        wt = shutil.which("wt")
        if wt:
            return "wt"
        return "cmd"
    for term in ["gnome-terminal", "konsole", "alacritty", "kitty", "xterm"]:
        if shutil.which(term):
            return term
    return "bash"


TERM = _find_terminal()


def _minimal_path(visual_path: Path) -> str:
    """Build a short PATH with just tool dirs + Windows essentials (absolute)."""
    win_root = os.environ.get("SystemRoot", r"C:\Windows")
    essential = [
        os.path.join(win_root, "System32"),
        os.path.join(win_root),
        str(Path.home() / ".cargo" / "bin"),
    ]
    tools = next(
        (parent / ".tools" for parent in (visual_path, *visual_path.parents) if (parent / ".tools").is_dir()),
        None,
    )
    if tools:
        tools = Path(tools).resolve()
        for exe in tools.rglob("glslViewer.exe"):
            if exe.is_file():
                essential.append(str(exe.parent))
        for exe in tools.rglob("Processing.exe"):
            if exe.is_file():
                essential.append(str(exe.parent))
        proc_dir = tools / "processing" / "Processing"
        if proc_dir.is_dir():
            essential.append(str(proc_dir))
    seen = set()
    result = []
    for d in essential:
        if d not in seen:
            seen.add(d)
            result.append(d)
    return ";".join(result)


def build_visual(visual: Visual) -> tuple[bool, str]:
    if not visual.build_cmd:
        return True, "no build command"

    visual.status = VisualStatus.BUILDING
    log.info("building %s: %s", visual.name, visual.build_cmd)

    try:
        env = None
        if IS_WINDOWS:
            env = dict(os.environ)
            env["PATH"] = _minimal_path(visual.path)
        result = subprocess.run(
            visual.build_cmd,
            shell=True,
            cwd=str(visual.path),
            capture_output=True,
            timeout=300,
            env=env,
        )
        output = result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
        if result.returncode != 0:
            visual.status = VisualStatus.ERROR
            return False, output
        visual.status = VisualStatus.IDLE
        return True, output
    except subprocess.TimeoutExpired:
        visual.status = VisualStatus.ERROR
        return False, "build timed out after 300s"
    except Exception as e:
        visual.status = VisualStatus.ERROR
        return False, str(e)


def run_visual(visual: Visual) -> tuple[bool, str]:
    run = visual.output.run_cmd or visual.run_cmd
    if not run:
        return False, "no run command"

    log.info("running %s: %s", visual.name, run)
    try:
        cwd = str(visual.path)

        if IS_WINDOWS:
            abs_cwd = str(Path(cwd).resolve())
            run = run.replace("<SKETCH>", abs_cwd)
            bat = os.path.join(tempfile.gettempdir(), f"xvc_{visual.name}.bat")
            with open(bat, "w") as f:
                f.write("@echo off\n")
                f.write('set "PATH=' + _minimal_path(visual.path) + '"\n')
                f.write("cd /d " + abs_cwd + "\n")
                f.write(run + "\n")

            if TERM == "wt":
                proc = subprocess.Popen(
                    ["wt", "new-tab", "--title", visual.name, "cmd", "/k", bat],
                )
            else:
                proc = subprocess.Popen(
                    ["cmd", "/k", bat],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
        else:
            shell_cmd = "cd " + cwd + " && " + run
            if TERM == "gnome-terminal":
                proc = subprocess.Popen(["gnome-terminal", "--", "bash", "-c", shell_cmd])
            elif TERM in ("alacritty", "kitty"):
                proc = subprocess.Popen([TERM, "-e", "bash", "-c", shell_cmd])
            elif TERM == "konsole":
                proc = subprocess.Popen(["konsole", "-e", "bash", "-c", shell_cmd])
            else:
                proc = subprocess.Popen(["bash", "-c", shell_cmd])

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
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                timeout=5,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
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
