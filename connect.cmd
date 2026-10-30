@echo off
set ADB="C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
echo [*] Connecting to Samsung Galaxy A03s...
echo [*] Trying Local Wi-Fi (192.168.1.188:5555)...
%ADB% connect 192.168.1.188:5555
echo [*] Trying Tailscale Mesh (100.100.241.85:5555)...
%ADB% connect 100.100.241.85:5555
echo.
echo [*] Connected devices:
%ADB% devices -l
pause
