from __future__ import annotations

import importlib.util
import platform
import sys


def check_environment() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pytest_available": importlib.util.find_spec("pytest") is not None,
        "opencv_optional": importlib.util.find_spec("cv2") is not None,
        "ocr_optional": importlib.util.find_spec("pytesseract") is not None,
        "selenium_optional": importlib.util.find_spec("selenium") is not None,
    }
