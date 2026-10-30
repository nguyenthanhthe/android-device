@echo off
setlocal
set ADB="%~dp0..\tools\platform-tools\adb.exe"
set SCRCPY="%~dp0..\tools\scrcpy\scrcpy.exe"

echo ========================================================
echo   Android Wireless Screen Mirroring (Scrcpy 60fps)
echo ========================================================
echo [*] Connecting to device...
%ADB% connect 192.168.1.188:5555 >nul 2>&1

echo [*] Launching Scrcpy (Phone screen turns off to save battery)...
%SCRCPY% -s 192.168.1.188:5555 --stay-awake --turn-screen-off --power-off-on-close
if %ERRORLEVEL% NEQ 0 (
    echo [!] Wireless connection failed. Trying USB fallback...
    %SCRCPY% --stay-awake --turn-screen-off --power-off-on-close
)
