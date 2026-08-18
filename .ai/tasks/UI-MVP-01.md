# UI-MVP-01 — Desktop UI + ADB Device Connect

## PM role boundary
- ChatGPT PM owns architecture, scope, acceptance criteria, PASS/FIX/NEXT.
- Exactly one ChatGPT Worker implements this task.
- Claude CLI must review the plan before any code is generated.
- Codex Desktop is the local executor: inspect/update/run/test on the Windows machine.
- Claude CLI performs post-test audit.
- Worker must not redesign, expand scope, create another worker, or declare DONE.

## Project
`C:\Users\OS\Desktop\Tools MMO\eBay Tool\control_android`

## Objective
Build the first usable Windows desktop UI for `control_android` with a button to discover/select/connect an Android device through the existing ADB layer.

## Locked implementation direction
- Use Python Tkinter for this MVP.
- Reuse `src/control_android/adb.py` and `AdbTransport`; do not replace the ADB transport.
- UI/connection state must stay separate from ADB command execution.
- ADB discovery must not permanently freeze the UI.

## Mandatory gate 0 — Claude CLI pre-review
Before coding, Claude CLI must review this task read-only for:
- scope correctness,
- Tkinter suitability for this minimal MVP,
- reuse of existing `AdbTransport`,
- UI/ADB separation,
- device-state handling,
- tests and regression risk.

Required result: `PREPLAN_RESULT: PASS`.

If Claude returns FAIL: stop implementation and report blockers to PM. No code may be generated before PASS.

## UI requirements
Window title: `CONTROL ANDROID`

Minimum visible components:
1. Heading `CONTROL ANDROID`
2. ADB status: Ready / Error
3. Device selector showing discovered devices
4. `Refresh` button
5. `Connect Device` button
6. Status text: Not connected / Connecting / Connected / No Android device detected / Unauthorized / Offline / ADB error
7. Connected device details: serial + state

## Behavior
### Refresh
- Use existing ADB discovery.
- Refresh device list.
- Do not interact with the Android screen.

### Connect Device
- If exactly one usable `device` state exists, it may be selected automatically.
- If multiple usable devices exist, connect only the selected device; do not guess silently.
- `offline` and `unauthorized` must never become Connected.
- No usable device -> clear status, no crash.
- ADB exception -> clear ADB error status, no crash.

A small backwards-compatible improvement to discovery is allowed only if needed to preserve `serial` and `state` correctly. Do not redesign `AdbTransport`.

## Preferred files
- `src/control_android/desktop.py`
- `tests/test_desktop.py`
- `START_CONTROL_ANDROID.bat` only if useful for launching the UI
- `src/control_android/adb.py` only for a small backwards-compatible discovery fix if required

Do not modify unrelated files.

## Out of scope
- screenshot display
- UI XML viewer
- tap/swipe/text input
- app launch/stop UI
- workflow engine
- Perception
- OCR/OpenCV/WebView
- scrcpy integration
- device mirroring
- automation jobs
- settings UI

## Required tests
Cover at minimum:
- one device discovered
- no devices
- multiple devices
- offline device
- unauthorized device
- ADB exception
- refresh updates available-device state
- connect selects a valid device
- invalid/offline/unauthorized device cannot become Connected
- existing regression tests remain PASS

## Required local execution
Codex Desktop must run on the actual project folder:

```bat
py -3.11 -m compileall src
py -3.11 -m pytest -q
adb devices
```

Then launch:

```bat
py -3.11 -m control_android.desktop
```

## Real-machine smoke acceptance
- Desktop window opens.
- Refresh detects an online Android device if present.
- Connect Device marks the selected usable device Connected.
- Serial is visible in the UI.
- No Android screen action occurs.
- Report the observed serial/state. Current historical device evidence includes serial `a79508ce12b87aef`, but do not hard-code it.

## Mandatory post-test Claude audit
After Codex finishes code/tests/smoke, Claude CLI audits:
- changed files,
- implementation scope,
- test evidence,
- ADB smoke evidence,
- UI/ADB separation,
- no out-of-scope Android actions,
- regression risk.

Required result: `AUDIT_RESULT: PASS` or `FAIL`.

## Worker report format
```text
TASK_ID: UI-MVP-01
CLAUDE_PREPLAN: PASS | FAIL
CHANGED_FILES:
CODEX_RESULT:
COMPILEALL: PASS | FAIL
PYTEST: PASS | FAIL
TEST_COUNT:
ADB_SMOKE:
  serial:
  state:
UI_SMOKE: PASS | FAIL
  window:
  refresh:
  connect_button:
  connected_serial:
CLAUDE_AUDIT: PASS | FAIL
BLOCKERS:
WORKER_STATUS: CODE_COMPLETE | FAILED
```

Never report DONE. Wait for PM decision.
