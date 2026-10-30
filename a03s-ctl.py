#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
a03s-ctl: Antigravity Automation & Control Bridge for Samsung Galaxy A03s (SM-A037F)
High-efficiency, token-optimized device control over Wireless ADB & Tailscale.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Default connection settings
DEVICE_SERIAL = "R9PT609NVNT"
DEFAULT_WIFI_IP = "192.168.1.188:5555"
DEFAULT_TAILSCALE_IP = "100.100.241.85:5555"
SCREENSHOT_DEFAULT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "screenshots",
    "a03s_screen.png",
)

ADB_PATH = "adb"


def run_cmd(cmd, timeout=10, check=False):
    """Run command and return (stdout, stderr, exit_code)."""
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=isinstance(cmd, str),
            timeout=timeout,
        )
        if check and res.returncode != 0:
            return res.stdout.strip(), res.stderr.strip(), res.returncode
        return res.stdout.strip(), res.stderr.strip(), res.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except Exception as e:
        return "", str(e), -1


def get_connected_device():
    """Detect available connected device or target Galaxy A03s."""
    out, _, _ = run_cmd([ADB_PATH, "devices", "-l"], timeout=5)
    lines = [line.strip() for line in out.splitlines() if line.strip() and not line.startswith("List of devices")]
    
    devices = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
            
    if not devices:
        return None
        
    # Prefer exact match or wireless IP
    for dev in devices:
        if DEVICE_SERIAL in dev or DEFAULT_WIFI_IP in dev or DEFAULT_TAILSCALE_IP in dev:
            return dev
    return devices[0]


def is_port_open(host, port=5555, timeout=0.8):
    """Fast non-blocking TCP socket check before running adb connect."""
    import socket
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def ensure_device(auto_connect=True):
    """Ensure device is attached, or attempt quick reconnect."""
    dev = get_connected_device()
    if dev:
        return dev
        
    if not auto_connect:
        return None
        
    # Check Wi-Fi port first
    wifi_host, wifi_port = DEFAULT_WIFI_IP.split(":")
    if is_port_open(wifi_host, wifi_port):
        run_cmd([ADB_PATH, "connect", DEFAULT_WIFI_IP], timeout=5)
        dev = get_connected_device()
        if dev:
            return dev

    # Check Tailscale mesh port
    ts_host, ts_port = DEFAULT_TAILSCALE_IP.split(":")
    if is_port_open(ts_host, ts_port):
        run_cmd([ADB_PATH, "connect", DEFAULT_TAILSCALE_IP], timeout=5)
        return get_connected_device()
        
    return get_connected_device()


def adb_exec(args, timeout=10, binary=False):
    """Execute adb command targeted at the connected device."""
    dev = ensure_device()
    cmd = [ADB_PATH]
    if dev:
        cmd.extend(["-s", dev])
    cmd.extend(args)
    
    if binary:
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            return res.stdout, res.stderr, res.returncode
        except Exception as e:
            return b"", str(e).encode(), -1
            
    out, err, code = run_cmd(cmd, timeout=timeout)
    return out, err, code


def cmd_persist_setup():
    """Apply Samsung Galaxy A03s persistence & background unthrottling."""
    dev = ensure_device()
    if not dev:
        print("[-] Cannot apply persistence: No device connected. Connect Galaxy A03s via USB or Wireless ADB first.")
        return {}
    print(f"[*] Applying persistence settings on device: {dev}...")
    commands = [
        ("Tắt thời gian chờ tự hủy quyền ADB", ["shell", "settings", "put", "global", "adb_allowed_connection_time", "0"]),
        ("Giữ máy luôn thức khi cắm sạc", ["shell", "settings", "put", "global", "stay_on_while_plugged_in", "7"]),
        ("Khóa đồng bộ test cho device_config", ["shell", "/system/bin/device_config", "set_sync_disabled_for_tests", "persistent"]),
        ("Tắt giới hạn Phantom Process Killer (max_phantom_processes)", ["shell", "/system/bin/device_config", "put", "activity_manager", "max_phantom_processes", "2147483647"]),
        ("Tắt giám sát Phantom Processes", ["shell", "settings", "put", "global", "settings_enable_monitor_phantom_procs", "false"]),
    ]
    results = {}
    for desc, cmd in commands:
        out, err, code = adb_exec(cmd, timeout=5)
        status = "OK" if code == 0 else f"ERR ({err})"
        results[desc] = status
        print(f"  [+] {desc}: {status}")
    return results


