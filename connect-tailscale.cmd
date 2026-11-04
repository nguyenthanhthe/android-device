@echo off
setlocal
cd /d "%~dp0"

echo [*] Connecting to Samsung Galaxy A03s via Tailscale Remote Mesh (100.100.241.85:5555)...
REM The mesh address is stable, so it needs no lookup.
adb connect 100.100.241.85:5555
echo.
echo [*] Current connected devices:
adb devices -l
pause
