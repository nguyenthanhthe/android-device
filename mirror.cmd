@echo off
setlocal
cd /d "%~dp0"

echo [*] Checking connection to Samsung Galaxy A03s...
REM The address of the phone changes with every DHCP lease, so it is
REM looked up at run time instead of being written down here.
python "%~dp0a03s-ctl.py" wireless >nul

echo [*] Launching scrcpy wireless display mirroring...
REM The serial is used for the pick, so the mirror works over USB and
REM over the network alike.
scrcpy -s R9PT609NVNT --stay-awake --turn-screen-off --power-off-on-close