def cmd_status():
    """Return lightweight JSON status of hardware, battery, RAM, IPs, focused app."""
    dev = ensure_device()
    if not dev:
        print(json.dumps({"error": "No Android device connected via ADB", "target": "Samsung Galaxy A03s"}, indent=2))
        return
        
    status = {
        "device": dev,
        "online": True,
        "battery": {},
        "memory": {},
        "network": {},
        "focused_window": "unknown",
    }
    
    # 1. Battery
    out, _, _ = adb_exec(["shell", "dumpsys", "battery"], timeout=4)
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("level:"):
            status["battery"]["level_percent"] = int(line.split(":")[1].strip())
        elif line.startswith("temperature:"):
            # Samsung temp in tenths of degree C (e.g. 300 = 30.0 C)
            raw_temp = float(line.split(":")[1].strip())
            status["battery"]["temperature_celsius"] = round(raw_temp / 10.0, 1)
        elif line.startswith("status:"):
            status["battery"]["charging_status"] = int(line.split(":")[1].strip())
            
    # 2. RAM
    out, _, _ = adb_exec(["shell", "cat", "/proc/meminfo"], timeout=4)
    mem_total = 0
    mem_avail = 0
    for line in out.splitlines():
        if "MemTotal:" in line:
            parts = line.split()
            mem_total = int(parts[1]) // 1024
        elif "MemAvailable:" in line:
            parts = line.split()
            mem_avail = int(parts[1]) // 1024
    if mem_total > 0:
        status["memory"]["total_mb"] = mem_total
        status["memory"]["available_mb"] = mem_avail
        status["memory"]["used_mb"] = mem_total - mem_avail
        status["memory"]["used_percent"] = round(((mem_total - mem_avail) / mem_total) * 100, 1)
        
    # 3. IP Addresses
    out, _, _ = adb_exec(["shell", "ip", "-f", "inet", "addr", "show"], timeout=4)
    wlan_ip = None
    tailscale_ip = None
    current_iface = ""
    for line in out.splitlines():
        line = line.strip()
        if re.match(r"^\d+:\s+(\S+):", line):
            current_iface = re.match(r"^\d+:\s+(\S+):", line).group(1)
        elif line.startswith("inet "):
            ip = line.split()[1].split("/")[0]
            if "wlan" in current_iface:
                wlan_ip = ip
            elif "tun" in current_iface or "tailscale" in current_iface:
                tailscale_ip = ip
    status["network"]["wifi_ip"] = wlan_ip or "disconnected"
    status["network"]["tailscale_ip"] = tailscale_ip or "disconnected"
    
    # 4. Current Focused App / Window
    out, _, _ = adb_exec(["shell", "dumpsys", "window"], timeout=4)
    for line in out.splitlines():
        if "mCurrentFocus" in line or "mFocusedApp" in line:
            status["focused_window"] = line.strip()
            break
            
    print(json.dumps(status, indent=2, ensure_ascii=False))


