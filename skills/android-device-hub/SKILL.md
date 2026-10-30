---
name: android-device-hub
description: Direct control, wireless ADB, debloating, screen mirroring, and automation hub for the dedicated Samsung Galaxy A03s (SM-A037F) device.
---

# Android Device Hub

Use this skill when interacting with the dedicated secondary Samsung Galaxy A03s (`SM-A037F`) device connected over USB or Wireless ADB (`192.168.1.188:5555`).

## Workspace & Tools Location
All device tools and scripts are located at:
`D:\Project\android-device`

- **ADB / Fastboot:** `D:\Project\android-device\tools\platform-tools\adb.exe`
- **Scrcpy:** `D:\Project\android-device\tools\scrcpy\scrcpy.exe`
- **MTKClient:** `D:\Project\android-device\tools\mtkclient`
- **Scripts:** `D:\Project\android-device\scripts`

## Target Profile
- **Model:** Samsung Galaxy A03s (`SM-A037F` / `a03snnxx`)
- **Serial:** `R9PT609NVNT`
- **Default Wi-Fi Endpoint:** `192.168.1.188:5555`
- **OS:** Android 13 One UI Core 5.1 (Build `A037FXXS7CXK1`)

## Common Operations

### 1. Ensure Wireless ADB Connection
```powershell
& "D:\Project\android-device\tools\platform-tools\adb.exe" connect 192.168.1.188:5555
```

### 2. High-Performance Screen Mirroring
```powershell
& "D:\Project\android-device\tools\scrcpy\scrcpy.exe" -s 192.168.1.188:5555 --stay-awake --turn-screen-off
```

### 3. Headless App Launch & Key Events
```powershell
# Open browser URL
& "D:\Project\android-device\tools\platform-tools\adb.exe" -s 192.168.1.188:5555 shell am start -a android.intent.action.VIEW -d "https://example.com"

# Tap coordinates (X, Y)
& "D:\Project\android-device\tools\platform-tools\adb.exe" -s 192.168.1.188:5555 shell input tap 500 1000

# Type text
& "D:\Project\android-device\tools\platform-tools\adb.exe" -s 192.168.1.188:5555 shell input text "Hello"
```

### 4. Capture Screenshot
```powershell
& "D:\Project\android-device\tools\platform-tools\adb.exe" -s 192.168.1.188:5555 exec-out screencap -p > screenshot.png
```
