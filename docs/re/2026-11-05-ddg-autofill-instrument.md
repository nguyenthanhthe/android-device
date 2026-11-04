# DuckDuckGo autofill instrumentation — SMALIHOOK verified live

Ngày: 2026-11-05 (vòng cron) · Target: `duckduckgo.apk` 72MB (R8, 4 dex)
· Chạy trên **emulator AOSP** — KHÔNG cài lên A03s (DDG thật có data trên máy,
uninstall sẽ mất data).

## Đã làm

1. Inject `Log.e("SMALIHOOK", ...)` vào 2 method của
   `com.duckduckgo.autofill.impl.service.RealAutofillService`:
   `onConnected()` (`.locals 3→4`) và `onSaveRequest()` (`.locals 1→2`).
   `onFillRequest()` bỏ qua — thêm code làm method tràn 65536 code units.
   Trick 1 register: `invoke-static {v6, v6} Log.e(tag=v6, msg=v6)` — trùng
   register hợp lệ trong dex, chỉ cần +1 string trong pool.

2. **Chặn đường apktool roundtrip**: build fail với
   `Unsigned short value out of range: 65536` tại
   `NetworkModule.apiRetrofit` instruction 0x1a — **không phải do hook**, là
   method-ref `Retrofit$Builder.baseUrl` vượt 65536 trong dex reassembled
   (dexlib2 sort lại pool khác R8 gốc). Reflection-call thử được nhưng chain
   fluent có NHIỀU ref tràn → vá từng lệnh là vô ích.

3. **Giải pháp gọn nhất: move cả `NetworkModule*` (17 file smali) từ
   `smali_classes2/` sang folder mới `smali_classes6/`** — pool method-ref của
   classes2 giảm, refs của NetworkModule re-resolve trong dex riêng nhỏ.
   Build thành công ngay.

4. Sign + cài lên emulator-5556 (AOSP). App chạy bình thường.

5. **Verify runtime**: `settings put secure autofill_service <component>` +
   **reboot emulator** (binding chỉ setup sạch sau boot) → mở app bất kỳ →
   system bind autofill service → **`E SMALIHOOK: SMALIHOOK`** trong logcat
   (onConnected fired, pid DDG 2058). `onFillRequest` sẽ fire khi có session
   fill thật (EditText có hint/heuristic — L3 crackme chưa trigger được).

## Bài học cho pipeline repkg (áp dụng cho app R8 lớn)

- apktool roundtrip dex lớn có thể fail vì **method/field-ref index ≥65536**
  do dexlib2 sort khác d8. Không sửa từng instruction.
- **Move class-group sang `smali_classesN` mới** = 1 thao tác, fix toàn bộ
  overflow trong pool đó. apktool hỗ trợ folder `smali_classesN` tùy ý.
- Trigger service-level hooks: cài qua `settings put` + **reboot** để binding
  sạch.

## Trạng thái

- `re-lab/out/ddg-instrumented-aligned-debugSigned.apk` — đã ký, đã cài
  emulator-5556, đang chạy.
- `re-lab/out/duckduckgo-apktool/` — decode dir đã chứa hooks + move-NetworkModule
  (đó là state buildable, không xóa).
- Backup decode "sạch" không cần — có thể decode lại từ APK gốc bất cứ lúc nào.
