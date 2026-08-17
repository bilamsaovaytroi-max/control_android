"""Repository-root import shim for the src-layout package.

This keeps developer commands such as ``python -m control_android.health``
working from the repository root without changing the production package
layout under ``src/control_android``.
"""

from __future__ import annotations

from pathlib import Path

_src_package = Path(__file__).resolve().parent.parent / "src" / "control_android"
if _src_package.is_dir():
    __path__.append(str(_src_package))
