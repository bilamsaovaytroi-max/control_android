# control_android

Android automation foundation for the Automation Spec v2.1 architecture.

## Status

M0 foundation is implemented and test-gated. M1 device operations are implemented as a safe transport layer but require a connected Android device for hardware checks.

## Architecture

`ADB transport -> Device Manager -> Perception adapters (UIAutomator/WebView/Vision/OCR) -> Action Engine -> Workflow/Verification`

Perception sources are additive: native UI and DOM evidence are preferred, computer vision and OCR are fallbacks, and every action must verify the resulting state.

## Commands

```powershell
python -m pytest -q
python -m control_android.cli health
python -m control_android.cli devices
```

No task is marked `DONE` unless the test gate records a passing result.