def cmd_ui_tree():
    """
    Dump UI hierarchy via uiautomator, extract clickable/scrollable/informative nodes,
    and output compact JSON with center coordinates for zero-token visual inspection.
    """
    dev = ensure_device()
    if not dev:
        print(json.dumps({"error": "No Android device connected via ADB"}, indent=2))
        return
        
    # Try stdout dump first
    xml_data, _, code = adb_exec(["exec-out", "uiautomator", "dump", "/dev/tty"], timeout=6)
    if code != 0 or not xml_data.startswith("<?xml") and "<hierarchy" not in xml_data:
        # Fallback to file dump
        adb_exec(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], timeout=6)
        xml_data, _, _ = adb_exec(["exec-out", "cat", "/sdcard/window_dump.xml"], timeout=4)
        
    if "<hierarchy" not in xml_data:
        print(json.dumps({"error": "Failed to retrieve UI hierarchy XML from device", "raw": xml_data[:200]}, indent=2))
        return
        
    # Clean possible prefix
    start_idx = xml_data.find("<hierarchy")
    if start_idx != -1:
        xml_data = xml_data[start_idx:]
        
    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        print(json.dumps({"error": f"XML parse error: {e}"}, indent=2))
        return
        
    elements = []
    bounds_pattern = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
    
    for node in root.iter("node"):
        attrib = node.attrib
        text = attrib.get("text", "").strip()
        desc = attrib.get("content-desc", "").strip()
        res_id = attrib.get("resource-id", "").strip()
        cls_name = attrib.get("class", "").strip()
        clickable = attrib.get("clickable", "false") == "true"
        checkable = attrib.get("checkable", "false") == "true"
        scrollable = attrib.get("scrollable", "false") == "true"
        focusable = attrib.get("focusable", "false") == "true"
        bounds_str = attrib.get("bounds", "")
        
        # Filter for actionable or informative nodes
        if not (clickable or checkable or scrollable or text or desc):
            continue
            
        m = bounds_pattern.match(bounds_str)
        if not m:
            continue
            
        x1, y1, x2, y2 = map(int, m.groups())
        # Filter out zero-size or invisible offscreen elements
        if x1 >= x2 or y1 >= y2:
            continue
            
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        item = {
            "center": [center_x, center_y],
            "bounds": [x1, y1, x2, y2],
            "clickable": clickable,
        }
        if text:
            item["text"] = text
        if desc:
            item["desc"] = desc
        if res_id:
            # Shorten resource-id by removing package prefix if redundant
            item["id"] = res_id.split(":id/")[-1] if ":id/" in res_id else res_id
        if "Button" in cls_name or "EditText" in cls_name or "CheckBox" in cls_name or "Switch" in cls_name:
            item["type"] = cls_name.split(".")[-1]
            
        elements.append(item)
        
    result = {
        "device": dev,
        "element_count": len(elements),
        "elements": elements,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_tap(x, y):
    """Tap at coordinates (x, y)."""
    out, err, code = adb_exec(["shell", "input", "tap", str(x), str(y)], timeout=5)
    if code == 0:
        print(f"[+] Tapped at ({x}, {y})")
    else:
        print(f"[-] Tap failed: {err}")


def cmd_swipe(x1, y1, x2, y2, duration=300):
    """Swipe from (x1, y1) to (x2, y2)."""
    out, err, code = adb_exec(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)], timeout=5)
    if code == 0:
        print(f"[+] Swiped from ({x1}, {y1}) to ({x2}, {y2}) [{duration}ms]")
    else:
        print(f"[-] Swipe failed: {err}")


def cmd_text(text_to_input):
    """Input text safely escaping special characters."""
    # Convert spaces to %s as required by adb input text
    escaped = text_to_input.replace(" ", "%s").replace("&", "\\&").replace("<", "\\<").replace(">", "\\>")
    out, err, code = adb_exec(["shell", "input", "text", escaped], timeout=5)
    if code == 0:
        print(f"[+] Entered text: {text_to_input}")
    else:
        print(f"[-] Text input failed: {err}")


def cmd_key(keycode):
    """Send keyevent (e.g. 4 for BACK, 3 for HOME, 26 for POWER)."""
    out, err, code = adb_exec(["shell", "input", "keyevent", str(keycode)], timeout=5)
    if code == 0:
        print(f"[+] Sent keyevent: {keycode}")
    else:
        print(f"[-] Keyevent failed: {err}")


