from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class Settings:
    project_root: Path
    adb_path: str = "adb"
    command_timeout_seconds: float = 20.0
    log_level: str = "INFO"
    artifact_dir: Path = Path("artifacts")

    @classmethod
    def from_file(cls, path: Path) -> "Settings":
        data = json.loads(path.read_text(encoding="utf-8"))
        root = path.parent.parent
        return cls(project_root=root, adb_path=data.get("adb_path", "adb"),
                   command_timeout_seconds=float(data.get("command_timeout_seconds", 20)),
                   log_level=data.get("log_level", "INFO"),
                   artifact_dir=root / data.get("artifact_dir", "artifacts"))
