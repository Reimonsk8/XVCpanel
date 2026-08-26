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
    CUSTOM = "custom"


class VisualStatus(str, enum.Enum):
    IDLE = "idle"
    BUILDING = "building"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


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
    status: VisualStatus = VisualStatus.IDLE
    process: object = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: dict, base_path: Path) -> Visual:
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
        )

    def filter_key(self) -> str:
        return f"{self.name} {self.framework.value} {' '.join(self.tags)}".lower()

    def missing_deps(self) -> list[str]:
        """Return list of required tools not found on PATH."""
        return [r for r in self.requires if shutil.which(r) is None]

    def ready(self) -> bool:
        """True if all deps are met."""
        return len(self.missing_deps()) == 0
