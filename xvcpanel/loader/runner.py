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


def _tool_dirs() -> list[str]:
    """Collect directories containing tools from .tools/ and ~/.cargo/bin."""
    dirs = []
    tools = Path(os.environ.get("XVCPANEL_ROOT", ".")) / ".tools"
    if tools.is_dir():
        for exe in tools.rglob("glslViewer.exe" if IS_WINDOWS else "glslViewer"):
            if exe.is_file():
                dirs.append(str(exe.parent))
        for exe in tools.rglob("processing-java*"):
            if exe.is_file():
                dirs.append(str(exe.parent))
    cargo = Path.home() / ".cargo" / "bin"
    if cargo.is_dir():
        dirs.append(str(cargo))
    return dirs


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

        visual.status = VisualStatus.IDLE
        return True, output
    except subprocess.TimeoutExpired:
        visual.status = VisualStatus.ERROR
        return False, "build timed out after 120s"
    except Exception as e:
        visual.status = VisualStatus.ERROR
        return False, str(e)


def run_visual(visual: Visual) -> tuple[bool, str]:
    run = visual.output.run_cmd or visual.run_cmd
    if not run:
        return False, "no run command"

    build = visual.build_cmd
    command = f"{build} && {run}" if build else run

    log.info("running %s: %s", visual.name, command)
    try:
        cwd = str(visual.path)

        if IS_WINDOWS:
            full_path = os.environ.get("PATH", "")
            tool_path = ";".join(_tool_dirs())
            if tool_path:
                full_path = tool_path + ";" + full_path
            bat = os.path.join(tempfile.gettempdir(), f"xvc_{visual.name}.bat")
            with open(bat, "w") as f:
                f.write(f'@echo off\r\nset "PATH={full_path}"\r\ncd /d {cwd}\r\n{command}\r\n')

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
            shell_cmd = f"cd {cwd} && {command}"
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
