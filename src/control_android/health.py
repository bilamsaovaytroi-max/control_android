from __future__ import annotations

import importlib.util
import json
import platform
import shutil
import sys


def check_environment() -> dict[str, object]:
    """Return a serializable environment snapshot for tests and diagnostics."""
    return {
        "python": sys.version.split()[0],
        "python_required": ">=3.11",
        "python_ok": sys.version_info >= (3, 11),
        "platform": platform.platform(),
        "pytest_available": importlib.util.find_spec("pytest") is not None,
        "adb": shutil.which("adb"),
        "scrcpy": shutil.which("scrcpy"),
        "tesseract": shutil.which("tesseract"),
    }


def collect_health() -> list[dict[str, object]]:
    env = check_environment()
    items: list[dict[str, object]] = [
        {
            "name": "python",
            "status": "PASS" if env["python_ok"] else "FAIL",
            "required": True,
            "detail": env["python"],
        }
    ]
    for name in ("adb", "scrcpy", "tesseract"):
        path = env[name]
        items.append(
            {
                "name": name,
                "status": "PASS" if path else "WARN",
                "required": False,
                "detail": path or f"{name} not found on PATH",
            }
        )
    return items


def main() -> int:
    items = collect_health()
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 1 if any(item["required"] and item["status"] != "PASS" for item in items) else 0


if __name__ == "__main__":
    raise SystemExit(main())
