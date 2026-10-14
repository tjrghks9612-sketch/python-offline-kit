@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-offline.ps1"
set "AX_SETUP_EXIT=%ERRORLEVEL%"
if not "%AX_SETUP_EXIT%"=="0" (
  echo.
  echo Setup failed. Read the message and logs folder. See README.md for policy restrictions.
)
if /I not "%~1"=="--no-pause" pause
exit /b %AX_SETUP_EXIT%
