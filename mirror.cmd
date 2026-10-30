@echo off
set ADB="C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
echo [*] Checking connection to Samsung Galaxy A03s...
%ADB% connect 192.168.1.188:5555 >nul 2>&1
%ADB% connect 100.100.241.85:5555 >nul 2>&1

echo [*] Launching scrcpy wireless display mirroring...
scrcpy -s 100.100.241.85:5555 --stay-awake --turn-screen-off --power-off-on-close || scrcpy -s 192.168.1.188:5555 --stay-awake --turn-screen-off --power-off-on-close
