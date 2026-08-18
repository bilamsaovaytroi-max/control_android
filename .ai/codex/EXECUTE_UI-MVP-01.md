# CODEX EXECUTION REQUEST — UI-MVP-01

Task: UI-MVP-01 — Desktop UI + ADB Device Connect
Branch: ai/goal-current

Codex role: executor/tester only. Do not redesign architecture and do not expand scope.

## Required local steps
1. In `C:\Users\OS\Desktop\Tools MMO\eBay Tool\control_android`, fetch and checkout `ai/goal-current`.
2. Pull latest branch state.
3. Verify these files exist:
   - `src/control_android/desktop.py`
   - `tests/test_desktop.py`
   - `START_CONTROL_ANDROID.bat`
4. Run:
   - `py -3.11 -m compileall src`
   - `py -3.11 -m pytest -q`
   - `adb devices`
5. Launch:
   - `py -3.11 -m control_android.desktop`
6. Perform read-only smoke only:
   - confirm window opens,
   - Refresh detects online device if present,
   - Connect Device marks usable device Connected,
   - serial/state shown,
   - do not tap/swipe/type on Android.
7. Report exact evidence to GitHub in `.ai/codex/reports/UI-MVP-01.md` with:
   - executed git SHA,
   - compileall result,
   - pytest result and count,
   - `adb devices` output,
   - UI smoke PASS/FAIL,
   - observed serial/state,
   - raw error if any,
   - final `CODEX_RESULT: PASS|FAIL`.

If any command fails, stop autonomous changes and report the raw failure. Do not redesign or generate replacement code.
