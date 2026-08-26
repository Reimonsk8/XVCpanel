"""XVCpanel health check — run before pushing to catch import/config errors."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ERRORS = []


def check(label, fn):
    try:
        fn()
        print(f"  OK  {label}")
    except Exception as e:
        ERRORS.append(f"{label}: {e}")
        print(f"  FAIL  {label}: {e}")


print("XVCpanel health check")
print()

# ── Imports ───────────────────────────────────────────────────────────────────
print("[imports]")
check("xvcpanel.models.visual", lambda: __import__("xvcpanel.models.visual"))
check("xvcpanel.models.visual.Output", lambda: __import__("xvcpanel.models.visual", fromlist=["Output"]))
check("xvcpanel.models.visual.Parameter", lambda: __import__("xvcpanel.models.visual", fromlist=["Parameter"]))
check("xvcpanel.loader.scanner", lambda: __import__("xvcpanel.loader.scanner"))
check("xvcpanel.loader.runner", lambda: __import__("xvcpanel.loader.runner"))
check("xvcpanel.controls.osc", lambda: __import__("xvcpanel.controls.osc"))
check("xvcpanel.spout.bridge", lambda: __import__("xvcpanel.spout.bridge"))
check("xvcpanel.ui.tui", lambda: __import__("xvcpanel.ui.tui"))
print()

# ── xvc.json parsing ─────────────────────────────────────────────────────────
print("[xvc.json files]")
library = ROOT / "library"
if not library.is_dir():
    ERRORS.append("library/ directory not found")
    print("  FAIL  library/ directory not found")
else:
    for xvc in sorted(library.rglob("xvc.json")):
        def _check_xvc(path=xvc):
            data = json.loads(path.read_text("utf-8"))
            assert "name" in data, "missing 'name'"
            assert "framework" in data, "missing 'framework'"
            assert "run" in data or "outputs" in data, "missing 'run' or 'outputs'"
            from xvcpanel.models.visual import Visual
            vis = Visual.from_dict(data, path.parent)
            assert vis.name, "empty name"
            assert vis.framework, "empty framework"
            if vis.outputs:
                assert all(o.name for o in vis.outputs), "output missing name"
            if vis.parameters:
                for p in vis.parameters:
                    assert p.name and p.address, f"parameter missing name/address"
        check(str(xvc.relative_to(ROOT)), _check_xvc)
print()

# ── Scanner ───────────────────────────────────────────────────────────────────
print("[scanner]")
def _check_scan():
    from xvcpanel.loader.scanner import scan_library
    visuals = scan_library(library)
    assert len(visuals) >= 5, f"expected >=5 visuals, got {len(visuals)}"
    for v in visuals:
        assert v.name, f"visual without name: {v}"
        assert v.outputs, f"{v.name} has no outputs"
check("scan_library finds 5+ visuals", _check_scan)
print()

# ── Runner ────────────────────────────────────────────────────────────────────
print("[runner]")
def _check_runner_no_cmd():
    from xvcpanel.loader.runner import build_visual, stop_visual
    from xvcpanel.models.visual import Visual, Framework
    v = Visual(name="test", framework=Framework.CUSTOM, path=ROOT)
    ok, _ = build_visual(v)
    assert ok, "build_visual with empty cmd should return True"
check("build_visual empty cmd", _check_runner_no_cmd)

def _check_runner_bad_cmd():
    from xvcpanel.loader.runner import build_visual
    from xvcpanel.models.visual import Visual, Framework
    v = Visual(name="test", framework=Framework.CUSTOM, path=ROOT, build_cmd="nonexistent_tool_xyz")
    ok, _ = build_visual(v)
    assert not ok, "build_visual with bad cmd should return False"
check("build_visual bad cmd", _check_runner_bad_cmd)

def _check_stop_no_proc():
    from xvcpanel.loader.runner import stop_visual
    from xvcpanel.models.visual import Visual, Framework
    v = Visual(name="test", framework=Framework.CUSTOM, path=ROOT)
    assert stop_visual(v), "stop_visual with no process should return True"
check("stop_visual no process", _check_stop_no_proc)
print()

# ── OSC ───────────────────────────────────────────────────────────────────────
print("[osc]")
def _check_osc_import():
    from xvcpanel.controls.osc import send_float
    assert callable(send_float)
check("send_float callable", _check_osc_import)
print()

# ── TUI composition ───────────────────────────────────────────────────────────
print("[tui]")
def _check_tui_compose():
    from xvcpanel.ui.tui import XVCpanel
    app = XVCpanel(library_path=library)
    # verify bindings exist
    binding_keys = {b.key for b in app.BINDINGS}
    assert "enter" in binding_keys, "missing enter binding"
    assert "b" in binding_keys, "missing b binding"
    assert "o" in binding_keys, "missing o binding"
check("XVCpanel bindings", _check_tui_compose)
print()

# ── Summary ───────────────────────────────────────────────────────────────────
if ERRORS:
    print(f"FAILED: {len(ERRORS)} error(s)")
    for e in ERRORS:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL PASSED")
    sys.exit(0)
