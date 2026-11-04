#!/usr/bin/env python3
"""repkg.py — RE patch-pipeline một lệnh cho workspace android-device.

Gom lại chuỗi đã dùng để giải UnCrackable L1/L2:
    apktool d  ->  apply patch (smali text / native bytes / manifest)  ->
    apktool b  ->  uber-apk-signer  ->  adb install

Dùng:
    python scripts/repkg.py <apk> --patch <patch.json> [--install] [--serial S] [--launch]

patch.json schema (mọi trường tuỳ chọn):
{
  "manifest": {"debuggable": true},
  "smali":  [{"file": "smali/<path>.smali", "one_of": ["old1", "old2"], "new": "chữ mới"}],
  "native": [{"lib": "lib/arm64-v8a/libfoo.so", "offset": 3476,
              "old_hex": "e1feff97", "new_hex": "1f2003d5"}]
}
- file/lib là đường dẫn tương đối trong thư mục apktool decode.
- offset là file offset thập phân; old_hex phải khớp đúng thì mới ghi.
- smali.old phải xuất hiện đúng 1 lần (nhiều hơn thì dừng, dùng one_of để chọn).

Chỉ dùng stdlib. Java phải có trong PATH (Temurin). ADB phải có trong PATH.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

APKTOOL = Path(r"D:\Project\re-lab\bin\apktool\apktool_3.0.3.jar")
SIGNER = Path(r"D:\Project\re-lab\bin\uber-apk-signer\uber-apk-signer-1.3.0.jar")
OUT_ROOT = Path(r"D:\Project\re-lab\out")


def java_jar(jar: Path, *args: str, timeout: int = 600) -> tuple[int, str]:
    p = subprocess.run(["java", "-jar", str(jar), *args], capture_output=True, timeout=timeout)
    return p.returncode, ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "replace").strip()


def adb(*args: str, timeout: int = 240) -> tuple[int, str]:
    p = subprocess.run(["adb", *args], capture_output=True, timeout=timeout)
    return p.returncode, ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "replace").strip()


def step(msg: str, rc: int, out: str, tail: int = 3) -> None:
    lines = out.strip().splitlines()[-tail:]
    print(f"[{'OK' if rc == 0 else 'FAIL'}] {msg}" + ("\n      " + "\n      ".join(lines) if lines else ""))
    if rc != 0:
        sys.exit(f"repkg: '{msg}' thất bại, dừng.")


def apply_patch(decode_dir: Path, patch: dict) -> None:
    manifest = patch.get("manifest", {})
    if manifest.get("debuggable"):
        mf = decode_dir / "AndroidManifest.xml"
        text = mf.read_text(encoding="utf-8")
        if "android:debuggable" not in text:
            text = text.replace("<application ", '<application android:debuggable="true" ', 1)
            mf.write_text(text, encoding="utf-8")
            print("      manifest: debuggable=true")

    for p in patch.get("smali", []):
        f = decode_dir / p["file"]
        text = f.read_text(encoding="utf-8")
        olds = p.get("one_of") or [p["old"]]
        hits = [o for o in olds if o in text]
        if len(hits) != 1:
            sys.exit(f"repkg: {p['file']} — old phải khớp đúng 1 phương án, thấy {len(hits)}")
        old = hits[0]
        if text.count(old) != 1:
            sys.exit(f"repkg: {p['file']} — chuỗi old xuất hiện {text.count(old)} lần, không xác định")
        f.write_text(text.replace(old, p["new"], 1), encoding="utf-8")
        print(f"      smali: {p['file']} patched ({len(old)} ký tự)")

    for p in patch.get("native", []):
        f = decode_dir / p["lib"]
        data = bytearray(f.read_bytes())
        off = int(p["offset"])
        old = bytes.fromhex(p["old_hex"])
        new = bytes.fromhex(p["new_hex"])
        if data[off : off + len(old)] != old:
            sys.exit(f"repkg: bytes tại {p['lib']}+{off:#x} không khớp old_hex")
        data[off : off + len(old)] = new
        f.write_bytes(bytes(data))
        print(f"      native: {p['lib']}+{off:#x} {p['old_hex']} -> {p['new_hex']}")


def read_pkg(decode_dir: Path) -> str:
    mf = (decode_dir / "AndroidManifest.xml").read_text(encoding="utf-8")
    for tok in mf.split():
        if tok.startswith("package="):
            return tok.split('"')[1]
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("apk", help="APK đầu vào")
    ap.add_argument("--patch", help="patch.json (schema xem docstring)", default=None)
    ap.add_argument("--install", action="store_true", help="cài lên thiết bị sau khi ký")
    ap.add_argument("--launch", action="store_true", help="mở app sau khi cài (monkey LAUNCHER)")
    ap.add_argument("--serial", help="adb -s <serial>", default=None)
    args = ap.parse_args()

    if not APKTOOL.exists() or not SIGNER.exists():
        sys.exit("repkg: thiếu apktool/uber-apk-signer trong re-lab/bin")

    apk = Path(args.apk).resolve()
    name = apk.stem
    decode_dir = OUT_ROOT / f"{name}-repkg"
    signed = OUT_ROOT / f"{name}-repkg-aligned-debugSigned.apk"

    rc, out = java_jar(APKTOOL, "d", "-f", "-o", str(decode_dir), str(apk))
    step("apktool decode", rc, out, tail=1)

    if args.patch:
        apply_patch(decode_dir, json.loads(Path(args.patch).read_text(encoding="utf-8")))

    unsigned = OUT_ROOT / f"{name}-repkg-unsigned.apk"
    rc, out = java_jar(APKTOOL, "b", str(decode_dir), "-o", str(unsigned))
    step("apktool build", rc, out, tail=1)

    rc, out = java_jar(SIGNER, "-a", str(unsigned), "-o", str(OUT_ROOT))
    step("sign (uber-apk-signer)", rc, out, tail=2)
    if not signed.exists():
        sys.exit("repkg: không thấy APK đã ký")
    unsigned.unlink(missing_ok=True)

    if not args.install:
        print(f"repkg: xong — {signed}")
        return 0

    pkg = read_pkg(decode_dir)
    if args.serial:
        adb("uninstall", pkg)
        rc, out = adb("-s", args.serial, "install", str(signed))
    else:
        adb("uninstall", pkg)
        rc, out = adb("install", str(signed))
    step("adb install", rc, out, tail=1)

    if args.launch:
        if args.serial:
            rc, out = adb("-s", args.serial, "shell", "monkey", "-p", pkg,
                          "-c", "android.intent.category.LAUNCHER", "1")
        else:
            rc, out = adb("shell", "monkey", "-p", pkg,
                          "-c", "android.intent.category.LAUNCHER", "1")
        step("launch", rc, out, tail=1)

    print("repkg: hoàn tất.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
