@echo off
setlocal
set ADB="%~dp0..\tools\platform-tools\adb.exe"
set OUTDIR=%~dp0..\screenshots

if not exist "%OUTDIR%" mkdir "%OUTDIR%"

for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TIMESTAMP=%%a
set FILENAME=%OUTDIR%\screen_%TIMESTAMP%.png

echo [*] Capturing screenshot from Samsung Galaxy A03s...
%ADB% -s 192.168.1.188:5555 exec-out screencap -p > "%FILENAME%"
if %ERRORLEVEL% EQU 0 (
    echo [+] Successfully saved to: %FILENAME%
) else (
    echo [!] Wireless failed, trying USB fallback...
    %ADB% exec-out screencap -p > "%FILENAME%"
    echo [+] Successfully saved to: %FILENAME%
)
