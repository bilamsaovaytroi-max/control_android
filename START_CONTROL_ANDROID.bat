@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
py -3.11 -m control_android.desktop
if errorlevel 1 (
  echo.
  echo CONTROL_ANDROID failed to start.
  echo Check that Python 3.11+ and ADB are installed and on PATH.
  pause
)
endlocal
