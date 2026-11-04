@echo off
setlocal
cd /d "%~dp0.."

echo [*] Opening ADB Shell on Samsung Galaxy A03s...
REM The address of the phone is looked up at run time, so it is not
REM written down here.  The shell opens on whatever link is found.
python "%~dp0..\a03s-ctl.py" wireless >nul
adb shell
