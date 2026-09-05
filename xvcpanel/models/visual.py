from __future__ import annotations

import enum
import shutil
from dataclasses import dataclass, field
from pathlib import Path


class Framework(str, enum.Enum):
    OPENFRAMEWORKS = "openframeworks"
    NANNOU = "nannou"
    PROCESSING = "processing"
    GLSL = "glsl"
    THREEJS = "threejs"
    CINDER = "cinder"
    TOUCHDESIGNER = "touchdesigner"
    VVVV = "vvvv"
    HYDRA = "hydra"
    P5JS = "p5js"
    MAX = "max"
    RESOLUME_WIRE = "resolume-wire"
    NOTCH = "notch"
    UNITY = "unity"
    UNREAL = "unreal"
    GODOT = "godot"
    LOVE2D = "love2d"
    ISF = "isf"
    CUSTOM = "custom"


class VisualStatus(str, enum.Enum):
    IDLE = "idle"
    BUILDING = "building"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class Output:
    name: str
    protocol: str = "window"
    run_cmd: str = ""


@dataclass
class Parameter:
    name: str
    address: str
    minimum: float = 0.0
    maximum: float = 1.0
    default: float = 0.5
    value: float = 0.5
    lfo: bool = False
    lfo_rate: float = 0.25
    lfo_curve: str = "sine"

    def set_value(self, value: float) -> None:
        self.value = min(self.maximum, max(self.minimum, value))


@dataclass
class Visual:
    name: str
    framework: Framework
    path: Path
    build_cmd: str = ""
    run_cmd: str = ""
    spout: bool = False
    tags: list[str] = field(default_factory=list)
    description: str = ""
    requires: list[str] = field(default_factory=list)
    install_hint: str = ""
    outputs: list[Output] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    osc_host: str = "127.0.0.1"
    osc_port: int = 0
    output_index: int = 0
    route: list[str] = field(default_factory=lambda: ["preview"])
    status: VisualStatus = VisualStatus.IDLE
    process: object = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: dict, base_path: Path) -> Visual:
        outputs = [Output(**output) for output in data.get("outputs", [])]
        if not outputs:
            outputs = [Output("Window", "window", data.get("run", ""))]
        parameters = []
        for item in data.get("parameters", []):
            default = float(item.get("default", 0.5))
            parameters.append(Parameter(
                name=item["name"],
                address=item["address"],
                minimum=float(item.get("min", 0.0)),
                maximum=float(item.get("max", 1.0)),
                default=default,
                value=default,
            ))
        osc = data.get("osc", {})
        return cls(
            name=data.get("name", base_path.name),
            framework=Framework(data.get("framework", "custom")),
            path=base_path,
            build_cmd=data.get("build", ""),
            run_cmd=data.get("run", ""),
            spout=data.get("spout", False),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            requires=data.get("requires", []),
            install_hint=data.get("install_hint", ""),
            outputs=outputs,
            parameters=parameters,
            osc_host=osc.get("host", "127.0.0.1"),
            osc_port=int(osc.get("port", 0)),
        )

    @property
    def output(self) -> Output:
        return self.outputs[self.output_index]

    def select_next_output(self) -> Output:
        self.output_index = (self.output_index + 1) % len(self.outputs)
        return self.output

    def has_route(self, sink: str) -> bool:
        return sink in self.route

    def toggle_route(self, sink: str) -> bool:
        """Flip a route sink on/off; returns its new state."""
        if sink in self.route:
            self.route = [s for s in self.route if s != sink]
            return False
        self.route = [*self.route, sink]
        return True

    def filter_key(self) -> str:
        return f"{self.name} {self.framework.value} {' '.join(self.tags)}".lower()

    def missing_deps(self) -> list[str]:
        """Return list of required tools not found on PATH."""
        return [r for r in self.requires if shutil.which(r) is None]

    def ready(self) -> bool:
        """True if all deps are met."""
        return len(self.missing_deps()) == 0

    def _source_candidates(self) -> list[str]:
        fw = self.framework
        if fw == Framework.GLSL:
            return ["data/*.glsl", "*.glsl"]
        if fw == Framework.PROCESSING:
            return ["*.pde"]
        if fw == Framework.NANNOU:
            return ["src/main.rs", "*.rs"]
        if fw == Framework.OPENFRAMEWORKS:
            return ["src/ofApp.cpp", "src/*.cpp"]
        return ["src/main.rs", "*.pde", "data/*.glsl", "*.glsl", "src/ofApp.cpp", "src/*.cpp"]

    @property
    def source_path(self) -> Path | None:
        """Primary editable source file for this visual (or None)."""
        for pattern in self._source_candidates():
            hits = sorted(self.path.glob(pattern))
            if hits:
                return hits[0]
        hits = [f for f in self.path.rglob("*")
                if f.suffix in (".rs", ".pde", ".glsl", ".cpp", ".js", ".py")
                and not any(part in ("target", "data") for part in f.parts)]
        return hits[0] if hits else None
