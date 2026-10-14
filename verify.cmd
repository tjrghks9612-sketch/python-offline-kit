@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify.ps1"
set "AX_VERIFY_EXIT=%ERRORLEVEL%"
if /I not "%~1"=="--no-pause" pause
exit /b %AX_VERIFY_EXIT%
