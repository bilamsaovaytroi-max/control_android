from __future__ import annotations

import argparse
import json
from .health import check_environment
from .adb import AdbTransport, AdbError


def main() -> int:
    parser = argparse.ArgumentParser(prog="control_android")
    parser.add_argument("command", choices=["health", "devices"])
    args = parser.parse_args()
    if args.command == "health":
        print(json.dumps(check_environment(), indent=2))
        return 0
    try:
        print(json.dumps([{"serial": s, "state": st} for s, st in AdbTransport().devices()], indent=2))
        return 0
    except AdbError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
