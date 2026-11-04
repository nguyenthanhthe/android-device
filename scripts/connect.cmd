@echo off
setlocal
cd /d "%~dp0.."

echo ========================================================
echo   Android Device Bridge - Wireless Connector
echo   Target: Samsung Galaxy A03s (SM-A037F)
echo   The address is looked up at run time, not hardcoded.
echo ========================================================
echo.

python "%~dp0..\a03s-ctl.py" wireless
if errorlevel 1 (
    echo [!] The wireless bridge could not be opened.
    pause
    exit /b 1
)

echo.
echo [*] Connected Devices List:
adb devices -l
echo.
pause
