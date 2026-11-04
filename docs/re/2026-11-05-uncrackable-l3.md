# UnCrackable Level 3 — solved: XOR secret extracted, root/anti-frida bypassed, Success on emulator

Ngày: 2026-11-05 · Chạy trên **emulator AOSP rootable** (máy thật không Frida được
— xem L1/L2). APK 1.4MB, native `libfoo.so` 4 ABI, verify trong native `bar()`.

## 1. Java side (jadx) — manh mối quyết định nằm ngoài native

- `MainActivity`: `verifyLibs()` — CRC self-check **cả 4 ABI libfoo.so + classes.dex**
  (patch = `tampered = 31337`); `init(xorkey.getBytes())` — đưa key vào native.
- **`private static final String xorkey = "pizzapizzapizzapizzapizz"`** — key XOR
  nằm ngay trong Java!
- `RootDetection.checkRoot1/2/3` + `IntegrityCheck.isDebuggable` — Java-level.
- `CodeCheck.bar(byte[])` — native verify.

## 2. Trích secret tĩnh — XOR sweep

XOR toàn bộ lib với key `pizzapizz...`, tìm run ASCII:

```
arm64-v8a 0x34b0: 'making owasp great again_'   (25 byte hiển thị)
x86_64   0x3b40: 'making owasp gre' + garbage   (16 byte)
```

## 3. Disassembly x86_64 `bar()` giải đáp — độ dài là 0x18 = 24

`llvm-objdump --disassemble-symbols=Java_..._CodeCheck_bar`:

- `cmpl $0x18, %eax` — **secret dài 24 ký tự**, dấu `_` trong decode arm64 là
  **garbage đầu tiên sau blob**, không phải phần secret!
- `leaq 0x7040` — bảng so sánh nằm trong **.bss (runtime-built)**, không decode
  tĩnh được; input[i] so với `table[i] ^ key[i]`.
- Bài học: decode blob đúng ngay 16 byte đầu rồi "hỏng" → kiểm tra **length
  check trong disassembly** trước khi tin độ dài decode.

→ **Secret: `making owasp great again`** (24 ký tự).

## 4. Bypass 3 lớp bằng repkg pipeline (patch JSON tĩnh)

L3 gốc trên emulator **detect root ngay** (AOSP userdebug có `su` trong PATH +
`Build.TAGS = test-keys`). Patch (`re-lab/patches/uc3-static-bypass.json`):

1. **Native**: `goodbye()` (killer của watchdog anti-frida) tại offset 0x3740
   x86_64 → `ret` (`50bf06000000e835` → `c390909090909090`).
2. **Smali**: `const/16 v5, 0x7a69` (31337) → `0x0` — cả 2 nhánh `sput tampered`
   cùng dùng v5 → field `tampered` vĩnh viễn = 0 → CRC mismatch không đổi key.
3. **Smali RootDetection**: `"su"` → `"zz"`, `"test-keys"` → `"xxxx-keys"` —
   hai check duy nhất thật sự trigger trên AOSP emulator.

Một lệnh: `python -m scripts.repkg <apk> --patch uc3-static-bypass.json
--install --launch --serial emulator-5556` → app sống, không dialog root.

## 5. Verify

Nhập `making owasp great again` qua `adb input text` (space = `%s`) + VERIFY →

**"Success! This is the correct secret."** — `re-lab/out/l3_result2.png`.

## 6. Ghi chú hạ tầng (cho vòng sau)

- Emulator Play Store image (Medium_Phone_API_37) = user build, **`adb root`
  bị chặn**; tạo AVD AOSP `system-images;android-35;default;x86_64` → userdebug
  → root được. cmdline-tools cài tại `Sdk/cmdline-tools/latest` (zip dl.google.com).
- frida-server x86_64: URL release 404 giả — dùng
  `curl -H "Accept: application/octet-stream" api.github.com/.../releases/assets/<id>`.
- Frida spawn `-f` chết trước hook (watchdog native chạy trước script) — cần
  hook `android_dlopen_ext`; nhưng với repkg static patch thì **không cần Frida
  cho bypass**, Frida chỉ còn vai trò dump runtime data (.bss table).
- Emulator flaky khi spawn/kill liên tục (pthread_create fail) — force-stop +
  relaunch sạch trước mỗi thử.

## 7. Bảng chốt

| Bước | Kết quả |
|---|---|
| XOR sweep tìm blob | ✅ (key nằm trong Java!) |
| Length check disassembly | ✅ 24 = không underscore |
| repkg 3-lớp bypass | ✅ một lệnh |
| Success trên emulator | ✅ |
| L1 + L2 + L3 | ✅✅✅ series hoàn tất |
