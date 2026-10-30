@echo off
set ADB="C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
echo [*] Connecting to Samsung Galaxy A03s via Tailscale Remote Mesh (100.100.241.85:5555)...
%ADB% connect 100.100.241.85:5555
echo.
echo [*] Current connected devices:
%ADB% devices -l
pause
