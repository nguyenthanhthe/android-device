@echo off
REM Connect to the Samsung Galaxy A03s over wireless ADB.
REM The address of the phone changes with every DHCP lease, so it is
REM looked up at run time (mDNS first, then a scan of the subnet)
REM instead of being written down here.
setlocal
cd /d "%~dp0"

echo [*] Connecting to Samsung Galaxy A03s over wireless ADB...
python "%~dp0a03s-ctl.py" wireless
if errorlevel 1 (
    echo [!] The wireless bridge could not be opened.
    pause
    exit /b 1
)

echo.
echo [*] Connected devices:
adb devices -l
pause