def cmd_screen_mirror():
    """Launch scrcpy with optimal headless background flags."""
    dev = ensure_device()
    scrcpy_cmd = [
        "scrcpy",
        "--stay-awake",
        "--turn-screen-off",
        "--max-size", "1024",
        "--max-fps", "30",
    ]
    if dev:
        scrcpy_cmd.extend(["-s", dev])
        
    print(f"[*] Starting scrcpy mirror for {dev or 'default'} in background...")
    try:
        subprocess.Popen(
            scrcpy_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        print("[+] Scrcpy launched successfully (phone screen turned off to save battery).")
    except Exception as e:
        print(f"[-] Failed to launch scrcpy: {e}")


def cmd_screenshot(output_path=None):
    """Capture compressed lightweight screenshot."""
    if not output_path:
        output_path = SCREENSHOT_DEFAULT
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    print(f"[*] Capturing screenshot to {output_path}...")
    png_bytes, err, code = adb_exec(["exec-out", "screencap", "-p"], timeout=10, binary=True)
    if code == 0 and len(png_bytes) > 0:
        # Normalize CRLF on Windows if adb binary piped
        if png_bytes.startswith(b"\x89PNG"):
            with open(output_path, "wb") as f:
                f.write(png_bytes)
        else:
            clean_bytes = png_bytes.replace(b"\r\n", b"\n")
            with open(output_path, "wb") as f:
                f.write(clean_bytes)
        print(f"[+] Screenshot saved ({len(png_bytes) // 1024} KB): {output_path}")
    else:
        print(f"[-] Screenshot failed: {err.decode(errors='ignore')}")


def cmd_root_check():
    """Check if root / su is accessible."""
    dev = ensure_device()
    if not dev:
        print("[-] Cannot check root: No device connected.")
        return False
    out, err, code = adb_exec(["shell", "su", "-c", "id"], timeout=5)
    print("=== Root Access Audit ===")
    if code == 0 and "uid=0(root)" in out:
        print(f"[+] Device is ROOTED: {out}")
        return True
    else:
        print(f"[-] Device is NOT Rooted (Standard User shell): code={code}, out={out}, err={err}")
        return False


def cmd_pkg_check():
    """Audit installed automation tools: Termux, Termux:API, Shizuku."""
    dev = ensure_device()
    if not dev:
        print("[-] Cannot audit packages: No device connected.")
        return ["com.termux", "com.termux.api", "moe.shizuku.privileged.api"]
    packages = {
        "com.termux": "Termux (Linux terminal environment)",
        "com.termux.api": "Termux:API (Android hardware sensors bridge)",
        "moe.shizuku.privileged.api": "Shizuku (System-level ADB privilege manager)",
    }
    out, _, _ = adb_exec(["shell", "pm", "list", "packages"], timeout=6)
    installed_pkgs = set()
    for line in out.splitlines():
        if line.startswith("package:"):
            installed_pkgs.add(line.replace("package:", "").strip())
            
    print("=== Extended Tools Audit ===")
    missing = []
    for pkg_id, desc in packages.items():
        is_inst = pkg_id in installed_pkgs
        status = "INSTALLED" if is_inst else "MISSING"
        print(f"  [{'x' if is_inst else ' '}] {pkg_id} ({desc}): {status}")
        if not is_inst:
            missing.append(pkg_id)
            
    return missing


def cmd_install_tools():
    """Download official Termux, Termux:API, and Shizuku APKs and install via adb."""
    import urllib.request
    apks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "apks")
    os.makedirs(apks_dir, exist_ok=True)
    
    tools = [
        {
            "name": "Termux (v0.118.3 arm64-v8a)",
            "pkg": "com.termux",
            "url": "https://github.com/termux/termux-app/releases/download/v0.118.3/termux-app_v0.118.3%2Bgithub-debug_arm64-v8a.apk",
            "file": "termux-app_v0.118.3_arm64-v8a.apk"
        },
        {
            "name": "Termux:API (v0.53.0)",
            "pkg": "com.termux.api",
            "url": "https://github.com/termux/termux-api/releases/download/v0.53.0/termux-api-app_v0.53.0%2Bgithub.debug.apk",
            "file": "termux-api-app_v0.53.0.apk"
        },
        {
            "name": "Shizuku (v13.6.0)",
            "pkg": "moe.shizuku.privileged.api",
            "url": "https://github.com/RikkaApps/Shizuku/releases/download/v13.6.0/shizuku-v13.6.0.r1086.2650830c-release.apk",
            "file": "shizuku-v13.6.0-release.apk"
        }
    ]
    
    dev = ensure_device()
    for item in tools:
        local_path = os.path.join(apks_dir, item["file"])
        if not os.path.exists(local_path):
            print(f"[*] Downloading {item['name']} from official GitHub release...")
            req = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(local_path, "wb") as f:
                f.write(resp.read())
            print(f"[+] Cached: {item['file']} ({os.path.getsize(local_path) // 1024} KB)")
        else:
            print(f"[*] Cached APK found: {item['file']} ({os.path.getsize(local_path) // 1024} KB)")
            
        if dev:
            print(f"[*] Installing {item['pkg']} to {dev}...")
            out, err, code = adb_exec(["install", "-r", "-d", local_path], timeout=60)
            if code == 0:
                print(f"[+] Installed successfully: {item['pkg']}")
            else:
                print(f"[-] Install failed ({item['pkg']}): {err or out}")
        else:
            print(f"[!] Device not connected: Downloaded APK is ready at {local_path} (install automatically when connected).")


