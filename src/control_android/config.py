from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    adb_path: str = "adb"
    adb_timeout: int = 10
    ui_dump_timeout: int = 8
    page_timeout: int = 45
    vision_min_confidence: float = 0.86
    retry_limit: int = 3
    stop_on_login: bool = True
    stop_on_challenge: bool = True

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "AppConfig":
        cfg = cls(**data)
        cfg.validate()
        return cfg

    def validate(self) -> None:
        if self.adb_timeout <= 0:
            raise ValueError("adb_timeout must be > 0")
        if self.ui_dump_timeout <= 0:
            raise ValueError("ui_dump_timeout must be > 0")
        if self.page_timeout <= 0:
            raise ValueError("page_timeout must be > 0")
        if self.retry_limit < 0:
            raise ValueError("retry_limit must be >= 0")
        if not 0.0 <= self.vision_min_confidence <= 1.0:
            raise ValueError("vision_min_confidence must be between 0 and 1")


def load_config(path: str | Path) -> AppConfig:
    file_path = Path(path)
    raw = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a mapping")
    return AppConfig.from_mapping(raw)
