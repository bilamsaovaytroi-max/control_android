from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Iterator

from .adb import AdbTransport


class DeviceManager:
    """Per-device operations with an isolated lock and transport."""

    def __init__(self, transport: AdbTransport | None = None):
        self.transport = transport or AdbTransport()
        self._locks: dict[str, Lock] = {}

    def _lock_for(self, serial: str) -> Lock:
        if serial not in self._locks:
            self._locks[serial] = Lock()
        return self._locks[serial]

    @contextmanager
    def reserve(self, serial: str, timeout: float | None = None) -> Iterator[None]:
        lock = self._lock_for(serial)
        acquired = lock.acquire(timeout=timeout) if timeout is not None else lock.acquire()
        if not acquired:
            raise TimeoutError(f"device is busy: {serial}")
        try:
            yield
        finally:
            lock.release()

    def screenshot(self, serial: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.transport.run_bytes(["exec-out", "screencap", "-p"], serial=serial))
        return destination

    def ui_xml(self, serial: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.transport.dump_ui_xml(serial), encoding="utf-8")
        return destination
