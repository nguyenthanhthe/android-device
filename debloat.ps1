# Safe Debloat Script for Samsung Galaxy A03s
$adb = "C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"

$bloatware = @(
    # Facebook Background Tracking & Updaters
    "com.facebook.services",
    "com.facebook.appmanager",
    "com.facebook.system",

    # Microsoft Pre-installed Apps
    "com.microsoft.bing",
    "com.microsoft.skydrive",
    "com.microsoft.office.word",
    "com.microsoft.office.excel",
    "com.microsoft.office.powerpoint",

    # Samsung Telemetry & Throttling
    "com.samsung.android.game.gos",          # Game Optimizing Service (causes CPU throttling)
    "com.samsung.android.app.settings.bixby",
    "com.samsung.android.bixby.service",
    "com.samsung.android.app.spage",         # Samsung Free news feed
    "com.samsung.android.kidsinstaller",
    "com.samsung.android.allshare.service.mediashare"
)

Write-Host "=== SAMSUNG GALAXY A03s SAFE DEBLOATER ===" -ForegroundColor Cyan
Write-Host "Target Device: SM-A037F (192.168.1.188:5555 / USB)" -ForegroundColor Yellow
Write-Host "Found $($bloatware.Count) candidate bloatware packages to remove.`n"

foreach ($pkg in $bloatware) {
    Write-Host "Uninstalling: $pkg ... " -NoNewline
    $res = & $adb shell "pm uninstall -k --user 0 $pkg" 2>&1
    if ($res -match "Success") {
        Write-Host "SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "SKIPPED/NOT INSTALLED ($res)" -ForegroundColor DarkGray
    }
}

Write-Host "`n[*] Debloat complete! Your device RAM and CPU are now significantly freed up." -ForegroundColor Green
Write-Host "[*] Note: You can restore any package at any time using: adb shell 'cmd package install-existing <pkg>'" -ForegroundColor Cyan
