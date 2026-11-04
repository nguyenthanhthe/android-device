# RE Recon: DuckDuckGo Browser APK

Ngày: 2026-11-05 · Người phân tích: ZCode agent · Đề bài: thực hành theo
[user1342/Awesome-Android-Reverse-Engineering](https://github.com/user1342/Awesome-Android-Reverse-Engineering)

## Mục tiêu & môi trường

| | |
|---|---|
| Target | `duckduckgo.apk` (72 MB) ở repo root, copy sang `D:\Project\re-lab\samples\` |
| Package | `com.duckduckgo.mobile.android` |
| SDK | minSdk **28** (Android 9) · targetSdk **36** |
| Toolchain | apktool **3.0.3** + jadx **1.5.6** + Temurin JRE 21 · output tại `D:\Project\re-lab\out\` |
| Thiết bị | Samsung A03s (Android 13, **no root**) — chỉ tác động tĩnh tại thời điểm recon |

## Kết quả decompile

- **jadx**: 12.887 class, 504 lỗi decompile (R8 full-mode obfuscation) — ~99% source đọc được.
- **apktool**: decode đủ manifest + 687 MB smali/resources/assets; native libs cho 4 ABI
  (`arm64-v8a` là ABI thực chạy trên A03s/MT6765).

## Permissions (24)

Nổi bật so với một browser thông thường:

- `READ_PHONE_STATE`, `QUERY_ALL_PACKAGES`, `REQUEST_INSTALL_PACKAGES` — phục vụ
  **App Tracking Protection** (chặn tracker nội bộ app khác, cần cài local VPN).
- `RECORD_AUDIO`, `CAMERA`, `FOREGROUND_SERVICE_MICROPHONE` — Voice Search / Fire button.
- `USE_BIOMETRIC`/`USE_FINGERPRINT` — kho autofill.
- `BILLING` — subscription Privacy Pro.

## Bề mặt tấn công (attack surface)

- **112 activity, 10 exported** — trong đó `BrowserActivity`,
  `SystemSearchActivity`, `SelectedTextSearchActivity`,
  `IntentDispatcherActivity` + `LaunchBridgeActivity`: nhận intent từ app ngoài,
  là điểm kiểm thử deeplink/intent-redirection.
- **9/9 activity-alias exported** (icon theme `Launcher*`) — normal.
- **22 service, 5 exported**: `RealAutofillService` (Autofill framework — bề mặt
  lớn nhất, xử lý credential), `DuckDuckGoCustomTabService`, 2 VPN TileService.
- **0 exported provider**; receiver chỉ còn androidx work diagnostics.
- `allowBackup=false` → không lấy data qua `adb backup`.

## Anti-analysis / traffic

- **Không** tìm thấy chuỗi root/Frida/Xposed/Magisk detection → dễ phân tích động.
- `res/xml/network_security_config.xml`: base-config **pin trust anchor ISRG Root
  X1/X2** (Let's Encrypt) + system CA → MITM bằng user CA (Burp) **bị chặn** trên
  bản release; chỉ `debug-overrides` tin user CA. `cleartextTrafficPermitted=true`
  ở base (cho flow nội bộ/localhost).
- WASM: `credential_transfer_matcher.wasm` (so khớp credential khi transfer) —
  ứng viên thú vị cho phân tích WASM bằng Ghidra/wabt.

## Việc tiếp theo (backlog cho vòng lặp sau)

1. **Repackage + frida-gadget** (no-root): `objection patchapk` hoặc apktool +
   gadget `.so` (arm64-v8a) + uber-apk-signer → cài bản patched, hook runtime.
2. **Hook `RealAutofillService`** để xem flow decrypt credential.
3. **apk-mitm** variant: pin ISRG bypass bằng Frida `ssl-pinning-bypass` gadget script.
4. Phân tích `assets/brokers/` (danh sách data broker của Personal Information Removal).

## Công cụ đã dựng (Wave 2)

`D:\Project\re-lab\bin\`: jadx 1.5.6 · apktool 3.0.3 · uber-apk-signer 1.3.0 ·
frida-tools (venv `re-lab/.venv`) · Temurin JRE 21 (winget) · Ollama 0.40.14 (winget) ·
mobilerun CLI 0.7.4 (uv tool, Python 3.12).
