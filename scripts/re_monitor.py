#!/usr/bin/env python3
"""re_monitor.py - vòng lặp nền liên tục cho workspace android-device.

Mỗi chu kỳ (mặc định 60s):
  - Kiểm tra thiết bị A03s qua a03s-ctl status (JSON).
  - Mất kết nối  -> tự chạy `a03s-ctl wireless` để kết nối lại (mDNS -> subnet -> Tailscale).
  - Pin < LOW_BATTERY và không sạc -> ghi cảnh báo (tự nghỉ spam tap, không có hành vi phá).
  - Nhiệt độ > HOT_TEMP -> ghi cảnh báo nhiệt.
  - Ghi JSONL log vào re-lab/monitor/monitor.log (ngoài repo, dung lượng tự cắt).

Chỉ dùng stdlib + adb có sẵn trong PATH. Chạy: python scripts/re_monitor.py
Dừng: tạo file  D:\\Project\\android-device\\scripts\\re_monitor.stop
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CTL = REPO / "a03s-ctl.cmd"          # Windows wrapper quanh a03s-ctl.py
LOG_DIR = Path(r"D:\Project\re-lab\monitor")
LOG_FILE = LOG_DIR / "monitor.log"
STOP_FILE = REPO / "scripts" / "re_monitor.stop"

INTERVAL_S = 60
LOW_BATTERY = 20          # % dưới ngưỡng này -> cảnh báo
HOT_TEMP = 43.0           # độ C trên ngưỡng này -> cảnh báo
MAX_LOG_MB = 20           # cắt log khi vượt


def log(event: str, **fields) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # xoay log đơn giản: quá to thì đổi tên thành .1 (ghi đè bản cũ)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_MB * 1024 * 1024:
        LOG_FILE.replace(LOG_FILE.with_suffix(".log.1"))
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(cmd: list[str] | str, timeout: int = 90) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        shell=isinstance(cmd, str),
    )


def device_status() -> dict | None:
    try:
        p = run([str(CTL), "status"], timeout=60)
        if p.returncode != 0:
            return None
        return json.loads(p.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


def try_reconnect() -> bool:
    """Gọi `a03s-ctl wireless` để tự tìm IP (mDNS/subnet/Tailscale) và kết nối."""
    try:
        p = run([str(CTL), "wireless"], timeout=120)
        ok = p.returncode == 0
        body = (p.stdout or "") + (p.stderr or "")
        log("reconnect", ok=ok, detail=body.strip()[:400])
        return ok
    except (subprocess.TimeoutExpired, OSError) as e:
        log("reconnect", ok=False, detail=repr(e)[:200])
        return False


def cycle() -> None:
    st = device_status()
    if not st or not st.get("online"):
        log("device_offline", hint="attempting reconnect")
        try_reconnect()
        return
    bat = st.get("battery", {})
    mem = st.get("memory", {})
    net = st.get("network", {})
    log(
        "status",
        battery=bat.get("level_percent"),
        charging=bat.get("charging_status"),
        temp_c=bat.get("temperature_celsius"),
        free_ram_mb=mem.get("available_mb"),
        wifi_ip=net.get("wifi_ip"),
    )
    if bat.get("level_percent", 100) < LOW_BATTERY and bat.get("charging_status") in (0, None):
        log("warn_low_battery", level=bat.get("level_percent"))
    if (bat.get("temperature_celsius") or 0) > HOT_TEMP:
        log("warn_hot", temp_c=bat.get("temperature_celsius"))


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log("monitor_start", pid=os.getpid(), interval_s=INTERVAL_S)
    cycles = 0
    while True:
        if STOP_FILE.exists():
            log("monitor_stop", cycles=cycles)
            STOP_FILE.unlink()
            return 0
        try:
            cycle()
        except Exception as e:  # vòng lặp không bao giờ được chết vì lỗi đơn lẻ
            log("cycle_error", detail=repr(e)[:300])
        cycles += 1
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    import os
    sys.exit(main())
