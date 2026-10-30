@echo off
setlocal
set ADB="%~dp0..\tools\platform-tools\adb.exe"

echo [*] Opening ADB Shell on Samsung Galaxy A03s...
%ADB% -s 192.168.1.188:5555 shell
if %ERRORLEVEL% NEQ 0 (
    echo [!] Wireless shell failed. Trying USB fallback...
    %ADB% shell
)
