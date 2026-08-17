from __future__ import annotations

import json
import shutil
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HealthItem:
    name: str
    status: str
    detail: str
    required: bool


def _tool_check(name: str, required: bool = False) -> HealthItem:
    path = shutil.which(name)
    if path:
        return HealthItem(name=name, status="PASS", detail=path, required=required)
    return HealthItem(
        name=name,
        status="FAIL" if required else "WARN",
        detail=f"{name} not found on PATH",
        required=required,
    )


def collect_health() -> list[HealthItem]:
    py_ok = sys.version_info >= (3, 11)
    items = [
        HealthItem(
            name="python",
            status="PASS" if py_ok else "FAIL",
            detail=sys.version.split()[0],
            required=True,
        ),
        _tool_check("adb", required=False),
        _tool_check("scrcpy", required=False),
        _tool_check("tesseract", required=False),
    ]
    return items


def main() -> int:
    items = collect_health()
    print(json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2))
    return 1 if any(item.required and item.status != "PASS" for item in items) else 0


if __name__ == "__main__":
    raise SystemExit(main())
