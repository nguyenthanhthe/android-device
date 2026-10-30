@echo off
setlocal
set ADB="%~dp0..\tools\platform-tools\adb.exe"

echo ========================================================
echo   Android Device Bridge - Wireless Connector
echo   Target: Samsung Galaxy A03s (192.168.1.188:5555)
echo ========================================================
echo.
echo [*] Checking connection to 192.168.1.188:5555...
%ADB% connect 192.168.1.188:5555
echo.
echo [*] Connected Devices List:
%ADB% devices -l
echo.
pause
