from __future__ import annotations

from dataclasses import dataclass
import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable

from .adb import AdbError, AdbTransport
from .item_information import BUTTON_LABEL as ITEM_INFORMATION_BUTTON_LABEL
from .item_information import run_item_information_workflow


ONLINE_STATE = "device"


@dataclass(frozen=True)
class DeviceRecord:
    serial: str
    state: str

    @property
    def usable(self) -> bool:
        return self.state == ONLINE_STATE

    @property
    def label(self) -> str:
        return f"{self.serial} [{self.state}]"


class DeviceConnectionModel:
    """Small, UI-independent state model for ADB discovery and selection."""

    def __init__(self, transport: AdbTransport | None = None):
        self.transport = transport or AdbTransport()
        self.devices: list[DeviceRecord] = []
        self.connected: DeviceRecord | None = None
        self.status = "Not connected"
        self.adb_ready = False
        self.last_error: str | None = None
        self.last_workflow_status: str | None = None
        self.last_workflow_evidence_dir: str | None = None

    def refresh(self) -> list[DeviceRecord]:
        try:
            discovered = self.transport.devices()
        except AdbError as exc:
            self.devices = []
            self.connected = None
            self.adb_ready = False
            self.last_error = str(exc)
            self.status = "ADB error"
            return []

        self.devices = [DeviceRecord(serial, state) for serial, state in discovered]
        self.adb_ready = True
        self.last_error = None

        if self.connected and not any(
            item.serial == self.connected.serial and item.usable for item in self.devices
        ):
            self.connected = None

        if not self.devices:
            self.status = "No Android device detected"
        elif self.connected:
            self.status = "Connected"
        elif not any(item.usable for item in self.devices):
            self.status = "No usable Android device"
        else:
            self.status = "Not connected"
        return list(self.devices)

    def connect(self, selected_serial: str | None = None) -> DeviceRecord | None:
        usable = [item for item in self.devices if item.usable]
        if not usable:
            if not self.devices:
                self.status = "No Android device detected"
            elif any(item.state == "unauthorized" for item in self.devices):
                self.status = "Unauthorized"
            elif any(item.state == "offline" for item in self.devices):
                self.status = "Offline"
            else:
                self.status = "No usable Android device"
            self.connected = None
            return None

        target: DeviceRecord | None = None
        if len(usable) == 1:
            target = usable[0]
        elif selected_serial:
            target = next((item for item in usable if item.serial == selected_serial), None)

        if target is None:
            selected = next((item for item in self.devices if item.serial == selected_serial), None)
            if selected is not None and selected.state == "unauthorized":
                self.status = "Unauthorized"
            elif selected is not None and selected.state == "offline":
                self.status = "Offline"
            else:
                self.status = "Select a usable device"
            self.connected = None
            return None

        self.connected = target
        self.status = "Connected"
        return target

    def run_item_information(self) -> str:
        if self.connected is None:
            self.status = "Connect a device first"
            self.last_workflow_status = None
            self.last_workflow_evidence_dir = None
            return self.status

        result = run_item_information_workflow(self.connected.serial)
        self.last_workflow_status = result.status
        self.last_workflow_evidence_dir = result.evidence_dir
        self.status = f"{ITEM_INFORMATION_BUTTON_LABEL}: {result.status}"
        return self.status


