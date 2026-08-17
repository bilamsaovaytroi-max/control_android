# G01 — ADB Device Discovery

## Goal
Create the first functional Android device tool: connect to the local ADB server, discover attached Android devices, and report each device's identity/state deterministically.

## Dependency
G00 Project Foundation must pass its required tests before G01 source is promoted to the execution branch.

## Scope
- Resolve ADB executable from configured path or PATH.
- Start/check the ADB server using bounded subprocess execution.
- Execute `adb devices -l`.
- Parse zero, one, or multiple device rows.
- Return structured fields when available: `serial`, `state`, `product`, `model`, `device`, `transport_id`.
- Normalize device state to at least: `device`, `offline`, `unauthorized`, `unknown`.
- Provide a CLI command/module that prints a concise human-readable result and supports machine-readable JSON output.
- Produce clear errors for ADB missing, command timeout, malformed output, and ADB invocation failure.

## Out of Scope
- Screenshot capture.
- UIAutomator/XML dump.
- Tap/swipe/input.
- App launch/stop.
- WebView/DOM.
- OpenCV/OCR.
- Workflow engine.
- Desktop UI.

## Planned Files
- `src/control_android/adb/__init__.py`
- `src/control_android/adb/transport.py`
- `src/control_android/device/__init__.py`
- `src/control_android/device/discovery.py`
- `src/control_android/device_scan.py`
- `tests/test_adb_transport.py`
- `tests/test_device_discovery.py`
- README updates limited to the new scan command.

## Acceptance Criteria
1. `python -m compileall src` passes.
2. `pytest -q` passes.
3. Parser correctly handles representative outputs for authorized device, offline device, unauthorized device, multiple devices, and no devices.
4. ADB subprocesses have finite timeouts and return structured failure information.
5. `python -m control_android.device_scan --json` returns valid JSON.
6. When an authorized Android device is attached, output contains its real serial and state `device`.
7. When no device is attached, tool reports an empty device list without crashing.
8. No out-of-scope Android interaction code is introduced.

## Live Device Gate
G01 is not DONE until Codex Executor runs the scan against the connected Android device and captures evidence that at least one real device is detected, unless PM explicitly marks the live-device gate BLOCKED because no device is physically available.

## Next Goal Boundary
After real-device detection passes, stop and ask PM for the next goal. Do not automatically implement screenshot/UIAutomator/action features.
