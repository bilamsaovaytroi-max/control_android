# UI-MVP-01 — Desktop UI + ADB Device Connect

## PM role boundary
- ChatGPT PM owns architecture, scope, acceptance criteria, pre-code review, PASS/FIX/NEXT.
- Exactly one ChatGPT Code Worker implements this task.
- Codex Desktop is the local executor only: pull the approved GitHub revision, run/test on Windows, capture evidence/errors.
- Independent ChatGPT Audit Worker is read-only and reviews the exact Git revision plus Codex evidence.
- Claude CLI is optional and non-blocking unless verifiable same-revision invocation evidence exists.

## Project
`C:\Users\OS\Desktop\Tools MMO\eBay Tool\control_android`

## Objective
Build the first usable Windows desktop UI for `control_android` with ADB device discovery and a `Connect Device` button.

## Locked implementation direction
- Python Tkinter.
- Reuse existing `src/control_android/adb.py` / `AdbTransport`.
- Keep UI state separate from ADB transport.
- ADB discovery must not freeze the Tk main thread.

## UI requirements
- Window title and heading: `CONTROL ANDROID`.
- ADB Status: Ready / Error.
- Device selector showing serial and ADB state.
- `Refresh` button.
- `Connect Device` button.
- Status text for Not connected / Refreshing / Connecting / Connected / No Android device detected / Unauthorized / Offline / ADB error.
- Connected serial and state display.

## Behavior
- Refresh uses existing ADB discovery only.
- One usable `device` may auto-select/connect.
- Multiple usable devices require explicit selected serial.
- `offline` and `unauthorized` never become Connected.
- No device or ADB failure must not crash the UI.
- No Android screen action is permitted in this task.

## Allowed files
- `src/control_android/desktop.py`
- `tests/test_desktop.py`
- `START_CONTROL_ANDROID.bat`
- Existing ADB transport only if a small backwards-compatible discovery fix is necessary.

## Out of scope
Screenshot UI, XML viewer, tap/swipe/input, OCR, OpenCV, WebView, perception, scrcpy, mirroring, workflow engine, automation jobs, settings UI.

## Required local Codex execution
```bat
git pull
py -3.11 -m compileall src
py -3.11 -m pytest -q
adb devices
START_CONTROL_ANDROID.bat
```

## Real-machine smoke acceptance
- Window opens.
- ADB Status becomes Ready when adb works.
- Refresh lists the attached device.
- Connect Device marks an online device Connected.
- Serial/state are shown.
- No tap/swipe/input is sent to Android.

## Codex evidence required
- executed Git SHA,
- compileall exit code/output,
- pytest exit code/test count,
- `adb devices` output,
- UI launch result,
- observed serial/state,
- raw errors if any.

## Independent audit gate
Audit Worker receives the exact revision + Codex evidence and returns `AUDIT_RESULT: PASS` or `FAIL`. Audit Worker may not edit source.

Only PM may declare `READY_FOR_USER_TEST` or `DONE`.
