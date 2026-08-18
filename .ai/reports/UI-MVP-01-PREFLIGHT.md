# UI-MVP-01 Preflight Report

Status: READY_FOR_LOCAL_EXECUTION

Approved implementation revision: `c13c70198f024ed2f88c3f089bfcb0431c562428`

## Changed implementation files
- `src/control_android/desktop.py`
- `tests/test_desktop.py`
- `START_CONTROL_ANDROID.bat`

## PM review
PASS.

Scope is limited to a Tkinter desktop UI, ADB device discovery/selection, Refresh, Connect Device, serial/state display, and safe handling of no-device/offline/unauthorized/ADB-error states. Existing `AdbTransport` is reused and no Android interaction commands are added.

## Isolated preflight
- `python -m compileall src`: PASS
- `pytest -q`: PASS
- Test count: 16 passed (7 reconstructed existing foundation tests + 9 UI-MVP tests)
- Python used for isolated compatibility check: 3.13.5, which satisfies project requirement `>=3.11`.

This preflight is not authoritative Windows/device evidence. The actual local project must still run under `py -3.11`, execute the full tests from the real checkout, run `adb devices`, and launch the Tkinter UI against the attached Android device.

## Required local executor commands
```bat
git pull origin ai/goal-current
py -3.11 -m compileall src
py -3.11 -m pytest -q
adb devices
START_CONTROL_ANDROID.bat
```

## Local smoke acceptance
- window `CONTROL ANDROID` opens;
- ADB Status becomes Ready;
- attached device appears in the selector;
- `Connect Device` marks an online device Connected;
- serial and state are visible;
- no tap/swipe/input command is sent to Android.

## Remaining gates
- Codex/local execution: PENDING
- authoritative Windows tests: PENDING
- real ADB/device smoke: PENDING
- independent audit on local evidence: PENDING
- PM final: PENDING