class ControlAndroidApp:
    def __init__(self, root: tk.Tk, model: DeviceConnectionModel | None = None):
        self.root = root
        self.model = model or DeviceConnectionModel()
        self._busy = False
        self._ui_queue: queue.Queue[Callable[[], None]] = queue.Queue()

        self.root.title("CONTROL ANDROID")
        self.root.minsize(520, 370)

        self.adb_status_var = tk.StringVar(value="ADB Status: Checking...")
        self.device_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Status: Not connected")
        self.serial_var = tk.StringVar(value="Serial: -")
        self.state_var = tk.StringVar(value="State: -")
        self.workflow_var = tk.StringVar(value="Workflow: -")

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="CONTROL ANDROID", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 18)
        )
        ttk.Label(frame, textvariable=self.adb_status_var).grid(row=1, column=0, sticky="w")
        ttk.Label(frame, text="Device").grid(row=2, column=0, sticky="w", pady=(16, 4))

        self.device_combo = ttk.Combobox(
            frame, textvariable=self.device_var, state="readonly", width=54
        )
        self.device_combo.grid(row=3, column=0, sticky="ew")

        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, sticky="w", pady=16)
        self.connect_button = ttk.Button(buttons, text="Connect Device", command=self.connect_device)
        self.connect_button.pack(side="left")
        self.refresh_button = ttk.Button(buttons, text="Refresh", command=self.refresh_devices)
        self.refresh_button.pack(side="left", padx=(10, 0))
        self.item_information_button = ttk.Button(
            buttons, text=ITEM_INFORMATION_BUTTON_LABEL, command=self.run_item_information
        )
        self.item_information_button.pack(side="left", padx=(10, 0))

        ttk.Separator(frame).grid(row=5, column=0, sticky="ew", pady=(4, 14))
        ttk.Label(frame, textvariable=self.status_var).grid(row=6, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.serial_var).grid(row=7, column=0, sticky="w", pady=(8, 0))
        ttk.Label(frame, textvariable=self.state_var).grid(row=8, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.workflow_var).grid(row=9, column=0, sticky="w", pady=(8, 0))

        self.root.after(50, self._drain_ui_queue)
        self.root.after(100, self.refresh_devices)

    def _selected_serial(self) -> str | None:
        label = self.device_var.get()
        for item in self.model.devices:
            if item.label == label:
                return item.serial
        return None

    def _set_busy(self, busy: bool, status: str | None = None) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.connect_button.configure(state=state)
        self.refresh_button.configure(state=state)
        self.item_information_button.configure(state=state)
        if status:
            self.status_var.set(f"Status: {status}")

    def _run_background(
        self,
        work: Callable[[], None],
        on_done: Callable[[], None],
        working_status: str,
    ) -> None:
        if self._busy:
            return
        self._set_busy(True, working_status)

        def runner() -> None:
            try:
                work()
            finally:
                self._ui_queue.put(on_done)

        threading.Thread(target=runner, daemon=True).start()

    def _drain_ui_queue(self) -> None:
        while True:
            try:
                callback = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            callback()
        self.root.after(50, self._drain_ui_queue)

    def refresh_devices(self) -> None:
        previous = self._selected_serial()

        def do_refresh() -> None:
            self.model.refresh()

        def done() -> None:
            self._render(previous_serial=previous)
            self._set_busy(False)

        self._run_background(do_refresh, done, "Refreshing...")

    def connect_device(self) -> None:
        selected = self._selected_serial()

        def do_connect() -> None:
            self.model.refresh()
            self.model.connect(selected)

        def done() -> None:
            self._render(previous_serial=selected)
            self._set_busy(False)

        self._run_background(do_connect, done, "Connecting...")

    def run_item_information(self) -> None:
        if self.model.connected is None:
            self.status_var.set("Status: Connect a device first")
            return

        def do_workflow() -> None:
            self.model.run_item_information()

        def done() -> None:
            self._render(previous_serial=self.model.connected.serial if self.model.connected else None)
            self._set_busy(False)

        self._run_background(do_workflow, done, "Detecting item page...")

    def _render(self, previous_serial: str | None = None) -> None:
        self.adb_status_var.set("ADB Status: Ready" if self.model.adb_ready else "ADB Status: Error")
        labels = [item.label for item in self.model.devices]
        self.device_combo["values"] = labels

        selected: DeviceRecord | None = None
        if self.model.connected:
            selected = self.model.connected
        elif previous_serial:
            selected = next((item for item in self.model.devices if item.serial == previous_serial), None)
        else:
            usable = [item for item in self.model.devices if item.usable]
            if len(usable) == 1:
                selected = usable[0]

        self.device_var.set(selected.label if selected else "")
        self.status_var.set(f"Status: {self.model.status}")
        if self.model.connected:
            self.serial_var.set(f"Serial: {self.model.connected.serial}")
            self.state_var.set(f"State: {self.model.connected.state}")
        else:
            self.serial_var.set("Serial: -")
            self.state_var.set("State: -")

        if self.model.last_workflow_status:
            self.workflow_var.set(
                f"Workflow: {self.model.last_workflow_status} | Evidence: {self.model.last_workflow_evidence_dir}"
            )
        else:
            self.workflow_var.set("Workflow: -")


def main() -> None:
    root = tk.Tk()
    ControlAndroidApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