def main():
    parser = argparse.ArgumentParser(description="a03s-ctl: Samsung Galaxy A03s Agent Control CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    subparsers.add_parser("status", help="Get lightweight JSON hardware/battery/RAM/IP status")
    subparsers.add_parser("ui-tree", help="Dump and filter UI tree to JSON with center tap coordinates")
    subparsers.add_parser("persist-setup", help="Apply persistence & disable Phantom Process Killer")
    subparsers.add_parser("root-check", help="Check su / root access")
    subparsers.add_parser("pkg-check", help="Check Termux & Shizuku packages")
    subparsers.add_parser("install-tools", help="Download & install Termux, Termux:API, and Shizuku APKs")
    subparsers.add_parser("screen-mirror", help="Launch scrcpy background mirror with screen off")
    
    p_tap = subparsers.add_parser("tap", help="Tap on screen coordinate")
    p_tap.add_argument("x", type=int, help="X coordinate")
    p_tap.add_argument("y", type=int, help="Y coordinate")
    
    p_swipe = subparsers.add_parser("swipe", help="Swipe across screen")
    p_swipe.add_argument("x1", type=int)
    p_swipe.add_argument("y1", type=int)
    p_swipe.add_argument("x2", type=int)
    p_swipe.add_argument("y2", type=int)
    p_swipe.add_argument("--duration", type=int, default=300)
    
    p_text = subparsers.add_parser("text", help="Input text string")
    p_text.add_argument("string", type=str)
    
    p_key = subparsers.add_parser("key", help="Send keyevent")
    p_key.add_argument("keycode", type=int)
    
    p_shot = subparsers.add_parser("screenshot", help="Capture screen to file")
    p_shot.add_argument("--output", "-o", type=str, default=None)
    
    args = parser.parse_args()
    
    if args.command == "status":
        cmd_status()
    elif args.command == "ui-tree":
        cmd_ui_tree()
    elif args.command == "persist-setup":
        cmd_persist_setup()
    elif args.command == "root-check":
        cmd_root_check()
    elif args.command == "pkg-check":
        cmd_pkg_check()
    elif args.command == "install-tools":
        cmd_install_tools()
    elif args.command == "screen-mirror":
        cmd_screen_mirror()
    elif args.command == "tap":
        cmd_tap(args.x, args.y)
    elif args.command == "swipe":
        cmd_swipe(args.x, args.y, args.x2, args.y2, args.duration)
    elif args.command == "text":
        cmd_text(args.string)
    elif args.command == "key":
        cmd_key(args.keycode)
    elif args.command == "screenshot":
        cmd_screenshot(args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
