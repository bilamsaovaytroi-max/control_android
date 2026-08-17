from __future__ import annotations

from dataclasses import dataclass
import subprocess
from typing import Sequence


class AdbError(RuntimeError):
    pass


@dataclass(frozen=True)
class AdbResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class AdbTransport:
    def __init__(self, adb_path: str = "adb", timeout: float = 20.0):
        self.adb_path = adb_path
        self.timeout = timeout

    def run(self, args: Sequence[str], serial: str | None = None) -> AdbResult:
        command = [self.adb_path]
        if serial:
            command += ["-s", serial]
        command += list(args)
        try:
            completed = subprocess.run(command, capture_output=True, text=True,
                                       timeout=self.timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AdbError(f"ADB command failed: {' '.join(command)}: {exc}") from exc
        result = AdbResult(tuple(command), completed.returncode, completed.stdout, completed.stderr)
        if result.returncode != 0:
            raise AdbError(f"ADB returned {result.returncode}: {result.stderr.strip()}")
        return result

    def run_bytes(self, args: Sequence[str], serial: str | None = None) -> bytes:
        """Run an ADB command whose stdout is binary (for example screencap)."""
        command = [self.adb_path]
        if serial:
            command += ["-s", serial]
        command += list(args)
        try:
            completed = subprocess.run(command, capture_output=True, timeout=self.timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AdbError(f"ADB binary command failed: {' '.join(command)}: {exc}") from exc
        if completed.returncode != 0:
            error = completed.stderr.decode("utf-8", errors="replace").strip()
            raise AdbError(f"ADB returned {completed.returncode}: {error}")
        return completed.stdout

    def devices(self) -> list[tuple[str, str]]:
        lines = self.run(["devices"]).stdout.splitlines()[1:]
        return [tuple(line.split("\t", 1)) for line in lines if "\t" in line]

    def shell(self, command: Sequence[str], serial: str) -> str:
        return self.run(["shell", *command], serial=serial).stdout

    def dump_ui_xml(self, serial: str) -> str:
        return self.shell(["uiautomator", "dump", "/dev/tty"], serial)
